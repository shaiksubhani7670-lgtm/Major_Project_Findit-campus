import os
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity
)
from app import db, limiter
from app.models.student import Student
from app.models.account import Account

auth_routes_bp = Blueprint('auth_routes', __name__)


def _get_app_url():
    """
    Return the canonical public base URL of the app.
    Priority:
      1. APP_URL env var (set manually in Vercel Settings)
      2. VERCEL_PROJECT_PRODUCTION_URL (auto-injected by Vercel — always the production alias, never a preview URL)
      3. request.host_url (local development fallback)

    NOTE: We deliberately skip VERCEL_URL because it returns the current
    deployment URL (e.g. findit-abc123-team.vercel.app) which has Vercel
    Deployment Protection enabled and requires a Vercel login — unusable for
    public users clicking an email link.
    """
    if os.getenv('APP_URL'):
        return os.getenv('APP_URL').rstrip('/')
    # Vercel injects this as the stable production domain (e.g. findit-virid.vercel.app)
    prod_url = os.getenv('VERCEL_PROJECT_PRODUCTION_URL')
    if prod_url:
        return f'https://{prod_url.rstrip("/")}'
    return request.host_url.rstrip('/')

@auth_routes_bp.route('/register', methods=['POST'])
def register():
    """
    Registration is disabled. Students use pre-registered Excel accounts.
    """
    return jsonify({
        'success': False, 
        'message': 'Registration is disabled. Please login using your pre-registered Excel credentials.'
    }), 403


@auth_routes_bp.route('/login', methods=['POST'])
@limiter.limit("20 per hour")
def login():
    """
    Log in using Roll Number or College Email.
    """
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Request body is required'}), 400

    login_id = str(data.get('email', '') or data.get('roll_number', '') or '').strip()
    password = str(data.get('password', '') or '').strip()

    if not login_id or not password:
        return jsonify({'success': False, 'message': 'Roll Number/Email and Password are required'}), 400

    # Look up student by email or roll_number (case-insensitive)
    student = None
    if '@' in login_id:
        student = Student.query.filter(db.func.lower(Student.college_email) == login_id.lower()).first()
    else:
        student = Student.query.filter(db.func.lower(Student.roll_number) == login_id.lower()).first()

    if not student:
        return jsonify({'success': False, 'message': 'Invalid Credentials'}), 401

    # Look up account
    account = Account.query.filter_by(student_id=student.student_id).first()
    if not account or not account.check_password(password):
        return jsonify({'success': False, 'message': 'Invalid Credentials'}), 401

    if account.status != 'active':
        return jsonify({'success': False, 'message': 'Account is inactive. Contact administration.'}), 403

    # Update last login
    is_first_login = account.last_login is None
    account.last_login = datetime.now(timezone.utc)
    db.session.commit()

    # Send welcome email on very first login (synchronous — Vercel serverless kills daemon threads)
    if is_first_login:
        try:
            from app.services.email_service import send_welcome_email
            send_welcome_email(student)
        except Exception:
            pass

    # Generate token - identity MUST be a string for flask-jwt-extended
    access_token = create_access_token(identity=str(student.student_id))
    
    return jsonify({
        'success': True,
        'message': 'Login Successful',
        'data': {
            'access_token': access_token,
            'user': student.to_dict()
        }
    }), 200


@auth_routes_bp.route('/logout', methods=['POST'])
def logout():
    """
    Logout route.
    """
    return jsonify({'success': True, 'message': 'Logged out successfully'}), 200


@auth_routes_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """
    Change current account password.
    """
    student_id = int(get_jwt_identity())
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Request body is required'}), 400

    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    confirm_new_password = data.get('confirm_new_password', '') or data.get('confirm_password', '')

    if not current_password or not new_password or not confirm_new_password:
        return jsonify({'success': False, 'message': 'All fields are required'}), 400

    if new_password != confirm_new_password:
        return jsonify({'success': False, 'message': 'New passwords do not match'}), 400

    account = Account.query.filter_by(student_id=student_id).first()
    if not account or not account.check_password(current_password):
        return jsonify({'success': False, 'message': 'Current password is incorrect'}), 401

    # Validate new password rules
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
        return jsonify({'success': True, 'message': 'Password Updated Successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Failed to update password: {str(e)}'}), 500


@auth_routes_bp.route('/send-verification', methods=['POST'])
@jwt_required()
def send_verification():
    """
    Send or resend email verification token link to the student's registered email.
    """
    import uuid
    student_id = int(get_jwt_identity())
    student = Student.query.get(student_id)
    if not student:
        return jsonify({'success': False, 'message': 'Student not found'}), 404

    if student.is_email_verified:
        return jsonify({'success': True, 'message': 'Email is already verified!', 'data': {'is_email_verified': True}}), 200

    token = uuid.uuid4().hex
    student.email_verification_token = token
    student.email_verification_sent_at = datetime.now(timezone.utc)
    db.session.commit()

    # Send verification email
    try:
        from app.services.email_service import send_verification_email
        send_verification_email(student, token, _get_app_url())
    except Exception as e:
        print("[auth_routes] Error sending verification email:", e)

    return jsonify({
        'success': True,
        'message': f'Verification email sent to {student.college_email} from finditcampus@gmail.com',
        'data': {'email': student.college_email, 'is_email_verified': False}
    }), 200


@auth_routes_bp.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    """
    Verify email token when student clicks verification link.
    """
    token = request.args.get('token') or (request.get_json() or {}).get('token')
    if not token:
        return jsonify({'success': False, 'message': 'Verification token is required'}), 400

    student = Student.query.filter_by(email_verification_token=token).first()
    if not student:
        return jsonify({'success': False, 'message': 'Invalid or expired verification link'}), 400

    student.is_email_verified = True
    student.email_verification_token = None
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Email {student.college_email} verified successfully!',
        'data': {
            'student_name': student.student_name,
            'roll_number': student.roll_number,
            'college_email': student.college_email,
            'is_email_verified': True
        }
    }), 200


@auth_routes_bp.route('/update-email', methods=['POST'])
@jwt_required()
def update_email():
    """
    Update student email address and trigger a new verification email.
    """
    import uuid
    student_id = int(get_jwt_identity())
    student = Student.query.get(student_id)
    if not student:
        return jsonify({'success': False, 'message': 'Student not found'}), 404

    data = request.get_json() or {}
    new_email = (data.get('email') or '').strip().lower()

    if not new_email or '@' not in new_email:
        return jsonify({'success': False, 'message': 'Please provide a valid email address'}), 400

    # Check if email is used by another student
    existing = Student.query.filter(
        db.func.lower(Student.college_email) == new_email,
        Student.student_id != student_id
    ).first()
    if existing:
        return jsonify({'success': False, 'message': 'Email address is already registered to another student'}), 400

    student.college_email = new_email
    student.is_email_verified = False
    token = uuid.uuid4().hex
    student.email_verification_token = token
    student.email_verification_sent_at = datetime.now(timezone.utc)
    db.session.commit()

    # Send verification link
    try:
        from app.services.email_service import send_verification_email
        send_verification_email(student, token, _get_app_url())
    except Exception as e:
        print("[auth_routes] Error updating email verification:", e)

    return jsonify({
        'success': True,
        'message': f'Email updated to {new_email}. Verification link sent from finditcampus@gmail.com!',
        'data': student.to_dict()
    }), 200
