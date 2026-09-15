from datetime import date, time
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.student import Student
from app.models.found_item import FoundItem
from app.models.question_answer import QuestionAnswer
from app.routes.lost_routes import trigger_matching_async

found_routes_bp = Blueprint('found_routes', __name__)

@found_routes_bp.route('/report', methods=['POST'])
@jwt_required()
def report_found_item():
    """
    Submit a found item report.
    """
    student_id = int(get_jwt_identity())
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Request body is required'}), 400

    item_name = (data.get('item_name') or '').strip()
    category = (data.get('category') or '').strip()
    color = (data.get('color') or '').strip()
    location = (data.get('location') or '').strip()
    found_date_str = (data.get('date') or '').strip()
    found_time_str = (data.get('time') or '').strip()
    description = (data.get('description') or '').strip()
    image_path = (data.get('image_path') or '').strip() or None
    image_paths = data.get('image_paths') or ([image_path] if image_path else [])
    additional_details = data.get('additional_details') or {}
    question_answers = data.get('question_answers') or []  # List of {question, answer}

    if not all([item_name, category, color, location, found_date_str, description]):
        return jsonify({'success': False, 'message': 'Required fields are missing'}), 400

    try:
        found_date = date.fromisoformat(found_date_str)
        found_time = time.fromisoformat(found_time_str) if found_time_str else None
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date or time format'}), 400

    try:
        found_item = FoundItem(
            student_id=student_id,
            category=category,
            item_name=item_name,
            color=color,
            location=location,
            date=found_date,
            time=found_time,
            description=description,
            image_path=image_path,
            image_paths=image_paths if image_paths else None,
            additional_details=additional_details,
            status='Searching'
        )
        db.session.add(found_item)
        db.session.flush() # Get report_id

        # Save question answers
        for qa in question_answers:
            q_text = qa.get('question', '').strip()
            a_text = qa.get('answer', '').strip()
            if q_text and a_text:
                qa_entry = QuestionAnswer(
                    report_type='found',
                    report_id=found_item.report_id,
                    question=q_text,
                    answer=a_text
                )
                db.session.add(qa_entry)

        db.session.commit()

        # Award +10 points for reporting a found item
        try:
            reporter = Student.query.get(student_id)
            if reporter:
                reporter.points = (reporter.points or 0) + 10
                db.session.commit()
        except Exception:
            pass

        # Trigger AI Matching Engine asynchronously
        trigger_matching_async(found_item.report_id, 'found')

        return jsonify({
            'success': True,
            'message': 'Found Report Submitted Successfully (+10 points earned!)',
            'data': {'report_id': found_item.report_id}
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Failed to submit report: {str(e)}'}), 500


@found_routes_bp.route('', methods=['GET'])
@jwt_required()
def list_found_reports():
    """
    List found reports with sorting, filtering, and search.
    """
    student_id = int(get_jwt_identity())
    query = FoundItem.query

    # Query params
    my_items = request.args.get('my_items')
    if my_items == 'true':
        query = query.filter_by(student_id=student_id)

    # Category filter
    category = request.args.get('category')
    if category:
        query = query.filter_by(category=category)

    # Status filter
    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)

    # Search filter
    search = request.args.get('search')
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                FoundItem.item_name.ilike(search_term),
                FoundItem.location.ilike(search_term),
                FoundItem.description.ilike(search_term)
            )
        )

    # Sorting
    sort_by = request.args.get('sort', 'newest')
    if sort_by == 'oldest':
        query = query.order_by(FoundItem.created_at.asc())
    else:
        query = query.order_by(FoundItem.created_at.desc())

    # Pagination: default 10 per page
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    reports_data = []
    for report in pagination.items:
        r_dict = report.to_dict()
        student = Student.query.get(report.student_id)
        r_dict['student_name'] = student.student_name if student else 'Unknown'
        reports_data.append(r_dict)

    return jsonify({
        'success': True,
        'message': 'Reports retrieved successfully',
        'data': {
            'reports': reports_data,
            'pagination': {
                'total': pagination.total,
                'page': pagination.page,
                'per_page': pagination.per_page,
                'pages': pagination.pages
            }
        }
    }), 200


