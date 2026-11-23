import sys
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from app import create_app
from app.models import UserModel, MaterialModel, SubjectModel
import json

app = create_app()
client = app.test_client()

print("✦ Testing Padika AI Routes & Services...")

# 1. Landing Page
resp = client.get('/')
assert resp.status_code == 200, f"Landing failed: {resp.status_code}"
assert b"Your Learning." in resp.data
print("✓ [PASS] Landing Page (200 OK)")

# 2. About Page
resp = client.get('/about')
assert resp.status_code == 200, f"About failed: {resp.status_code}"
assert b"Padika AI" in resp.data
print("✓ [PASS] About Page (200 OK)")

# 3. Login Page
resp = client.get('/auth/login')
assert resp.status_code == 200, f"Login GET failed: {resp.status_code}"
assert b"Sign In" in resp.data
print("✓ [PASS] Login Page GET (200 OK)")

# 4. Student Authentication & Session
login_resp = client.post('/auth/login', data={'email': 'student@padika.ai', 'password': 'Student@123'}, follow_redirects=True)
assert login_resp.status_code == 200, f"Login POST failed: {login_resp.status_code}"
assert b"Welcome, Ananya" in login_resp.data
print("✓ [PASS] Student Login & Dashboard (200 OK)")

# 5. Materials Library
mat_resp = client.get('/materials')
assert mat_resp.status_code == 200, f"Materials failed: {mat_resp.status_code}"
assert b"Curriculum Materials Library" in mat_resp.data
print("✓ [PASS] Materials Library (200 OK)")

# 6. PDF Viewer
view_resp = client.get('/materials/1/view')
assert view_resp.status_code == 200, f"PDF Viewer failed: {view_resp.status_code}"
assert b"Grounded AI Assistant" in view_resp.data
print("✓ [PASS] Glassmorphism PDF Viewer (200 OK)")

# 7. Raw PDF Stream
pdf_file_resp = client.get('/materials/1/pdf-file')
assert pdf_file_resp.status_code == 200, f"Raw PDF stream failed: {pdf_file_resp.status_code}"
assert pdf_file_resp.mimetype == 'application/pdf'
print("✓ [PASS] Raw PDF Safe File Stream (200 OK, application/pdf)")

# 8. AI Chat Interface
chat_resp = client.get('/chat')
assert chat_resp.status_code == 200, f"Chat UI failed: {chat_resp.status_code}"
assert b"Previous Sessions" in chat_resp.data
print("✓ [PASS] AI Chatbot Page (200 OK)")

# 9. AI Chat API Send Message (RAG test)
chat_api_resp = client.post('/chat/api/send', json={
    'message': 'Explain Convolutional Neural Networks and pooling in normal format',
    'subject_id': 1,
    'language': 'en',
    'format': 'normal'
})
assert chat_api_resp.status_code == 200, f"Chat API failed: {chat_api_resp.status_code}"
chat_data = json.loads(chat_api_resp.data)
assert chat_data.get('success') is True
assert len(chat_data.get('citations', [])) > 0
print(f"✓ [PASS] RAG Chat API Endpoint: Generated answer with {len(chat_data['citations'])} page citation(s)")

# 10. Bookmark Toggle API
bm_resp = client.post('/student/api/bookmark/toggle', json={'material_id': 1})
assert bm_resp.status_code == 200
bm_data = json.loads(bm_resp.data)
assert bm_data.get('success') is True
print("✓ [PASS] AJAX Bookmark Toggle Endpoint (200 OK)")

# 11. Faculty Login & Dashboard
with client.session_transaction() as sess:
    sess.clear()
fac_resp = client.post('/auth/login', data={'email': 'faculty@padika.ai', 'password': 'Faculty@123'}, follow_redirects=True)
assert fac_resp.status_code == 200
assert b"Faculty Hub" in fac_resp.data
print("✓ [PASS] Faculty Portal Dashboard (200 OK)")

# 12. Faculty Manage Materials
fac_manage = client.get('/faculty/materials')
assert fac_manage.status_code == 200
print("✓ [PASS] Faculty Manage Materials Page (200 OK)")

# 13. Admin Login & Dashboard
with client.session_transaction() as sess:
    sess.clear()
adm_resp = client.post('/auth/login', data={'email': 'admin@padika.ai', 'password': 'Admin@123'}, follow_redirects=True)
assert adm_resp.status_code == 200
assert b"Campus Administrative Console" in adm_resp.data
print("✓ [PASS] Campus Admin Dashboard (200 OK)")

# 14. Admin Users Management
adm_users = client.get('/admin/users')
assert adm_users.status_code == 200
print("✓ [PASS] Admin User Management Page (200 OK)")

# 15. Admin Curriculum Management
adm_curr = client.get('/admin/curriculum')
assert adm_curr.status_code == 200
print("✓ [PASS] Admin Curriculum Management Page (200 OK)")

print("\n==============================================================")
print("🎉 ALL 15 INTEGRATION TESTS PASSED WITH 100% SUCCESS!")
print("==============================================================")

