-- Padika AI Relational Database Schema (SQLite & PostgreSQL Compatible)

CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    code TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS academic_years (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    is_current INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS semesters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    number INTEGER NOT NULL,
    academic_year_id INTEGER REFERENCES academic_years(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    semester_id INTEGER NOT NULL REFERENCES semesters(id) ON DELETE CASCADE,
    credits INTEGER DEFAULT 3,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(code, department_id)
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('student', 'faculty', 'admin')),
    department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
    semester_id INTEGER REFERENCES semesters(id) ON DELETE SET NULL,
    roll_number TEXT,
    employee_id TEXT,
    is_active INTEGER DEFAULT 1,
    avatar_color TEXT DEFAULT '#8a2be2',
    bio TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS faculty_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    faculty_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    department_id INTEGER REFERENCES departments(id) ON DELETE CASCADE,
    semester_id INTEGER REFERENCES semesters(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(faculty_id, subject_id)
);

CREATE TABLE IF NOT EXISTS student_enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    semester_id INTEGER NOT NULL REFERENCES semesters(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, department_id, semester_id)
);

CREATE TABLE IF NOT EXISTS materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL CHECK(category IN ('Notes', 'Book', 'PPT', 'Question Bank', 'Syllabus', 'Reference')),
    filename TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    file_size INTEGER DEFAULT 0,
    mime_type TEXT DEFAULT 'application/pdf',
    file_path TEXT NOT NULL,
    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    semester_id INTEGER NOT NULL REFERENCES semesters(id) ON DELETE CASCADE,
    faculty_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'Processing' CHECK(status IN ('Processing', 'Completed', 'Failed')),
    page_count INTEGER DEFAULT 0,
    chunk_count INTEGER DEFAULT 0,
    view_count INTEGER DEFAULT 0,
    download_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    material_id INTEGER NOT NULL REFERENCES materials(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL DEFAULT 'Academic Discussion',
    subject_id INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
    material_id INTEGER REFERENCES materials(id) ON DELETE SET NULL,
    language_preference TEXT DEFAULT 'en' CHECK(language_preference IN ('en', 'ta', 'tanglish')),
    format_preference TEXT DEFAULT 'normal' CHECK(format_preference IN ('normal', '2-mark', '13-mark', '16-mark')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    sender TEXT NOT NULL CHECK(sender IN ('user', 'ai')),
    message TEXT NOT NULL,
    sources_json TEXT, -- JSON array of [{material_id, document_title, page_number, snippet}]
    language TEXT DEFAULT 'en',
    format TEXT DEFAULT 'normal',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bookmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    material_id INTEGER NOT NULL REFERENCES materials(id) ON DELETE CASCADE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, material_id)
);

CREATE TABLE IF NOT EXISTS system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    details TEXT,
    ip_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indices for rapid queries
CREATE INDEX IF NOT EXISTS idx_materials_dept_sem ON materials(department_id, semester_id);
CREATE INDEX IF NOT EXISTS idx_materials_subject ON materials(subject_id);
CREATE INDEX IF NOT EXISTS idx_materials_faculty ON materials(faculty_id);
CREATE INDEX IF NOT EXISTS idx_chunks_material ON document_chunks(material_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_bookmarks_user ON bookmarks(user_id);

