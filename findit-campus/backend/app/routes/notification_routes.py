from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.notification import Notification

notification_routes_bp = Blueprint('notification_routes', __name__)

@notification_routes_bp.route('', methods=['GET'])
@jwt_required()
def get_notifications():
    """
    Get notifications for the logged-in student.
    """
    student_id = int(get_jwt_identity())
    notifications = Notification.query.filter_by(student_id=student_id).order_by(Notification.created_at.desc()).all()
    
    return jsonify({
        'success': True,
        'message': 'Notifications retrieved successfully',
        'data': {
            'notifications': [n.to_dict() for n in notifications]
        }
    }), 200


@notification_routes_bp.route('/read', methods=['PUT'])
@jwt_required()
def mark_all_read():
    """
    Mark all notifications as read.
    """
    student_id = int(get_jwt_identity())
    try:
        Notification.query.filter_by(student_id=student_id, is_read=False).update({'is_read': True})
        db.session.commit()
        return jsonify({'success': True, 'message': 'All notifications marked as read'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Failed to update notifications: {str(e)}'}), 500


@notification_routes_bp.route('/<int:notification_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notification_id):
    """
    Delete a specific notification.
    """
    student_id = int(get_jwt_identity())
    notification = Notification.query.get(notification_id)
    if not notification:
        return jsonify({'success': False, 'message': 'Notification not found'}), 404

    if notification.student_id != student_id:
        return jsonify({'success': False, 'message': 'Access denied'}), 403

    try:
        db.session.delete(notification)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Notification deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Failed to delete notification: {str(e)}'}), 500
