from flask import Blueprint, request, jsonify, session
from services.rag_service import LocalRAGService
from database.models import db, ChatHistory

chatbot_bp = Blueprint("chatbot", __name__, url_prefix="/api/chat")

def get_current_user_id() -> int:
    return session.get("user_id", 1)

@chatbot_bp.route("", methods=["POST"])
@chatbot_bp.route("/query", methods=["POST"])
def chat_query():
    user_id = get_current_user_id()
    data = request.get_json() or {}
    message = data.get("message") or data.get("query") or ""

    if not message.strip():
        return jsonify({"status": "error", "message": "Query message cannot be empty."}), 400

    response = LocalRAGService.answer_question(query=message, user_id=user_id)

    # Save to ChatHistory database table
    try:
        chat_user = ChatHistory(
            user_id=user_id,
            role="user",
            message=message
        )
        chat_bot = ChatHistory(
            user_id=user_id,
            role="assistant",
            message=response["answer"],
            sources=response.get("sources", [])
        )
        db.session.add(chat_user)
        db.session.add(chat_bot)
        db.session.commit()
    except Exception:
        db.session.rollback()

    return jsonify({"status": "success", "data": response})

@chatbot_bp.route("/history", methods=["GET"])
def get_chat_history():
    user_id = get_current_user_id()
    records = ChatHistory.query.filter_by(user_id=user_id).order_by(ChatHistory.created_at.asc()).limit(50).all()

    messages = []
    for r in records:
        messages.append({
            "id": r.id,
            "sender": r.role,
            "message": r.message,
            "sources": r.sources or [],
            "timestamp": r.created_at.strftime("%H:%M") if r.created_at else ""
        })

    return jsonify({"status": "success", "history": messages})
