import threading
from datetime import date, time
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.student import Student
from app.models.lost_item import LostItem
from app.models.question_answer import QuestionAnswer

lost_routes_bp = Blueprint('lost_routes', __name__)

def trigger_matching_async(report_id, report_type):
    """Run AI matching asynchronously in a background thread."""
    from app.services.matching_service import matching_service
    # We need application context to query database inside thread
    from flask import current_app
    app = current_app._get_current_object()
    
    def run_with_context():
        with app.app_context():
            try:
                matching_service.run_matching(report_id, report_type)
            except Exception as e:
                print(f"Async matching error: {e}")

    thread = threading.Thread(target=run_with_context, daemon=True)
    thread.start()


@lost_routes_bp.route('/report', methods=['POST'])
@jwt_required()
def report_lost_item():
    """
    Submit a lost item report.
    """
    student_id = int(get_jwt_identity())
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Request body is required'}), 400

    item_name = (data.get('item_name') or '').strip()
    category = (data.get('category') or '').strip()
    color = (data.get('color') or '').strip()
    location = (data.get('location') or '').strip()
    lost_date_str = (data.get('date') or '').strip()
    lost_time_str = (data.get('time') or '').strip()
    description = (data.get('description') or '').strip()
    image_path = (data.get('image_path') or '').strip() or None
    image_paths = data.get('image_paths') or ([ image_path ] if image_path else [])
    additional_details = data.get('additional_details') or {}
    question_answers = data.get('question_answers') or []  # List of {question, answer}

    if not all([item_name, category, color, location, lost_date_str, description]):
        return jsonify({'success': False, 'message': 'Required fields are missing'}), 400

    try:
        lost_date = date.fromisoformat(lost_date_str)
        lost_time = time.fromisoformat(lost_time_str) if lost_time_str else None
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date or time format'}), 400

    try:
        lost_item = LostItem(
            student_id=student_id,
            category=category,
            item_name=item_name,
            color=color,
            location=location,
            date=lost_date,
            time=lost_time,
            description=description,
            image_path=image_path,
            image_paths=image_paths if image_paths else None,
            additional_details=additional_details,
            status='Searching'
        )
        db.session.add(lost_item)
        db.session.flush() # Get report_id

        # Save question answers
        for qa in question_answers:
            q_text = qa.get('question', '').strip()
            a_text = qa.get('answer', '').strip()
            if q_text and a_text:
                qa_entry = QuestionAnswer(
                    report_type='lost',
                    report_id=lost_item.report_id,
                    question=q_text,
                    answer=a_text
                )
                db.session.add(qa_entry)

        db.session.commit()

        # Award +5 points for reporting a lost item
        try:
            from app.models.student import Student
            reporter = Student.query.get(student_id)
            if reporter:
                reporter.points = (reporter.points or 0) + 5
                db.session.commit()
        except Exception:
            pass

        # Trigger AI Matching Engine asynchronously
        trigger_matching_async(lost_item.report_id, 'lost')

        return jsonify({
            'success': True,
            'message': 'Lost Report Submitted Successfully (+5 points earned!)',
            'data': {'report_id': lost_item.report_id}
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Failed to submit report: {str(e)}'}), 500


@lost_routes_bp.route('', methods=['GET'])
@jwt_required()
def list_lost_reports():
    """
    List lost reports with sorting, filtering, and search.
    """
    student_id = int(get_jwt_identity())
    query = LostItem.query

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

    # Search filter (item name or location or brand)
    search = request.args.get('search')
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                LostItem.item_name.ilike(search_term),
                LostItem.location.ilike(search_term),
                LostItem.description.ilike(search_term)
            )
        )

    # Sorting
    sort_by = request.args.get('sort', 'newest')
    if sort_by == 'oldest':
        query = query.order_by(LostItem.created_at.asc())
    else:
        query = query.order_by(LostItem.created_at.desc())

    # Pagination: default 10 per page
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    reports_data = []
    for report in pagination.items:
        r_dict = report.to_dict()
        # Find related student details
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


@lost_routes_bp.route('/<int:report_id>', methods=['GET'])
@jwt_required()
def get_lost_report(report_id):
    """
    Get detailed lost report including question answers.
    """
    student_id = int(get_jwt_identity())
    report = LostItem.query.get(report_id)
    if not report:
        return jsonify({'success': False, 'message': 'Report not found'}), 404

    # Allow student who created it to see it
    r_dict = report.to_dict()
    
    # Load question answers
    qa_list = QuestionAnswer.query.filter_by(report_type='lost', report_id=report_id).all()
    r_dict['question_answers'] = [qa.to_dict() for qa in qa_list]

    # Include reporter details
    student = Student.query.get(report.student_id)
    r_dict['student_name'] = student.student_name if student else 'Unknown'
    r_dict['roll_number'] = student.roll_number if student else 'Unknown'

    return jsonify({
        'success': True,
        'message': 'Report details retrieved successfully',
        'data': r_dict
    }), 200


@lost_routes_bp.route('/<int:report_id>', methods=['PUT'])
@jwt_required()
def update_lost_report(report_id):
    """
    Update lost report. Allowed only if status is 'Searching'.
    """
    student_id = int(get_jwt_identity())
    report = LostItem.query.get(report_id)
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
    lost_date_str = data.get('date')
    lost_time_str = data.get('time')
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
    
    if lost_date_str:
        try:
            report.date = date.fromisoformat(lost_date_str.strip())
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date format'}), 400
    if lost_time_str:
        try:
            report.time = time.fromisoformat(lost_time_str.strip())
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid time format'}), 400

    try:
        # Update question answers if provided
        if question_answers is not None:
            # Delete old QA
            QuestionAnswer.query.filter_by(report_type='lost', report_id=report_id).delete()
            # Insert new QA
            for qa in question_answers:
                q_text = qa.get('question', '').strip()
                a_text = qa.get('answer', '').strip()
                if q_text and a_text:
                    qa_entry = QuestionAnswer(
                        report_type='lost',
                        report_id=report_id,
                        question=q_text,
                        answer=a_text
                    )
                    db.session.add(qa_entry)

        db.session.commit()
        
        # Trigger matching engine in background since details changed
        trigger_matching_async(report.report_id, 'lost')

        return jsonify({
            'success': True,
            'message': 'Report updated successfully',
            'data': report.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Failed to update report: {str(e)}'}), 500


@lost_routes_bp.route('/<int:report_id>', methods=['DELETE'])
@jwt_required()
def delete_lost_report(report_id):
    """
    Cancel/soft delete lost report.
    """
    student_id = int(get_jwt_identity())
    report = LostItem.query.get(report_id)
    if not report:
        return jsonify({'success': False, 'message': 'Report not found'}), 404

    if report.student_id != student_id:
        return jsonify({'success': False, 'message': 'Unauthorized to cancel this report'}), 403

    if report.status == 'Completed':
        return jsonify({'success': False, 'message': 'Cannot cancel a completed report'}), 400

    try:
        # Soft delete by marking as Cancelled
        report.status = 'Cancelled'
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Report cancelled successfully'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Failed to cancel report: {str(e)}'}), 500
