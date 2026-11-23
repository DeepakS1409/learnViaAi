from flask import Blueprint, render_template, redirect, url_for, session
from app.auth import get_current_user
from app.models import StatsModel, DepartmentModel, MaterialModel

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def landing():
    user = get_current_user()
    stats = StatsModel.get_platform_overview()
    departments = DepartmentModel.get_all()
    recent_materials = MaterialModel.get_filtered(status='Completed')[:6]
    return render_template('landing.html', user=user, stats=stats, departments=departments, recent_materials=recent_materials)

@main_bp.route('/about')
def about():
    user = get_current_user()
    stats = StatsModel.get_platform_overview()
    return render_template('about.html', user=user, stats=stats)

@main_bp.route('/dashboard')
def dashboard_redirect():
    user = get_current_user()
    if not user:
        return redirect(url_for('auth_routes.login'))
    if user['role'] == 'student':
        return redirect(url_for('student.dashboard'))
    elif user['role'] == 'faculty':
        return redirect(url_for('faculty.dashboard'))
    elif user['role'] == 'admin':
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('main.landing'))

