"""
FindIt Campus — Auth Utilities
JWT helpers, role-based access decorators, and password utilities.
"""

from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app.models.user import User, UserRole


def role_required(*roles):
    """
    Decorator to restrict endpoint access by user role.

    Usage:
        @role_required(UserRole.ADMIN)
        @role_required(UserRole.STAFF, UserRole.ADMIN)
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = User.query.get(user_id)

            if user is None:
                return jsonify({'error': 'User not found'}), 404

            if not user.is_active:
                return jsonify({'error': 'Account is deactivated'}), 403

            if user.role not in roles:
                return jsonify({
                    'error': 'Forbidden',
                    'message': f'This action requires one of the following roles: {", ".join(r.value for r in roles)}'
                }), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator


def get_current_user():
    """
    Get the currently authenticated user from the JWT token.
    Returns None if not authenticated.
    """
    try:
        user_id = get_jwt_identity()
        return User.query.get(user_id)
    except Exception:
        return None


def get_client_ip():
    """Extract client IP address from the request, handling proxies."""
    if request.headers.get('X-Forwarded-For'):
        return request.headers['X-Forwarded-For'].split(',')[0].strip()
    return request.remote_addr


def get_user_agent():
    """Extract user agent string from the request."""
    return request.headers.get('User-Agent', 'Unknown')[:500]
