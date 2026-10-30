# Intelligent Electronics Project Assistant
> **Turn your component inventory into buildable, safety-checked electronics projects.**  
> A full-stack engineering project built with Python, Flask, SQLAlchemy, scikit-learn, OpenCV, TensorFlow, and Vanilla JS.

---

## 📐 Core Engineering Pipeline

```
AVAILABLE COMPONENTS (Inventory / Visual Scanner)
       ↓
PROJECT RECOMMENDATION ENGINE (Multi-factor Logistic Regression)
       ↓
DEPENDENCY ANALYSIS (Missing Parts & Low-Cost Alternatives)
       ↓
SAFETY & HAZARD CHECK (Voltage, Heat, Current Limits)
       ↓
COST OPTIMISATION (Prototype vs. Production Mode)
       ↓
AUTOMATIC WIRING SCHEMATIC GENERATOR (Breadboard & Schematic SVG)
       ↓
INTERACTIVE STEP-BY-STEP BUILDER (Progress Tracking & Verification)
       ↓
BUILD FAILURE DIAGNOSIS (Rule-Based & Multimeter Procedures)
       ↓
LOCAL RAG AI COPILOT & PERSONAL PROJECT MEMORY
```

---

## ⚡ macOS Setup Guide (Intel x86_64 macOS 12.7.6 & Apple Silicon)

### Prerequisites:
- macOS 12.7.6+ (Intel or Apple Silicon)
- Python 3.11.x

### Quick Installation Commands:

```bash
# 1. Verify Python Version
python3.11 --version

# 2. Create Virtual Environment
python3.11 -m venv .venv

# 3. Activate Virtual Environment
source .venv/bin/activate

# 4. Upgrade Pip & Install Dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# 5. Configure Environment Variables
cp .env.example .env

# 6. Initialize & Seed SQLite Database
python -m database.init_db

# 7. Start Application Server
python app.py
```

Open your browser to: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

**Default Demo Credentials:**
- **Username:** `demo`
- **Password:** `demo123`

---

## 💻 Windows Setup Guide (PowerShell / Command Prompt)

```powershell
# PowerShell / CMD
python --version
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python -m database.init_db
python app.py
```

---

## 🏗️ Architecture & Technology Stack

- **Backend:** Python 3.11+, Flask 2.3.3, Flask-SQLAlchemy 3.1.1, SQLAlchemy 2.0+, Werkzeug, python-dotenv, Flask-CORS
- **Database:** SQLite (default at `database/app.db`) with optional MySQL support
- **Machine Learning & RAG:** `scikit-learn` (Logistic Regression, TF-IDF Vectorizer, Cosine Similarity), `opencv-python`, `TensorFlow` (Keras image classifier), `Pillow`, `numpy`
- **Frontend:** Responsive HTML5, CSS3 Custom Properties (Dark Charcoal/Electric Blue theme), Vanilla JavaScript, Fetch API, SVG dynamic graph rendering (Zero Node.js/Vite build steps required)

---

## 📂 Project Directory Structure

```
intelligent-electronics-assistant/
├── app.py                      # Flask Application Factory & Server entry point
├── config.py                   # Environment configuration & defaults
├── requirements.txt            # Dependency manifest
├── .env.example                # Sample environment variables
├── database/
│   ├── models.py               # SQLAlchemy ORM Data Models (15 tables)
│   ├── seed.py                 # Initial workshop seeding script
│   └── init_db.py              # CLI database setup script
├── data/
│   ├── components.json         # Seed components catalogue
│   ├── projects.json           # Seed project knowledge base (15 projects)
│   ├── aliases.json            # Component alias mappings
│   ├── safety_rules.json       # Circuit safety rulebook
│   ├── wiring_rules.json       # Wiring connection rules
│   └── diagnosis_rules.json    # Diagnostic symptom & resolution rules
├── services/
│   ├── component_service.py    # Inventory CRUD & alias normalization
│   ├── project_service.py      # Project querying & feasibility
│   ├── dependency_service.py   # Missing parts & alternative discovery
│   ├── safety_service.py       # Voltage & thermal safety hazard analysis
│   ├── cost_service.py         # Prototype vs. Production cost breakdown
│   ├── recommendation_service.py # ML recommendation ranking engine
│   ├── wiring_service.py       # SVG Breadboard/Schematic layout renderer
│   ├── build_service.py        # Step-by-step progress tracker
│   ├── diagnosis_service.py    # Circuit failure diagnostic engine
│   ├── rag_service.py          # TF-IDF local RAG & optional LLM engine
│   └── memory_service.py       # Maker project memory telemetry
├── ml/
│   ├── preprocess.py           # OpenCV image normalization
│   ├── predict_component.py    # TensorFlow Keras scanner predictor
│   ├── recommendation.py       # Logistic Regression score predictor
│   ├── train_recommendation.py # Script to retrain recommendation model
│   ├── train_scanner.py        # Script to train TensorFlow scanner model
│   └── model/                  # Saved .keras and .json models
├── routes/
│   ├── auth.py                 # Authentication endpoints
│   ├── dashboard.py            # Page view routes & system status
│   ├── components.py           # REST API /api/components
│   ├── projects.py             # REST API /api/projects
│   ├── recommendations.py      # REST API /api/recommendations
│   ├── scanner.py              # REST API /api/scanner/predict
│   ├── wiring.py               # REST API /api/wiring
│   ├── build.py                # REST API /api/build-progress
│   ├── diagnosis.py            # REST API /api/diagnosis
│   ├── chatbot.py              # REST API /api/chat
│   └── history.py              # REST API /api/history
├── templates/                  # Jinja2 HTML templates
│   ├── base.html               # Shell layout & sidebar navigation
│   ├── dashboard.html          # Main workshop dashboard
│   ├── components.html         # Component inventory table & modals
│   ├── projects.html           # Project recommendations page
│   ├── project_detail.html     # Deep dive project specs page
│   ├── build_guide.html        # Step-by-step interactive builder
│   ├── scanner.html            # AI component scanner UI
│   ├── wiring.html             # SVG wiring diagram view
│   ├── diagnosis.html          # Circuit failure diagnosis engine UI
│   ├── chatbot.html            # Local RAG AI Copilot UI
│   ├── profile.html            # Maker memory & preferences page
│   └── my_projects.html        # Saved, attempted, completed builds
├── static/                     # CSS stylesheets & JS modules
└── tests/                      # Pytest automated test suite (19 tests)
```

