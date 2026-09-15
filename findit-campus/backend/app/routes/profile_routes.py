from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.student import Student
from app.models.account import Account
from app.models.lost_item import LostItem
from app.models.found_item import FoundItem

profile_routes_bp = Blueprint('profile_routes', __name__)

@profile_routes_bp.route('/', methods=['GET'])
@jwt_required()
def get_profile():
    """
    Get profile information of the logged-in student, including report statistics.
    """
    student_id = int(get_jwt_identity())
    student = Student.query.get(student_id)
    if not student:
        return jsonify({'success': False, 'message': 'Student not found'}), 404

    # Compute statistics
    # Lost reports logged by this student
    total_lost = LostItem.query.filter_by(student_id=student_id).count()
    # Found reports logged by this student
    total_found = FoundItem.query.filter_by(student_id=student_id).count()
    
    # Items returned: lost reports that are completed, or found reports that are completed
    items_returned_lost = LostItem.query.filter_by(student_id=student_id, status='Completed').count()
    items_returned_found = FoundItem.query.filter_by(student_id=student_id, status='Completed').count()
    items_returned = items_returned_lost + items_returned_found

    # Pending reports: reports with status 'Searching' or 'Matched' or 'Claim Pending'
    pending_lost = LostItem.query.filter(
        LostItem.student_id == student_id,
        LostItem.status.in_(['Searching', 'Matched', 'Claim Pending'])
    ).count()
    pending_found = FoundItem.query.filter(
        FoundItem.student_id == student_id,
        FoundItem.status.in_(['Searching', 'Matched', 'Claim Pending'])
    ).count()
    pending_reports = pending_lost + pending_found

    return jsonify({
        'success': True,
        'message': 'Profile details retrieved successfully',
        'data': {
            'student': student.to_dict(),
            'statistics': {
                'total_lost_reports': total_lost,
                'total_found_reports': total_found,
                'items_returned': items_returned,
                'pending_reports': pending_reports
            }
        }
    }), 200


@profile_routes_bp.route('/password', methods=['PUT'])
@jwt_required()
def update_password():
    """
    Change account password from profile tab.
    """
    student_id = int(get_jwt_identity())
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Request body is required'}), 400

    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')

    if not current_password or not new_password or not confirm_password:
        return jsonify({'success': False, 'message': 'All fields are required'}), 400

    if new_password != confirm_password:
        return jsonify({'success': False, 'message': 'New passwords do not match'}), 400

    account = Account.query.filter_by(student_id=student_id).first()
    if not account or not account.check_password(current_password):
        return jsonify({'success': False, 'message': 'Current password is incorrect'}), 401

    # Validate password rules
    if len(new_password) < 8:
        return jsonify({'success': False, 'message': 'Password must be at least 8 characters long'}), 400
    if not any(c.isupper() for c in new_password):
        return jsonify({'success': False, 'message': 'Password must contain at least one uppercase letter'}), 400
    if not any(c.islower() for c in new_password):
        return jsonify({'success': False, 'message': 'Password must contain at least one lowercase letter'}), 400
    if not any(c.isdigit() for c in new_password):
        return jsonify({'success': False, 'message': 'Password must contain at least one number'}), 400
    special_chars = "!@#$%^&*(),.?\":{}|<>"
    if not any(c in special_chars for c in new_password):
        return jsonify({'success': False, 'message': 'Password must contain at least one special character'}), 400

    try:
        account.set_password(new_password)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Password updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Failed to update password: {str(e)}'}), 500
