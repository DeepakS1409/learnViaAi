# Padika AI — College-Wide AI Learning Platform

> **"Your Learning. Reimagined with AI."**  
> A college-wide academic AI learning platform featuring a **Pure Glassmorphism UI**, role-based portals (Student, Faculty, Admin), and a grounded RAG chatbot powered by **PyMuPDF**, **Sentence Transformers**, and the **Gemini API**.

---

## ✦ Key Innovations & Features

### 1. Strict Pure Glassmorphism UI Design
- **100% Glassmorphism Experience**: Layered transparent cards with `backdrop-filter: blur()`, saturated translucency, deep midnight purple & violet ambient gradient glows.
- **Glowing Borders & Accents**: Neon purple, indigo, cyan, and emerald glowing states.
- **Custom Floating Glass Elements**: Glass navbars, floating glass chat input bar, frosted modals, translucent data tables, interactive filter pills, and glass badges.
- **Zero Ordinary White or Bootstrap Layouts**: Consistent dark ambient aesthetic across all 18 pages.

### 2. Grounded Academic RAG (Retrieval-Augmented Generation)
- **Zero Hallucination Guarantee**: Student queries are searched strictly against the professor's uploaded syllabus notes, question banks, and reference books.
- **Clickable Page Citations**: Every AI response cites the exact document title and page number (e.g., `[Doc: Unit 1 Lecture Notes.pdf, Page 14]`).
- **Out-of-Scope Protection**: If a question is not covered in the faculty materials, Padika AI explicitly alerts the student rather than inventing facts.

### 3. Multilingual Support
- **English**: Academic, rigorous, easy-to-understand explanations.
- **தமிழ் (Tamil)**: Full Tamil script responses with standard technical terms.
- **Tanglish (Tamil in English Script)**: Conversational and intuitive (e.g. *"OSI model layers pathi simple-ah sollanum na..."*).
- **Auto-Language Detection**: Automatically detects user input language or honors manual selection.

### 4. Exam-Oriented Answer Generation
- **Normal**: Clear conceptual overview with practical examples and diagrams.
- **2-Mark Format**: Crisp 1-2 sentence definition + exactly 2-3 key bullet points / formula, aligned with Anna University and university exam criteria.
- **13-Mark Format**: Comprehensive answer structured with Introduction, Architecture, Step-by-Step Mechanism, Diagram description, Advantages, and Conclusion.
- **16-Mark Format**: In-depth university paper guide with Theoretical Framework, Mathematical/Algorithmic formulation, Real-world case study, and Comparative Analysis.

### 5. In-Browser Glassmorphism PDF Reader
- Embedded reader displaying uploaded documents with page tracking.
- Interactive **"Ask AI in Document"** slide-out drawer for instant scoped questioning while reading.
- Fullscreen mode and direct downloads.

### 6. Role-Based Access Control (RBAC)
- **Student Portal**:
  - Enrolled subjects and faculty materials matching department and semester.
  - Personal bookmarks, interactive AI chat, full conversation history.
- **Faculty Portal**:
  - Drag-and-drop PDF upload with instant PyMuPDF text extraction, chunking, and embedding.
  - Management hub to edit, delete, or inspect document processing status and usage statistics.
- **Admin Portal**:
  - College-wide overview, user account management (activate/suspend), and curriculum management (add/delete departments and courses).

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript | Pure Glassmorphism design system without heavy frameworks |
| **Backend** | Python Flask | Lightweight, fast REST routes and Jinja2 rendering |
| **Database** | SQLite (SQLAlchemy ready) | Structured relational schema with foreign key constraints |
| **PDF Processing**| PyMuPDF (`pymupdf`/`fitz`) | High-speed text extraction with strict page-number preservation |
| **Embeddings** | Sentence Transformers | Multilingual 384-dimensional dense semantic vectors |
| **Vector Search**| Cosine Similarity Engine | High-performance sub-second scoped chunk retrieval |
| **AI LLM** | Google Gemini API | Grounded synthesis with smart local grounded generator fallback |

---

## 🚀 Getting Started on Windows (VS Code)

### Prerequisites
- Windows 10/11 laptop
- Python 3.10+ (or Python Launcher `py`)
- Visual Studio Code

### 1. Clone or Open Project
Open the project directory in VS Code:
```powershell
cd "c:\Users\User\OneDrive\Documents\Studying AI"
```

