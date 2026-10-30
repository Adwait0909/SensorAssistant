import os
import json
import logging
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config import Config
from database.models import Component, Project, SafetyRule, WiringRule, DiagnosisRule, ProjectHistory, ChatHistory

logger = logging.getLogger("ElectronicsAssistant")

class LocalRAGService:
    @staticmethod
    def _build_knowledge_corpus() -> List[Dict[str, Any]]:
        """
        Aggregate knowledge chunks from database tables:
        - component database
        - project database
        - safety rules
        - wiring rules
        - diagnosis rules
        - user project history
        """
        corpus = []

        # 1. Components
        comps = Component.query.all()
        for c in comps:
            text = f"Component Name: {c.name}. Category: {c.category}. Voltage: {c.voltage}. Description: {c.description}. Safety Notes: {c.safety_notes}"
            corpus.append({
                "source_type": "Component Database",
                "title": c.name,
                "text": text,
                "ref_id": c.id
            })

        # 2. Projects
        projs = Project.query.all()
        for p in projs:
            reqs = ", ".join(p.required_components or [])
            text = f"Project Title: {p.name}. Category: {p.category}. Difficulty: {p.difficulty}. Description: {p.description}. Required Components: {reqs}. Expected Output: {p.expected_output}"
            corpus.append({
                "source_type": "Project Database",
                "title": p.name,
                "text": text,
                "ref_id": p.id
            })

        # 3. Safety Rules
        s_rules = SafetyRule.query.all()
        for sr in s_rules:
            text = f"Safety Rule Target: {sr.target}. Risk Level: {sr.risk_level}. Rule Details: {sr.rule}"
            corpus.append({
                "source_type": "Safety Rules",
                "title": f"Safety for {sr.target}",
                "text": text,
                "ref_id": sr.id
            })

        # 4. Wiring Rules
        w_rules = WiringRule.query.all()
        for wr in w_rules:
            text = f"Wiring Standard Target: {wr.component}. Wiring Connection Rule: {wr.rule}"
            corpus.append({
                "source_type": "Wiring Rules",
                "title": f"Wiring Rule: {wr.component}",
                "text": text,
                "ref_id": wr.id
            })

        # 5. Diagnosis Rules
        d_rules = DiagnosisRule.query.all()
        for dr in d_rules:
            causes = "; ".join(dr.causes or [])
            text = f"Failure Symptom: {dr.symptom}. Common Causes: {causes}"
            corpus.append({
                "source_type": "Diagnosis Rules",
                "title": f"Diagnosis: {dr.symptom}",
                "text": text,
                "ref_id": dr.id
            })

        return corpus

    @classmethod
    def retrieve_context(cls, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """
        Local structured retrieval using TF-IDF and Cosine Similarity.
        Does NOT require any external network call or API key.
        """
        corpus = cls._build_knowledge_corpus()
        if not corpus:
            return []

        doc_texts = [item["text"] for item in corpus]
        
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf_matrix = vectorizer.fit_transform(doc_texts + [query])

        query_vec = tfidf_matrix[-1]
        doc_vecs = tfidf_matrix[:-1]

        similarities = cosine_similarity(query_vec, doc_vecs)[0]
        top_indices = similarities.argsort()[::-1][:top_k]

        retrieved = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score > 0.05:
                item = corpus[idx]
                item["similarity_score"] = round(score, 3)
                retrieved.append(item)

        return retrieved

    @classmethod
    def answer_question(cls, query: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate answer:
        - If OPENAI_API_KEY is present: use LLM to formulate answer from retrieved context.
        - If API key is absent: use deterministic local retrieval-based response generator.
        NEVER crashes without API key.
        NEVER invents component specifications.
        """
        retrieved_items = cls.retrieve_context(query, top_k=4)
        api_key = Config.OPENAI_API_KEY

        sources = []
        source_texts = []
        for item in retrieved_items:
            sources.append({
                "title": item["title"],
                "source_type": item["source_type"]
            })
            source_texts.append(f"[{item['source_type']}] {item['title']}: {item['text']}")

        llm_used = False

        if api_key:
            # External LLM Formulation path (optional)
            try:
                import openai
                client = openai.OpenAI(api_key=api_key)
                prompt = f"User Question: {query}\n\nRetrieved Knowledge Context:\n" + "\n".join(source_texts)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an electronics assistant. Answer the user strictly based on the provided context. Do not invent specifications."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2
                )
                answer_text = response.choices[0].message.content
                llm_used = True
            except Exception as e:
                logger.warning(f"External LLM call failed or unavailable ({e}). Falling back to Local RAG generator.")
                answer_text = cls._generate_deterministic_answer(query, retrieved_items)
        else:
            # Deterministic Local Retrieval-based Answer Generator
            answer_text = cls._generate_deterministic_answer(query, retrieved_items)

        return {
            "query": query,
            "answer": answer_text,
            "sources": sources,
            "llm_used": llm_used,
            "engine": "Optional OpenAI API" if llm_used else "Local RAG Engine (TF-IDF Cosine Similarity)"
        }

    @staticmethod
    def _generate_deterministic_answer(query: str, retrieved_items: List[Dict[str, Any]]) -> str:
        """Deterministic answer synthesis directly from retrieved database chunks."""
        if not retrieved_items:
            return "I could not find exact matching component specifications or wiring rules in your workshop database for that query. Please try searching for specific parts like Arduino, ESP32, LDR, or LED."

        lines = ["Based on your local workshop knowledge base:\n"]
        for idx, item in enumerate(retrieved_items, start=1):
            lines.append(f"**{idx}. {item['title']}** ({item['source_type']})")
            lines.append(f"{item['text']}\n")

        lines.append("---")
        lines.append("*Answer generated deterministically via Local RAG (TF-IDF Cosine Similarity).*")
        return "\n".join(lines)
