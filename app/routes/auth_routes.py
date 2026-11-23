from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import UserModel, DepartmentModel, SemesterModel
from app.auth import login_user, logout_user, get_current_user

auth_bp = Blueprint('auth_routes', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if get_current_user():
        return redirect(url_for('main.dashboard_redirect'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter both email and password.', 'warning')
            return render_template('auth/login.html')

        user = UserModel.get_by_email(email)
        if not user or not UserModel.verify_password(user['password_hash'], password):
            flash('Invalid email or password. Please try again.', 'danger')
            return render_template('auth/login.html')

        if not user.get('is_active', 1):
            flash('Your account has been deactivated. Please contact the administrator.', 'danger')
            return render_template('auth/login.html')

        login_user(user)
        flash(f'Welcome back, {user["full_name"]}!', 'success')
        
        next_page = request.args.get('next')
        if next_page and not next_page.startswith('http'):
            return redirect(next_page)
        return redirect(url_for('main.dashboard_redirect'))

    return render_template('auth/login.html')

@auth_bp.route('/register/student', methods=['GET', 'POST'])
def register_student():
    if get_current_user():
        return redirect(url_for('main.dashboard_redirect'))

    departments = DepartmentModel.get_all()
    semesters = SemesterModel.get_all()

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        roll_number = request.form.get('roll_number', '').strip().upper()
        department_id = request.form.get('department_id')
        semester_id = request.form.get('semester_id')

        if not (full_name and email and password and department_id and semester_id):
            flash('All required fields must be filled.', 'warning')
            return render_template('auth/register_student.html', departments=departments, semesters=semesters)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register_student.html', departments=departments, semesters=semesters)

        if UserModel.get_by_email(email):
            flash('An account with this email already exists. Please log in.', 'warning')
            return redirect(url_for('auth_routes.login'))

        user_id = UserModel.create(
            full_name=full_name,
            email=email,
            password=password,
            role='student',
            department_id=int(department_id),
            semester_id=int(semester_id),
            roll_number=roll_number
        )

        user = UserModel.get_by_id(user_id)
        login_user(user)
        flash('Student account registered successfully! Welcome to Padika AI.', 'success')
        return redirect(url_for('student.dashboard'))

    return render_template('auth/register_student.html', departments=departments, semesters=semesters)

@auth_bp.route('/register/faculty', methods=['GET', 'POST'])
def register_faculty():
    if get_current_user():
        return redirect(url_for('main.dashboard_redirect'))

    departments = DepartmentModel.get_all()

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        employee_id = request.form.get('employee_id', '').strip().upper()
        department_id = request.form.get('department_id')

        if not (full_name and email and password and employee_id and department_id):
            flash('All required fields must be filled.', 'warning')
            return render_template('auth/register_faculty.html', departments=departments)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register_faculty.html', departments=departments)

        if UserModel.get_by_email(email):
            flash('An account with this email already exists.', 'warning')
            return redirect(url_for('auth_routes.login'))

        user_id = UserModel.create(
            full_name=full_name,
            email=email,
            password=password,
            role='faculty',
            department_id=int(department_id),
            employee_id=employee_id
        )

        user = UserModel.get_by_id(user_id)
        login_user(user)
        flash('Faculty account registered successfully! You can now upload curriculum materials.', 'success')
        return redirect(url_for('faculty.dashboard'))

    return render_template('auth/register_faculty.html', departments=departments)

@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.landing'))