### 2. Install Required Dependencies
```powershell
py -m pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create or verify your `.env` file (copied from `.env.example`):
```env
SECRET_KEY=padika-super-secret-glass-key-2026-production
FLASK_DEBUG=1
PORT=5000
HOST=127.0.0.1
DATABASE_PATH=padika.db
UPLOAD_FOLDER=uploads/pdfs
GEMINI_API_KEY=your_gemini_api_key_here
```
> **Note on Gemini API Key**: If you leave `GEMINI_API_KEY` blank, Padika AI will seamlessly use its built-in intelligent grounded RAG engine, so all features, formats, and citations work immediately without any API key required!

### 4. Initialize Database and Seed Academic Demo Data
Run the database initialization script:
```powershell
py init_db.py
```
This automatically:
- Creates all database tables.
- Seeds admin, faculty, and student accounts.
- Generates 3 authentic multi-page academic PDFs in `uploads/pdfs/`.
- Extracts pages with PyMuPDF, generates embeddings, and indexes them into the vector store.
- Sets up sample bookmarks and chat sessions.

### 5. Launch Padika AI
```powershell
py run.py
```
Open your browser and navigate to:
👉 **`http://127.0.0.1:5000`**

---

## 🔑 Pre-Configured Demo Credentials

The login page features convenient **1-Click autofill buttons**:

| Role | Email | Password | Access / Scope |
| :--- | :--- | :--- | :--- |
| **Student** | `student@padika.ai` | `Student@123` | CSE Dept, Semester 6, Enrolled Subjects & Notes |
| **Faculty** | `faculty@padika.ai` | `Faculty@123` | Dr. K. Ramanathan, CSE Dept, Upload & Manage |
| **Admin** | `admin@padika.ai` | `Admin@123` | Full Campus Control, Users & Curriculum |

---

## 📁 Project Structure

```
Studying AI/
├── app/
│   ├── __init__.py              # Flask app factory, custom filters, context globals
│   ├── config.py                # Environment configuration & constants
│   ├── database.py              # SQLite connection manager & query helpers
│   ├── schema.sql               # Relational SQL schema
│   ├── models.py                # User, Subject, Material, Chunk, Chat models
│   ├── auth.py                  # Session authentication helpers
│   ├── access_control.py        # Backend authorization decorators
│   ├── services/
│   │   ├── pdf_service.py       # PyMuPDF page extraction & chunking
│   │   ├── embedding_service.py # Sentence Transformers & semantic vectors
│   │   ├── vector_store.py      # Cosine similarity vector search
│   │   └── rag_service.py       # Gemini API RAG pipeline & citations
│   ├── routes/
│   │   ├── main.py              # Landing page & About routes
│   │   ├── auth_routes.py       # Login & registration routes
│   │   ├── student.py           # Student portal dashboard & bookmarks
│   │   ├── faculty.py           # Faculty upload & material management
│   │   ├── admin.py             # User & curriculum management
│   │   ├── materials_routes.py  # Library, subject materials & PDF viewer
│   │   ├── chat_routes.py       # AI chat interface & RAG endpoints
│   │   └── profile_routes.py    # Profile & settings routes
│   ├── static/
│   │   ├── css/
│   │   │   ├── glassmorphism.css# Pure Glassmorphism design tokens & components
│   │   │   ├── chat.css         # Chatbot glass interface styles
│   │   │   └── pdf_viewer.css   # PDF reader & AI side-drawer styles
│   │   └── js/
│   │       ├── main.js          # Flash alerts, bookmarks, modals
│   │       ├── chat.js          # Chatbot AJAX, markdown renderer, citations
│   │       └── pdf_viewer.js    # PDF toolbar & document-scoped AI drawer
│   └── templates/
│       ├── base.html            # Master glass layout & navigation
│       ├── landing.html         # Landing page with hero & previews
│       ├── about.html           # About Padika AI architecture
│       ├── auth/
│       │   ├── login.html
│       │   ├── register_student.html
│       │   └── register_faculty.html
│       ├── student/
│       │   ├── dashboard.html
│       │   ├── materials.html
│       │   └── bookmarks.html
│       ├── faculty/
│       │   ├── dashboard.html
│       │   ├── upload.html
│       │   └── manage_materials.html
│       ├── admin/
│       │   ├── dashboard.html
│       │   ├── users.html
│       │   └── curriculum.html
│       ├── materials/
│       │   ├── library.html
│       │   ├── subject_materials.html
│       │   └── pdf_viewer.html
│       ├── chat/
│       │   ├── chat.html
│       │   └── history.html
│       └── profile/
│           └── profile.html
├── uploads/
│   └── pdfs/                    # Uploaded faculty academic PDF documents
├── padika.db                    # SQLite database
├── init_db.py                   # Database seeder & PDF generator
├── run.py                       # Development server runner
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
└── README.md                    # Platform documentation
```

---

## 🛡️ License & Academic Integrity
Built for university and college engineering departments to elevate self-directed learning and ensure AI answers strictly adhere to accredited curricula.