---

## 📊 Final Feature Matrix

| Feature | Status | Technology / Details |
| :--- | :--- | :--- |
| **Component Inventory** | ✅ Fully Implemented | CRUD, Search, Filter, Stock Tracking, Alias Normalization |
| **Project Knowledge Base** | ✅ Fully Implemented | 15 detailed projects, step guide, wiring & safety data |
| **Recommendation Engine** | ✅ Fully Implemented | Logistic Regression, 7-factor scoring (0-100), Circular UI |
| **Dependency Analysis** | ✅ Fully Implemented | Missing parts detection, compatible low-cost alternatives |
| **Safety Rule Engine** | ✅ Fully Implemented | Hazard level calculation (Low, Medium, High, Critical) |
| **Cost Optimisation** | ✅ Fully Implemented | Prototype Mode vs. Ideal Production Mode pricing |
| **Wiring Diagram Generator**| ✅ Fully Implemented | Dynamic SVG Breadboard & Schematic generation, Download, Print |
| **Interactive Build Guide** | ✅ Fully Implemented | Step verification, live percentage progress bar, persistence |
| **Failure Diagnosis** | ✅ Fully Implemented | Symptom pattern matching, multimeter tests, step resolution |
| **Local RAG Copilot** | ✅ Fully Implemented | Vectorless TF-IDF + Cosine similarity, source cards |
| **Personal Project Memory** | ✅ Fully Implemented | Workshop telemetry, category distribution, skill progression |
| **Authentication & Session**| ✅ Fully Implemented | Werkzeug password hashing, session state, mode persistence |
| **REST APIs & Database** | ✅ Fully Implemented | 16 REST endpoints, SQLite default, 15 SQLAlchemy tables |
| **Automated Tests** | ✅ Fully Implemented | 19 Pytest unit/integration tests passing (100%) |
| **Component Scanner Model** | ⚙️ Optional Resource | Preprocessed OpenCV pipeline ready; requires trained `.keras` file |
| **External LLM Integration** | ⚙️ Optional Resource | Local RAG works 100% offline; uses OpenAI if `OPENAI_API_KEY` set |
| **MySQL Database** | ⚙️ Optional Resource | SQLite active by default; switchable via `DB_TYPE=mysql` in `.env` |

---

## 🛠️ Datasets & Retraining Scripts

### 1. Training the Recommendation Ranking Model
To retrain the Logistic Regression scorer on custom project feature sets:
```bash
python -m ml.train_recommendation
```

### 2. Training the TensorFlow Component Scanner
Structure custom component images inside `ml/dataset/`:
```
ml/dataset/
├── Arduino/
├── ESP32/
├── LED/
├── Resistor/
└── ...
```
Run the scanner training script:
```bash
python -m ml.train_scanner
```

---

## 🧪 Running Pytest Tests

Execute the complete test suite:
```bash
python -m pytest tests/
```

All 19 tests covering authentication, core models, recommendations, dependencies, safety, cost, wiring, scanner, diagnosis, RAG, memory, and view routes will execute.

---

## 💡 Viva Demonstration Sequence (Step-by-Step)

1. **Login:** Open `http://127.0.0.1:5000`, log in with `demo` / `demo123`.
2. **Dashboard:** View dynamic system status badges (Database, ML Model, RAG, Scanner) and inventory summary.
3. **Add Component:** Go to *My Components*, click *Add Component*, input a part (e.g. `DHT11 Temperature Sensor`), save and observe instant table update.
4. **Scan Component:** Go to *Component Scanner*, upload or drag a component image. Observe normalized label detection and click *Add to Inventory*.
5. **Recommendations:** Open *Recommendations*, toggle between *Prototype Mode* and *Production Mode*, and view ranked cards with circular feasibility progress circles.
6. **Project Detail & Dependencies:** Select a project (e.g. `Automatic Street Light`). View missing components, compatible low-cost alternatives, and safety warnings.
7. **Wiring Generator:** Click *Wiring Diagrams*. Toggle between *Breadboard View* and *Schematic View*, test zoom controls, download SVG, and test printing.
8. **Interactive Build:** Click *Start Step-by-Step Build*. Mark steps completed and observe live progress bar updating to 100%.
9. **Failure Diagnosis:** Open *Failure Diagnosis*, select a preset (e.g. `LED Not Turning ON` or `GSM module not responding`), submit form, and inspect multimeter test procedures and resolution steps.
10. **AI Copilot (Local RAG):** Open *AI Assistant*, ask *"What voltage does ESP32 need?"*, and inspect the response with retrieved knowledge context sources.
11. **My Projects & Memory:** Go to *My Projects* and *Profile* to see maker progression signals and telemetry updating based on completed projects.

---

## 📌 Known Limitations & Notes
- **Local RAG Fallback:** Designed to run 100% offline using TF-IDF cosine similarity. No external API key is required.
- **Scanner Model:** If no pre-trained `component_scanner.keras` file is present in `ml/model/`, the scanner route safely reports `"model_not_trained"` without throwing server exceptions.
