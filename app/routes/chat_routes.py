from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.auth import get_current_user
from app.access_control import login_required
from app.models import (
    ChatModel, SubjectModel, MaterialModel, DepartmentModel
)
from app.services.rag_service import RAGService

chat_bp = Blueprint('chat_routes', __name__, url_prefix='/chat')

@chat_bp.route('')
@login_required
def chat_view():
    user = get_current_user()
    session_id = request.args.get('session_id')
    preselected_subject = request.args.get('subject_id')
    preselected_material = request.args.get('material_id')

    # Fetch user's chat sessions
    sessions = ChatModel.get_user_sessions(user['id'])

    current_session = None
    messages = []

    if session_id:
        current_session = ChatModel.get_session(int(session_id), user_id=user['id'])
    
    if not current_session and sessions:
        # Load most recent session
        current_session = sessions[0]
    elif not current_session:
        # Create a initial session
        new_id = ChatModel.create_session(
            user_id=user['id'],
            title="Academic Consultation",
            subject_id=int(preselected_subject) if preselected_subject else None,
            material_id=int(preselected_material) if preselected_material else None
        )
        current_session = ChatModel.get_session(new_id)
        sessions = ChatModel.get_user_sessions(user['id'])

    if current_session:
        messages = ChatModel.get_messages(current_session['id'])

    # Relevant subjects based on role
    if user['role'] == 'student' and user.get('department_id'):
        subjects = SubjectModel.get_by_department_and_semester(user['department_id'], user['semester_id'])
    else:
        subjects = SubjectModel.get_all()

    # Materials for document filter
    materials = MaterialModel.get_filtered(status='Completed')
    has_gemini_key = bool(RAGService.get_api_key())

    return render_template('chat/chat.html',
                           user=user,
                           sessions=sessions,
                           current_session=current_session,
                           messages=messages,
                           subjects=subjects,
                           materials=materials,
                           preselected_subject=preselected_subject,
                           preselected_material=preselected_material,
                           has_gemini_key=has_gemini_key)

@chat_bp.route('/history')
@login_required
def history():
    user = get_current_user()
    sessions = ChatModel.get_user_sessions(user['id'])
    return render_template('chat/history.html', user=user, sessions=sessions)

@chat_bp.route('/api/send', methods=['POST'])
@login_required
def send_message():
    user = get_current_user()
    data = request.get_json() or {}
    message_text = data.get('message', '').strip()
    session_id = data.get('session_id')
    subject_id = data.get('subject_id')
    material_id = data.get('material_id')
    language = data.get('language', 'en')
    format_pref = data.get('format', 'normal')

    if not message_text:
        return jsonify({'error': 'Message text cannot be empty'}), 400

    # Ensure session exists or create one
    if not session_id:
        # Auto generate title from query
        title = message_text[:35] + ("..." if len(message_text) > 35 else "")
        session_id = ChatModel.create_session(
            user_id=user['id'],
            title=title,
            subject_id=int(subject_id) if subject_id else None,
            material_id=int(material_id) if material_id else None,
            language=language,
            format_pref=format_pref
        )
    else:
        session_id = int(session_id)
        existing_sess = ChatModel.get_session(session_id, user_id=user['id'])
        if not existing_sess:
            return jsonify({'error': 'Invalid chat session'}), 404

    # 1. Save user message to database
    ChatModel.add_message(
        session_id=session_id,
        sender='user',
        message=message_text,
        language=language,
        format_pref=format_pref
    )

    # 2. Execute RAG service with grounding and citations
    rag_result = RAGService.generate_response(
        query=message_text,
        subject_id=int(subject_id) if subject_id else None,
        material_id=int(material_id) if material_id else None,
        language_pref=language,
        format_pref=format_pref
    )

    # 3. Save AI response to database
    ChatModel.add_message(
        session_id=session_id,
        sender='ai',
        message=rag_result['answer'],
        sources=rag_result['citations'],
        language=rag_result['language'],
        format_pref=rag_result['format']
    )

    return jsonify({
        'success': True,
        'session_id': session_id,
        'answer': rag_result['answer'],
        'citations': rag_result['citations'],
        'language': rag_result['language'],
        'format': rag_result['format'],
        'grounded': rag_result['grounded']
    })

@chat_bp.route('/api/sessions/new', methods=['POST'])
@login_required
def create_new_session():
    user = get_current_user()
    data = request.get_json() or {}
    title = data.get('title', 'New Discussion')
    subject_id = data.get('subject_id')
    material_id = data.get('material_id')
    language = data.get('language', 'en')
    format_pref = data.get('format', 'normal')

    new_id = ChatModel.create_session(
        user_id=user['id'],
        title=title,
        subject_id=int(subject_id) if subject_id else None,
        material_id=int(material_id) if material_id else None,
        language=language,
        format_pref=format_pref
    )
    return jsonify({'success': True, 'session_id': new_id})

@chat_bp.route('/api/sessions/<int:session_id>', methods=['DELETE'])
@login_required
def delete_session(session_id):
    user = get_current_user()
    ChatModel.delete_session(session_id, user['id'])
    return jsonify({'success': True})

@chat_bp.route('/api/settings', methods=['GET', 'POST'])
@login_required
def ai_settings():
    from flask import session as flask_session
    if request.method == 'POST':
        data = request.get_json() or {}
        key = data.get('gemini_api_key', '').strip()
        model = data.get('gemini_model', 'gemini-1.5-flash').strip()
        flask_session['gemini_api_key'] = key
        Config.GEMINI_API_KEY = key
        if model:
            Config.GEMINI_MODEL = model
        return jsonify({'success': True, 'has_key': bool(key), 'model': Config.GEMINI_MODEL})
    
    current_key = RAGService.get_api_key()
    # Mask key for privacy
    masked_key = (current_key[:6] + "..." + current_key[-4:]) if len(current_key) > 10 else ("Configured" if current_key else "")
    return jsonify({
        'has_key': bool(current_key),
        'masked_key': masked_key,
        'model': Config.GEMINI_MODEL
    })

