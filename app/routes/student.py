from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.auth import get_current_user
from app.access_control import login_required, role_required
from app.models import (
    UserModel, SubjectModel, MaterialModel, BookmarkModel, ChatModel, DepartmentModel, SemesterModel
)

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.route('/dashboard')
@login_required
@role_required('student')
def dashboard():
    user = get_current_user()
    dept = DepartmentModel.get_by_id(user['department_id']) if user.get('department_id') else None
    sem = SemesterModel.get_by_id(user['semester_id']) if user.get('semester_id') else None
    
    # Enrolled subjects
    subjects = SubjectModel.get_by_department_and_semester(user['department_id'], user['semester_id']) if user.get('department_id') else []
    
    # Materials for student's department & semester
    materials = MaterialModel.get_filtered(
        department_id=user.get('department_id'),
        semester_id=user.get('semester_id'),
        status='Completed'
    )[:8]
    
    # Recent chats
    recent_chats = ChatModel.get_user_sessions(user['id'])[:5]
    
    # Bookmarks
    bookmarks = BookmarkModel.get_user_bookmarks(user['id'])[:6]
    
    return render_template('student/dashboard.html',
                           user=user,
                           department=dept,
                           semester=sem,
                           subjects=subjects,
                           materials=materials,
                           recent_chats=recent_chats,
                           bookmarks=bookmarks)

@student_bp.route('/materials')
@login_required
@role_required('student')
def materials():
    user = get_current_user()
    category = request.args.get('category', 'All')
    subject_id = request.args.get('subject_id')
    search = request.args.get('search')
    
    subjects = SubjectModel.get_by_department_and_semester(user['department_id'], user['semester_id']) if user.get('department_id') else []
    
    materials_list = MaterialModel.get_filtered(
        department_id=user.get('department_id'),
        semester_id=user.get('semester_id'),
        subject_id=int(subject_id) if subject_id else None,
        category=category,
        search=search,
        status='Completed'
    )
    
    return render_template('student/materials.html',
                           user=user,
                           subjects=subjects,
                           materials=materials_list,
                           selected_category=category,
                           selected_subject=subject_id,
                           search=search)

@student_bp.route('/bookmarks')
@login_required
def bookmarks():
    user = get_current_user()
    bookmarks_list = BookmarkModel.get_user_bookmarks(user['id'])
    return render_template('student/bookmarks.html', user=user, bookmarks=bookmarks_list)

@student_bp.route('/api/bookmark/toggle', methods=['POST'])
@login_required
def toggle_bookmark():
    user = get_current_user()
    data = request.get_json() or {}
    material_id = data.get('material_id')
    if not material_id:
        return jsonify({'error': 'Material ID required'}), 400
    
    is_saved = BookmarkModel.toggle(user['id'], material_id)
    return jsonify({'success': True, 'is_bookmarked': is_saved})

