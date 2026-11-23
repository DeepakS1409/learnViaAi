import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from app.config import Config
from app.auth import get_current_user
from app.access_control import login_required, role_required, can_manage_material
from app.models import (
    MaterialModel, SubjectModel, DepartmentModel, SemesterModel, ChunkModel, UserModel
)
from app.services.pdf_service import PDFService
from app.services.embedding_service import EmbeddingService

faculty_bp = Blueprint('faculty', __name__, url_prefix='/faculty')

@faculty_bp.route('/dashboard')
@login_required
@role_required('faculty', 'admin')
def dashboard():
    user = get_current_user()
    dept = DepartmentModel.get_by_id(user['department_id']) if user.get('department_id') else None
    
    # Uploaded materials by this faculty
    materials = MaterialModel.get_filtered(faculty_id=user['id'])
    
    # Statistics
    total_materials = len(materials)
    total_views = sum(m['view_count'] for m in materials)
    total_downloads = sum(m['download_count'] for m in materials)
    completed_count = sum(1 for m in materials if m['status'] == 'Completed')
    
    # Available subjects for their department
    subjects = SubjectModel.get_by_department_and_semester(user['department_id']) if user.get('department_id') else SubjectModel.get_all()
    
    return render_template('faculty/dashboard.html',
                           user=user,
                           department=dept,
                           materials=materials[:6],
                           subjects=subjects,
                           stats={
                               'total_materials': total_materials,
                               'total_views': total_views,
                               'total_downloads': total_downloads,
                               'completed_count': completed_count
                           })

@faculty_bp.route('/upload', methods=['GET', 'POST'])
@login_required
@role_required('faculty', 'admin')
def upload():
    user = get_current_user()
    departments = DepartmentModel.get_all()
    semesters = SemesterModel.get_all()
    subjects = SubjectModel.get_all()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', 'Notes')
        subject_id = request.form.get('subject_id')
        department_id = request.form.get('department_id') or user.get('department_id')
        semester_id = request.form.get('semester_id')
        
        file = request.files.get('file')

        if not (title and subject_id and department_id and semester_id and file):
            flash('Please complete all required fields and select a file.', 'warning')
            return render_template('faculty/upload.html', user=user, departments=departments, semesters=semesters, subjects=subjects)

        if not file.filename or not PDFService.allowed_file(file.filename):
            flash('Please upload a valid PDF document.', 'danger')
            return render_template('faculty/upload.html', user=user, departments=departments, semesters=semesters, subjects=subjects)

        # Ensure upload folder exists
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

        original_filename = secure_filename(file.filename)
        unique_name = f"{uuid.uuid4().hex}_{original_filename}"
        file_path = os.path.join(Config.UPLOAD_FOLDER, unique_name)
        file.save(file_path)
        file_size = os.path.getsize(file_path)

        # 1. Create material record in DB with 'Processing' status
        material_id = MaterialModel.create(
            title=title,
            description=description,
            category=category,
            filename=unique_name,
            original_filename=original_filename,
            file_size=file_size,
            mime_type='application/pdf',
            file_path=file_path,
            subject_id=int(subject_id),
            department_id=int(department_id),
            semester_id=int(semester_id),
            faculty_id=user['id']
        )

        # 2. Extract text and generate chunks & embeddings
        try:
            pages = PDFService.extract_text_with_pages(file_path)
            chunks = PDFService.chunk_document(pages)

            if not chunks:
                # If PDF is scanned or empty
                MaterialModel.update_status(material_id, 'Failed', page_count=len(pages), chunk_count=0)
                flash('Warning: The uploaded PDF appears to be empty or an unindexed scanned document. We have recorded it, but AI RAG features require readable text.', 'warning')
                return redirect(url_for('faculty.manage_materials'))

            # Generate embeddings and prepare bulk insert tuples
            import json
            chunk_tuples = []
            contents = [c['content'] for c in chunks]
            embeddings = EmbeddingService.generate_embeddings_batch(contents)

            for c, emb in zip(chunks, embeddings):
                chunk_tuples.append((
                    material_id,
                    c['page_number'],
                    c['chunk_index'],
                    c['content'],
                    json.dumps(emb)
                ))

            ChunkModel.insert_bulk(chunk_tuples)
            MaterialModel.update_status(material_id, 'Completed', page_count=len(pages), chunk_count=len(chunks))

            flash(f'Successfully uploaded and indexed "{title}" ({len(pages)} pages, {len(chunks)} AI chunks created). Ready for student queries!', 'success')
            return redirect(url_for('faculty.manage_materials'))

        except Exception as e:
            MaterialModel.update_status(material_id, 'Failed')
            flash(f'Error processing PDF content: {str(e)}', 'danger')
            return redirect(url_for('faculty.manage_materials'))

    return render_template('faculty/upload.html', user=user, departments=departments, semesters=semesters, subjects=subjects)

@faculty_bp.route('/materials')
@login_required
@role_required('faculty', 'admin')
def manage_materials():
    user = get_current_user()
    if user['role'] == 'admin':
        materials = MaterialModel.get_filtered()
    else:
        materials = MaterialModel.get_filtered(faculty_id=user['id'])
    
    return render_template('faculty/manage_materials.html', user=user, materials=materials)

@faculty_bp.route('/materials/<int:material_id>/edit', methods=['POST'])
@login_required
@role_required('faculty', 'admin')
def edit_material(material_id):
    user = get_current_user()
    material = MaterialModel.get_by_id(material_id)
    if not material or not can_manage_material(user, material):
        flash('Permission denied to edit this material.', 'danger')
        return redirect(url_for('faculty.manage_materials'))

    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    category = request.form.get('category', material['category'])

    if title:
        MaterialModel.update_details(material_id, title, description, category)
        flash('Material details updated successfully.', 'success')
    return redirect(url_for('faculty.manage_materials'))

@faculty_bp.route('/materials/<int:material_id>/delete', methods=['POST'])
@login_required
@role_required('faculty', 'admin')
def delete_material(material_id):
    user = get_current_user()
    material = MaterialModel.get_by_id(material_id)
    if not material or not can_manage_material(user, material):
        flash('Permission denied to delete this material.', 'danger')
        return redirect(url_for('faculty.manage_materials'))

    # Remove physical file if exists
    try:
        if os.path.exists(material['file_path']):
            os.remove(material['file_path'])
    except Exception:
        pass

    ChunkModel.delete_by_material(material_id)
    MaterialModel.delete(material_id)
    flash(f'Material "{material["title"]}" and its vector index have been permanently deleted.', 'info')
    return redirect(url_for('faculty.manage_materials'))

