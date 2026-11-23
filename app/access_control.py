from functools import wraps
from flask import session, redirect, url_for, flash, abort, request, jsonify
from app.auth import get_current_user
from app.models import MaterialModel

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            if request.is_json or request.path.startswith('/api/') or request.path.startswith('/chat/api/'):
                return jsonify({'error': 'Authentication required. Please log in.'}), 401
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth_routes.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    """Ensure current user has one of the allowed roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({'error': 'Authentication required.'}), 401
                flash('Please log in to continue.', 'warning')
                return redirect(url_for('auth_routes.login'))
            if user['role'] not in allowed_roles:
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({'error': 'Access denied: insufficient permissions.'}), 403
                flash('Access denied: You do not have permission to view that page.', 'danger')
                if user['role'] == 'student':
                    return redirect(url_for('student.dashboard'))
                elif user['role'] == 'faculty':
                    return redirect(url_for('faculty.dashboard'))
                elif user['role'] == 'admin':
                    return redirect(url_for('admin.dashboard'))
                return redirect(url_for('main.landing'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def can_access_material(user, material):
    """
    Validates backend authorization for material access:
    - Admin: Full access
    - Faculty: Can access their own materials or materials in their department
    - Student: Can only access materials for their enrolled department & semester
    """
    if not user or not material:
        return False
    if user['role'] == 'admin':
        return True
    if user['role'] == 'faculty':
        if material['faculty_id'] == user['id'] or material['department_id'] == user['department_id']:
            return True
        return False
    if user['role'] == 'student':
        # Must match department and semester
        if material['department_id'] == user['department_id'] and material['semester_id'] == user['semester_id']:
            return True
        return False
    return False

def can_manage_material(user, material):
    """
    Verifies if user can edit/delete material:
    - Admin: Yes
    - Faculty: Only if they are the original uploader
    """
    if not user or not material:
        return False
    if user['role'] == 'admin':
        return True
    if user['role'] == 'faculty' and material['faculty_id'] == user['id']:
        return True
    return False

