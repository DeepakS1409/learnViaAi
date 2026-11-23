from flask import session, redirect, url_for, flash, g
from app.models import UserModel

def login_user(user):
    """Store authenticated user id and role in Flask session."""
    session.clear()
    session['user_id'] = user['id']
    session['role'] = user['role']
    session['full_name'] = user['full_name']
    session['email'] = user['email']
    session['department_id'] = user['department_id']
    session['semester_id'] = user['semester_id']
    session['avatar_color'] = user.get('avatar_color', '#8a2be2')

def logout_user():
    """Clear session data."""
    session.clear()

def get_current_user():
    """Retrieve the currently logged-in user or None."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    user = UserModel.get_by_id(user_id)
    if not user or not user.get('is_active', 1):
        session.clear()
        return None
    return user

