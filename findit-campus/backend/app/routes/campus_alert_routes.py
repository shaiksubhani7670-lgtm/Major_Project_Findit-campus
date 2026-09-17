"""
FindIt Campus — Privacy-Safe Campus Alert Routes

Provides a public-facing (authenticated students only) view of recent lost items
with ONLY safe, anonymized data. Never exposes owner contact info, student_id, or
any personal details before ownership verification.

Endpoints:
    GET /api/campus-alerts          — Recent lost-item alerts (anonymized)
    GET /api/campus-alerts/count    — Count of active alerts (for badge)
"""

from datetime import datetime, timedelta, timezone
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.lost_item import LostItem

campus_alert_routes_bp = Blueprint('campus_alert_routes', __name__)


def _safe_alert(item: LostItem) -> dict:
    """
    Return only privacy-safe fields from a LostItem.
    NEVER include student_id, owner name, email, phone.
    """
    # Truncate description to avoid leaking unique personal identifiers
    desc = (item.description or '')[:200]

    return {
        'alert_id': item.report_id,  # used for "Report Found Item" link
        'category': item.category,
        'item_name': item.item_name,
        'color': item.color,
        'location': item.location,
        'date': item.date.isoformat() if item.date else None,
        'description': desc,
        # Safe subset of additional_details — exclude personal info keys
        'safe_details': _safe_additional_details(item.additional_details),
        'has_image': bool(item.image_path or item.image_paths),
        'created_at': item.created_at.isoformat(),
        # Link to quickly report this as found
        'report_found_url': f'/report-found?lost_ref={item.report_id}&location=',
    }


def _safe_additional_details(details: dict) -> dict:
    """Filter additional_details to only show safe, non-personal keys."""
    if not details:
        return {}
    SAFE_KEYS = {
        'brand', 'model', 'color', 'case_color', 'screen_size',
        'material', 'style', 'design', 'metal_type', 'stone',
        'approximate_size', 'condition'
    }
    return {k: v for k, v in details.items() if k.lower() in SAFE_KEYS and v}


@campus_alert_routes_bp.route('', methods=['GET'])
@jwt_required()
def get_campus_alerts():
    """
    Return recent privacy-safe lost item alerts.
    Only items with status 'Searching' or 'Matched' from the last 30 days.
    """
    days = request.args.get('days', 30, type=int)
    limit = min(request.args.get('limit', 20, type=int), 50)
    category = request.args.get('category')

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    query = LostItem.query.filter(
        LostItem.status.in_(['Searching', 'Matched']),
        LostItem.created_at >= cutoff
    )

    if category:
        query = query.filter(LostItem.category.ilike(f'%{category}%'))

    items = query.order_by(LostItem.created_at.desc()).limit(limit).all()

    alerts = [_safe_alert(item) for item in items]

    return jsonify({
        'success': True,
        'message': f'{len(alerts)} campus alert(s) found',
        'data': {
            'alerts': alerts,
            'total': len(alerts),
            'days': days,
        }
    }), 200


@campus_alert_routes_bp.route('/count', methods=['GET'])
@jwt_required()
def get_alerts_count():
    """Return the count of active campus lost-item alerts (for badge display)."""
    days = request.args.get('days', 30, type=int)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    count = LostItem.query.filter(
        LostItem.status.in_(['Searching', 'Matched']),
        LostItem.created_at >= cutoff
    ).count()

    return jsonify({
        'success': True,
        'data': {'count': count}
    }), 200
