from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.auth import get_current_user, login_user
from app.access_control import login_required
from app.models import UserModel, DepartmentModel, SemesterModel

profile_bp = Blueprint('profile_routes', __name__, url_prefix='/profile')

@profile_bp.route('', methods=['GET', 'POST'])
@login_required
def profile():
    user = get_current_user()
    departments = DepartmentModel.get_all()
    semesters = SemesterModel.get_all()

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        bio = request.form.get('bio', '').strip()
        dept_id = request.form.get('department_id')
        sem_id = request.form.get('semester_id')

        if full_name:
            UserModel.update_profile(
                user_id=user['id'],
                full_name=full_name,
                bio=bio,
                department_id=int(dept_id) if dept_id else None,
                semester_id=int(sem_id) if sem_id else None
            )
            # Refresh session
            updated_user = UserModel.get_by_id(user['id'])
            login_user(updated_user)
            flash('Your profile settings have been updated successfully.', 'success')
            return redirect(url_for('profile_routes.profile'))

    user_dept = DepartmentModel.get_by_id(user['department_id']) if user.get('department_id') else None
    user_sem = SemesterModel.get_by_id(user['semester_id']) if user.get('semester_id') else None

    return render_template('profile/profile.html',
                           user=user,
                           department=user_dept,
                           semester=user_sem,
                           departments=departments,
                           semesters=semesters)

