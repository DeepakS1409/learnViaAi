import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app.database import query_one, query_all, execute_insert, execute_write

class UserModel:
    @staticmethod
    def get_by_id(user_id):
        return query_one("SELECT * FROM users WHERE id = ?", (user_id,))

    @staticmethod
    def get_by_email(email):
        return query_one("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email.strip(),))

    @staticmethod
    def create(full_name, email, password, role, department_id=None, semester_id=None, roll_number=None, employee_id=None):
        password_hash = generate_password_hash(password)
        colors = ['#8a2be2', '#6366f1', '#3b82f6', '#ec4899', '#06b6d4', '#10b981']
        avatar_color = colors[abs(hash(email)) % len(colors)]
        return execute_insert(
            """INSERT INTO users (full_name, email, password_hash, role, department_id, semester_id, roll_number, employee_id, avatar_color)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (full_name.strip(), email.strip().lower(), password_hash, role, department_id, semester_id, roll_number, employee_id, avatar_color)
        )

    @staticmethod
    def verify_password(stored_hash, password):
        return check_password_hash(stored_hash, password)

    @staticmethod
    def get_all(role_filter=None, search=None):
        query = """
            SELECT u.*, d.name as department_name, d.code as department_code, s.name as semester_name
            FROM users u
            LEFT JOIN departments d ON u.department_id = d.id
            LEFT JOIN semesters s ON u.semester_id = s.id
            WHERE 1=1
        """
        params = []
        if role_filter:
            query += " AND u.role = ?"
            params.append(role_filter)
        if search:
            query += " AND (u.full_name LIKE ? OR u.email LIKE ? OR u.roll_number LIKE ? OR u.employee_id LIKE ?)"
            term = f"%{search}%"
            params.extend([term, term, term, term])
        query += " ORDER BY u.created_at DESC"
        return query_all(query, params)

    @staticmethod
    def toggle_status(user_id):
        user = UserModel.get_by_id(user_id)
        if not user:
            return False
        new_status = 0 if user['is_active'] else 1
        execute_write("UPDATE users SET is_active = ? WHERE id = ?", (new_status, user_id))
        return new_status

    @staticmethod
    def update_profile(user_id, full_name, bio=None, department_id=None, semester_id=None):
        return execute_write(
            """UPDATE users SET full_name = ?, bio = ?, department_id = COALESCE(?, department_id), semester_id = COALESCE(?, semester_id)
               WHERE id = ?""",
            (full_name, bio, department_id, semester_id, user_id)
        )

class DepartmentModel:
    @staticmethod
    def get_all():
        return query_all("SELECT * FROM departments ORDER BY code ASC")

    @staticmethod
    def get_by_id(dept_id):
        return query_one("SELECT * FROM departments WHERE id = ?", (dept_id,))

    @staticmethod
    def create(name, code, description=""):
        return execute_insert(
            "INSERT INTO departments (name, code, description) VALUES (?, ?, ?)",
            (name.strip(), code.strip().upper(), description)
        )

    @staticmethod
    def delete(dept_id):
        return execute_write("DELETE FROM departments WHERE id = ?", (dept_id,))

class SemesterModel:
    @staticmethod
    def get_all():
        return query_all("SELECT s.*, y.name as academic_year_name FROM semesters s JOIN academic_years y ON s.academic_year_id = y.id ORDER BY s.number ASC")

    @staticmethod
    def get_by_id(sem_id):
        return query_one("SELECT * FROM semesters WHERE id = ?", (sem_id,))

class SubjectModel:
    @staticmethod
    def get_all():
        return query_all("""
            SELECT s.*, d.name as department_name, d.code as department_code, sem.name as semester_name, sem.number as semester_number
            FROM subjects s
            JOIN departments d ON s.department_id = d.id
            JOIN semesters sem ON s.semester_id = sem.id
            ORDER BY d.code, sem.number, s.code
        """)

    @staticmethod
    def get_by_id(subject_id):
        return query_one("""
            SELECT s.*, d.name as department_name, d.code as department_code, sem.name as semester_name, sem.number as semester_number
            FROM subjects s
            JOIN departments d ON s.department_id = d.id
            JOIN semesters sem ON s.semester_id = sem.id
            WHERE s.id = ?
        """, (subject_id,))

    @staticmethod
    def get_by_department_and_semester(department_id, semester_id=None):
        if semester_id:
            return query_all("SELECT * FROM subjects WHERE department_id = ? AND semester_id = ? ORDER BY code ASC", (department_id, semester_id))
        return query_all("SELECT * FROM subjects WHERE department_id = ? ORDER BY semester_id, code ASC", (department_id,))

    @staticmethod
    def create(code, name, department_id, semester_id, credits=3, description=""):
        return execute_insert(
            """INSERT INTO subjects (code, name, department_id, semester_id, credits, description)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (code.strip().upper(), name.strip(), department_id, semester_id, credits, description)
        )

    @staticmethod
    def delete(subject_id):
        return execute_write("DELETE FROM subjects WHERE id = ?", (subject_id,))

class MaterialModel:
    @staticmethod
    def create(title, description, category, filename, original_filename, file_size, mime_type, file_path, subject_id, department_id, semester_id, faculty_id):
        return execute_insert(
            """INSERT INTO materials (title, description, category, filename, original_filename, file_size, mime_type, file_path, subject_id, department_id, semester_id, faculty_id, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Processing')""",
            (title.strip(), description, category, filename, original_filename, file_size, mime_type, file_path, subject_id, department_id, semester_id, faculty_id)
        )

    @staticmethod
    def update_status(material_id, status, page_count=0, chunk_count=0):
        return execute_write(
            "UPDATE materials SET status = ?, page_count = ?, chunk_count = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, page_count, chunk_count, material_id)
        )

    @staticmethod
    def update_details(material_id, title, description, category):
        return execute_write(
            "UPDATE materials SET title = ?, description = ?, category = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (title.strip(), description, category, material_id)
        )

    @staticmethod
    def delete(material_id):
        return execute_write("DELETE FROM materials WHERE id = ?", (material_id,))

    @staticmethod
    def increment_view(material_id):
        return execute_write("UPDATE materials SET view_count = view_count + 1 WHERE id = ?", (material_id,))

    @staticmethod
    def increment_download(material_id):
        return execute_write("UPDATE materials SET download_count = download_count + 1 WHERE id = ?", (material_id,))

    @staticmethod
    def get_by_id(material_id):
        return query_one("""
            SELECT m.*, s.code as subject_code, s.name as subject_name,
                   d.name as department_name, d.code as department_code,
                   sem.name as semester_name, sem.number as semester_number,
                   u.full_name as faculty_name, u.email as faculty_email
            FROM materials m
            JOIN subjects s ON m.subject_id = s.id
            JOIN departments d ON m.department_id = d.id
            JOIN semesters sem ON m.semester_id = sem.id
            JOIN users u ON m.faculty_id = u.id
            WHERE m.id = ?
        """, (material_id,))

    @staticmethod
    def get_filtered(department_id=None, semester_id=None, subject_id=None, category=None, search=None, faculty_id=None, status=None):
        query = """
            SELECT m.*, s.code as subject_code, s.name as subject_name,
                   d.name as department_name, d.code as department_code,
                   sem.name as semester_name, sem.number as semester_number,
                   u.full_name as faculty_name
            FROM materials m
            JOIN subjects s ON m.subject_id = s.id
            JOIN departments d ON m.department_id = d.id
            JOIN semesters sem ON m.semester_id = sem.id
            JOIN users u ON m.faculty_id = u.id
            WHERE 1=1
        """
        params = []
        if department_id:
            query += " AND m.department_id = ?"
            params.append(department_id)
        if semester_id:
            query += " AND m.semester_id = ?"
            params.append(semester_id)
        if subject_id:
            query += " AND m.subject_id = ?"
            params.append(subject_id)
        if category and category != 'All':
            query += " AND m.category = ?"
            params.append(category)
        if faculty_id:
            query += " AND m.faculty_id = ?"
            params.append(faculty_id)
        if status:
            query += " AND m.status = ?"
            params.append(status)
        if search:
            query += " AND (m.title LIKE ? OR m.description LIKE ? OR s.name LIKE ? OR s.code LIKE ?)"
            term = f"%{search}%"
            params.extend([term, term, term, term])
        query += " ORDER BY m.created_at DESC"
        return query_all(query, params)

class ChunkModel:
    @staticmethod
    def insert_bulk(chunks):
        """Bulk inserts chunks: list of (material_id, page_number, chunk_index, content, embedding_json)."""
        from app.database import get_db
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.executemany(
                """INSERT INTO document_chunks (material_id, page_number, chunk_index, content, embedding_json)
                   VALUES (?, ?, ?, ?, ?)""",
                chunks
            )
        return len(chunks)

    @staticmethod
    def get_by_material(material_id):
        return query_all("SELECT * FROM document_chunks WHERE material_id = ? ORDER BY page_number, chunk_index ASC", (material_id,))

    @staticmethod
    def get_by_subject(subject_id):
        return query_all("""
            SELECT c.*, m.title as material_title, m.category as material_category
            FROM document_chunks c
            JOIN materials m ON c.material_id = m.id
            WHERE m.subject_id = ? AND m.status = 'Completed'
            ORDER BY m.id, c.page_number
        """, (subject_id,))

    @staticmethod
    def delete_by_material(material_id):
        return execute_write("DELETE FROM document_chunks WHERE material_id = ?", (material_id,))

class ChatModel:
    @staticmethod
    def create_session(user_id, title="New Academic Chat", subject_id=None, material_id=None, language='en', format_pref='normal'):
        return execute_insert(
            """INSERT INTO chat_sessions (user_id, title, subject_id, material_id, language_preference, format_preference)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, title, subject_id, material_id, language, format_pref)
        )

    @staticmethod
    def get_session(session_id, user_id=None):
        if user_id:
            return query_one("SELECT * FROM chat_sessions WHERE id = ? AND user_id = ?", (session_id, user_id))
        return query_one("SELECT * FROM chat_sessions WHERE id = ?", (session_id,))

    @staticmethod
    def get_user_sessions(user_id):
        return query_all("""
            SELECT cs.*, s.name as subject_name, s.code as subject_code, m.title as material_title,
                   (SELECT COUNT(*) FROM chat_messages WHERE session_id = cs.id) as message_count,
                   (SELECT message FROM chat_messages WHERE session_id = cs.id ORDER BY created_at DESC LIMIT 1) as last_message
            FROM chat_sessions cs
            LEFT JOIN subjects s ON cs.subject_id = s.id
            LEFT JOIN materials m ON cs.material_id = m.id
            WHERE cs.user_id = ?
            ORDER BY cs.updated_at DESC
        """, (user_id,))

    @staticmethod
    def update_session_title(session_id, title):
        return execute_write("UPDATE chat_sessions SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (title, session_id))

    @staticmethod
    def delete_session(session_id, user_id):
        return execute_write("DELETE FROM chat_sessions WHERE id = ? AND user_id = ?", (session_id, user_id))

    @staticmethod
    def add_message(session_id, sender, message, sources=None, language='en', format_pref='normal'):
        sources_json = json.dumps(sources) if sources else None
        execute_write("UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (session_id,))
        return execute_insert(
            """INSERT INTO chat_messages (session_id, sender, message, sources_json, language, format)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (session_id, sender, message, sources_json, language, format_pref)
        )

    @staticmethod
    def get_messages(session_id):
        rows = query_all("SELECT * FROM chat_messages WHERE session_id = ? ORDER BY created_at ASC", (session_id,))
        for r in rows:
            if r.get('sources_json'):
                try:
                    r['sources'] = json.loads(r['sources_json'])
                except Exception:
                    r['sources'] = []
            else:
                r['sources'] = []
        return rows

class BookmarkModel:
    @staticmethod
    def toggle(user_id, material_id, notes=""):
        existing = query_one("SELECT * FROM bookmarks WHERE user_id = ? AND material_id = ?", (user_id, material_id))
        if existing:
            execute_write("DELETE FROM bookmarks WHERE user_id = ? AND material_id = ?", (user_id, material_id))
            return False
        else:
            execute_insert("INSERT INTO bookmarks (user_id, material_id, notes) VALUES (?, ?, ?)", (user_id, material_id, notes))
            return True

    @staticmethod
    def is_bookmarked(user_id, material_id):
        return query_one("SELECT 1 FROM bookmarks WHERE user_id = ? AND material_id = ?", (user_id, material_id)) is not None

    @staticmethod
    def get_user_bookmarks(user_id):
        return query_all("""
            SELECT b.*, m.title, m.description, m.category, m.page_count, m.file_path,
                   s.name as subject_name, s.code as subject_code,
                   d.code as department_code, u.full_name as faculty_name
            FROM bookmarks b
            JOIN materials m ON b.material_id = m.id
            JOIN subjects s ON m.subject_id = s.id
            JOIN departments d ON m.department_id = d.id
            JOIN users u ON m.faculty_id = u.id
            WHERE b.user_id = ?
            ORDER BY b.created_at DESC
        """, (user_id,))

class StatsModel:
    @staticmethod
    def get_platform_overview():
        students = query_one("SELECT COUNT(*) as count FROM users WHERE role = 'student'")['count']
        faculty = query_one("SELECT COUNT(*) as count FROM users WHERE role = 'faculty'")['count']
        materials = query_one("SELECT COUNT(*) as count FROM materials")['count']
        chats = query_one("SELECT COUNT(*) as count FROM chat_messages WHERE sender = 'ai'")['count']
        departments = query_one("SELECT COUNT(*) as count FROM departments")['count']
        subjects = query_one("SELECT COUNT(*) as count FROM subjects")['count']
        return {
            'student_count': students,
            'faculty_count': faculty,
            'material_count': materials,
            'ai_query_count': chats,
            'department_count': departments,
            'subject_count': subjects
        }

