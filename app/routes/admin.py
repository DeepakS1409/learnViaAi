from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.auth import get_current_user
from app.access_control import login_required, role_required
from app.models import (
    StatsModel, UserModel, DepartmentModel, SemesterModel, SubjectModel, MaterialModel
)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    user = get_current_user()
    stats = StatsModel.get_platform_overview()
    recent_users = UserModel.get_all()[:8]
    recent_materials = MaterialModel.get_filtered()[:8]
    departments = DepartmentModel.get_all()
    return render_template('admin/dashboard.html',
                           user=user,
                           stats=stats,
                           recent_users=recent_users,
                           recent_materials=recent_materials,
                           departments=departments)

@admin_bp.route('/users')
@login_required
@role_required('admin')
def users():
    user = get_current_user()
    role_filter = request.args.get('role')
    search = request.args.get('search')
    users_list = UserModel.get_all(role_filter=role_filter, search=search)
    return render_template('admin/users.html', user=user, users=users_list, role_filter=role_filter, search=search)

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@role_required('admin')
def toggle_user_status(user_id):
    current_admin = get_current_user()
    if current_admin['id'] == user_id:
        flash('You cannot deactivate your own admin account.', 'warning')
        return redirect(url_for('admin.users'))
    
    new_status = UserModel.toggle_status(user_id)
    status_str = "activated" if new_status else "deactivated"
    flash(f"User account has been {status_str}.", 'info')
    return redirect(url_for('admin.users'))

@admin_bp.route('/curriculum', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def curriculum():
    user = get_current_user()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add_department':
            name = request.form.get('name', '').strip()
            code = request.form.get('code', '').strip().upper()
            desc = request.form.get('description', '').strip()
            if name and code:
                try:
                    DepartmentModel.create(name, code, desc)
                    flash(f'Department "{code} - {name}" created successfully.', 'success')
                except Exception as e:
                    flash(f'Error creating department: {e}', 'danger')
            return redirect(url_for('admin.curriculum'))
            
        elif action == 'add_subject':
            code = request.form.get('code', '').strip().upper()
            name = request.form.get('name', '').strip()
            dept_id = request.form.get('department_id')
            sem_id = request.form.get('semester_id')
            credits = request.form.get('credits', 3)
            desc = request.form.get('description', '').strip()
            
            if code and name and dept_id and sem_id:
                try:
                    SubjectModel.create(code, name, int(dept_id), int(sem_id), int(credits), desc)
                    flash(f'Subject "{code} - {name}" added to curriculum.', 'success')
                except Exception as e:
                    flash(f'Error creating subject: {e}', 'danger')
            return redirect(url_for('admin.curriculum'))

        elif action == 'delete_subject':
            sub_id = request.form.get('subject_id')
            if sub_id:
                SubjectModel.delete(int(sub_id))
                flash('Subject deleted from curriculum.', 'info')
            return redirect(url_for('admin.curriculum'))

        elif action == 'delete_department':
            dept_id = request.form.get('department_id')
            if dept_id:
                DepartmentModel.delete(int(dept_id))
                flash('Department and associated subjects deleted.', 'info')
            return redirect(url_for('admin.curriculum'))

    departments = DepartmentModel.get_all()
    semesters = SemesterModel.get_all()
    subjects = SubjectModel.get_all()
    return render_template('admin/curriculum.html',
                           user=user,
                           departments=departments,
                           semesters=semesters,
                           subjects=subjects)