@found_routes_bp.route('/<int:report_id>', methods=['GET'])
@jwt_required()
def get_found_report(report_id):
    """
    Get detailed found report including question answers.
    """
    report = FoundItem.query.get(report_id)
    if not report:
        return jsonify({'success': False, 'message': 'Report not found'}), 404

    r_dict = report.to_dict()
    
    # Load question answers
    qa_list = QuestionAnswer.query.filter_by(report_type='found', report_id=report_id).all()
    r_dict['question_answers'] = [qa.to_dict() for qa in qa_list]

    student = Student.query.get(report.student_id)
    r_dict['student_name'] = student.student_name if student else 'Unknown'
    r_dict['roll_number'] = student.roll_number if student else 'Unknown'

    return jsonify({
        'success': True,
        'message': 'Report details retrieved successfully',
        'data': r_dict
    }), 200


@found_routes_bp.route('/<int:report_id>', methods=['PUT'])
@jwt_required()
def update_found_report(report_id):
    """
    Update found report. Allowed only if status is 'Searching'.
    """
    student_id = int(get_jwt_identity())
    report = FoundItem.query.get(report_id)
    if not report:
        return jsonify({'success': False, 'message': 'Report not found'}), 404

    if report.student_id != student_id:
        return jsonify({'success': False, 'message': 'Unauthorized to edit this report'}), 403

    if report.status != 'Searching':
        return jsonify({'success': False, 'message': 'Cannot edit report after a match has been found'}), 400

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Request body is required'}), 400

    item_name = data.get('item_name')
    category = data.get('category')
    color = data.get('color')
    location = data.get('location')
    found_date_str = data.get('date')
    found_time_str = data.get('time')
    description = data.get('description')
    image_path = data.get('image_path')
    additional_details = data.get('additional_details')
    question_answers = data.get('question_answers')

    if item_name: report.item_name = item_name.strip()
    if category: report.category = category.strip()
    if color: report.color = color.strip()
    if location: report.location = location.strip()
    if description: report.description = description.strip()
    if image_path is not None: report.image_path = image_path.strip() or None
    if additional_details is not None: report.additional_details = additional_details
    
    if found_date_str:
        try:
            report.date = date.fromisoformat(found_date_str.strip())
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date format'}), 400
    if found_time_str:
        try:
            report.time = time.fromisoformat(found_time_str.strip())
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid time format'}), 400

    try:
        if question_answers is not None:
            QuestionAnswer.query.filter_by(report_type='found', report_id=report_id).delete()
            for qa in question_answers:
                q_text = qa.get('question', '').strip()
                a_text = qa.get('answer', '').strip()
                if q_text and a_text:
                    qa_entry = QuestionAnswer(
                        report_type='found',
                        report_id=report_id,
                        question=q_text,
                        answer=a_text
                    )
                    db.session.add(qa_entry)

        db.session.commit()
        
        trigger_matching_async(report.report_id, 'found')

        return jsonify({
            'success': True,
            'message': 'Report updated successfully',
            'data': report.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Failed to update report: {str(e)}'}), 500


@found_routes_bp.route('/<int:report_id>', methods=['DELETE'])
@jwt_required()
def delete_found_report(report_id):
    """
    Cancel/soft delete found report.
    """
    student_id = int(get_jwt_identity())
    report = FoundItem.query.get(report_id)
    if not report:
        return jsonify({'success': False, 'message': 'Report not found'}), 404

    if report.student_id != student_id:
        return jsonify({'success': False, 'message': 'Unauthorized to cancel this report'}), 403

    if report.status == 'Completed':
        return jsonify({'success': False, 'message': 'Cannot cancel a completed report'}), 400

    try:
        report.status = 'Cancelled'
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Report cancelled successfully'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Failed to cancel report: {str(e)}'}), 500
