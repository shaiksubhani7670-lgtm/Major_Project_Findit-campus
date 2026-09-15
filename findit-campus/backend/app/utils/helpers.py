"""
FindIt Campus — Helper Utilities
Common utility functions used across the application.
"""

from datetime import datetime, timezone
from flask import request
from app import db


def log_action(action, message, user_id=None, level='info', details=None):
    """
    Create a system log entry.
    Import here to avoid circular imports.
    """
    from app.models.log import SystemLog, LogAction, LogLevel

    log_entry = SystemLog(
        user_id=user_id,
        action=LogAction(action) if isinstance(action, str) else action,
        level=LogLevel(level) if isinstance(level, str) else level,
        message=message,
        details=details,
        ip_address=_get_ip(),
        user_agent=request.headers.get('User-Agent', '')[:500] if request else None,
    )
    db.session.add(log_entry)
    db.session.commit()
    return log_entry


def _get_ip():
    """Get client IP from request."""
    try:
        if request.headers.get('X-Forwarded-For'):
            return request.headers['X-Forwarded-For'].split(',')[0].strip()
        return request.remote_addr
    except RuntimeError:
        return None


def paginate_query(query, page=None, per_page=None, max_per_page=100):
    """
    Paginate a SQLAlchemy query using request parameters.

    Returns:
        dict with 'items', 'total', 'page', 'per_page', 'pages'
    """
    if page is None:
        page = request.args.get('page', 1, type=int)
    if per_page is None:
        per_page = request.args.get('per_page', 20, type=int)

    per_page = min(per_page, max_per_page)
    page = max(page, 1)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return {
        'items': pagination.items,
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev,
    }


def format_datetime(dt):
    """Format datetime to ISO string, handling None."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def success_response(data=None, message=None, status_code=200):
    """Create a standardized success response."""
    response = {'success': True}
    if message:
        response['message'] = message
    if data is not None:
        response['data'] = data
    return response, status_code


def error_response(message, status_code=400, errors=None):
    """Create a standardized error response."""
    response = {'success': False, 'error': message}
    if errors:
        response['errors'] = errors
    return response, status_code
