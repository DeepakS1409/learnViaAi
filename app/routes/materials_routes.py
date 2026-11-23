import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, abort, jsonify
from app.auth import get_current_user
from app.access_control import login_required, can_access_material
from app.models import (
    MaterialModel, SubjectModel, DepartmentModel, SemesterModel, BookmarkModel
)

materials_bp = Blueprint('materials_routes', __name__)

@materials_bp.route('/materials')
@login_required
def library():
    user = get_current_user()
    
    # Query parameters
    dept_id = request.args.get('department_id')
    sem_id = request.args.get('semester_id')
    sub_id = request.args.get('subject_id')
    cat = request.args.get('category', 'All')
    search = request.args.get('search')
    
    # If student, default to their enrolled department and semester if not explicitly changed
    if user['role'] == 'student' and not dept_id:
        dept_id = user.get('department_id')
        sem_id = user.get('semester_id')

    materials_list = MaterialModel.get_filtered(
        department_id=int(dept_id) if dept_id else None,
        semester_id=int(sem_id) if sem_id else None,
        subject_id=int(sub_id) if sub_id else None,
        category=cat if cat != 'All' else None,
        search=search,
        status='Completed'
    )

    departments = DepartmentModel.get_all()
    semesters = SemesterModel.get_all()
    subjects = SubjectModel.get_all()

    # User bookmark IDs for quick lookup
    user_bookmarks = set(b['material_id'] for b in BookmarkModel.get_user_bookmarks(user['id']))

    return render_template('materials/library.html',
                           user=user,
                           materials=materials_list,
                           departments=departments,
                           semesters=semesters,
                           subjects=subjects,
                           user_bookmarks=user_bookmarks,
                           selected_dept=int(dept_id) if dept_id else None,
                           selected_sem=int(sem_id) if sem_id else None,
                           selected_sub=int(sub_id) if sub_id else None,
                           selected_cat=cat,
                           search=search)

@materials_bp.route('/subjects/<int:subject_id>/materials')
@login_required
def subject_materials(subject_id):
    user = get_current_user()
    subject = SubjectModel.get_by_id(subject_id)
    if not subject:
        flash('Subject not found.', 'danger')
        return redirect(url_for('materials_routes.library'))

    # Access control: students must belong to this department & semester
    if user['role'] == 'student':
        if user.get('department_id') != subject['department_id'] or user.get('semester_id') != subject['semester_id']:
            flash('You are not enrolled in this subject.', 'warning')
            return redirect(url_for('student.dashboard'))

    materials_list = MaterialModel.get_filtered(subject_id=subject_id, status='Completed')
    user_bookmarks = set(b['material_id'] for b in BookmarkModel.get_user_bookmarks(user['id']))

    return render_template('materials/subject_materials.html',
                           user=user,
                           subject=subject,
                           materials=materials_list,
                           user_bookmarks=user_bookmarks)

@materials_bp.route('/materials/<int:material_id>/view')
@login_required
def view_pdf(material_id):
    user = get_current_user()
    material = MaterialModel.get_by_id(material_id)
    if not material:
        flash('Material not found.', 'danger')
        return redirect(url_for('materials_routes.library'))

    if not can_access_material(user, material):
        flash('You do not have permission to access this material.', 'danger')
        return redirect(url_for('main.dashboard_redirect'))

    # Increment view count
    MaterialModel.increment_view(material_id)
    is_bookmarked = BookmarkModel.is_bookmarked(user['id'], material_id)

    return render_template('materials/pdf_viewer.html',
                           user=user,
                           material=material,
                           is_bookmarked=is_bookmarked)

@materials_bp.route('/materials/<int:material_id>/pdf-file')
@login_required
def serve_pdf(material_id):
    user = get_current_user()
    material = MaterialModel.get_by_id(material_id)
    if not material or not can_access_material(user, material):
        abort(403)

    if not os.path.exists(material['file_path']):
        abort(404)

    return send_file(material['file_path'], mimetype='application/pdf')

@materials_bp.route('/materials/<int:material_id>/download')
@login_required
def download_material(material_id):
    user = get_current_user()
    material = MaterialModel.get_by_id(material_id)
    if not material or not can_access_material(user, material):
        flash('Permission denied to download this file.', 'danger')
        return redirect(url_for('materials_routes.library'))

    if not os.path.exists(material['file_path']):
        flash('Physical file was not found on server.', 'danger')
        return redirect(url_for('materials_routes.library'))

    MaterialModel.increment_download(material_id)
    return send_file(material['file_path'], as_attachment=True, download_name=material['original_filename'])

