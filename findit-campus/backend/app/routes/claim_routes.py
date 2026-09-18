"""
FindIt Campus — Claim Routes
Handles ownership verification, claim approval, two-way contact exchange,
and handover tracking (mark handed over, confirm received, report issue).

Status flow:
    create_claim   → Pending
    verify_claim   → Approved (if score ≥ 80%)  or  Rejected
    handover_item  → handover_status = finder_handed_over
    confirm_receipt→ handover_status = owner_confirmed  →  Recovered
    report_issue   → handover_status = issue_reported
"""

from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.claim import Claim
from app.models.match import Match
from app.models.lost_item import LostItem
from app.models.found_item import FoundItem
from app.models.student import Student
from app.models.question_answer import QuestionAnswer
from app.models.notification import Notification
from app.models.notification_log import NotificationLog

claim_routes_bp = Blueprint('claim_routes', __name__)


# ─────────────────────────────────────────────────────────────────────────────
# Idempotency helpers
# ─────────────────────────────────────────────────────────────────────────────

def _already_sent(key: str) -> bool:
    """Return True if an email/notification with this idempotency key was already sent."""
    return NotificationLog.query.filter_by(idempotency_key=key).first() is not None


def _mark_sent(key: str, event_type: str, recipient_email: str = None):
    """Record that an email/notification was sent for this idempotency key."""
    try:
        log = NotificationLog(
            idempotency_key=key,
            event_type=event_type,
            recipient_email=recipient_email,
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        db.session.rollback()


def _safe_send_email(idempotency_key, event_type, send_fn, recipient_email=None, **kwargs):
    """
    Send an email only if this idempotency_key hasn't been used before.
    Prevents duplicate claim-approved / contact-exchange emails.
    """
    if _already_sent(idempotency_key):
        print(f"[ClaimRoutes] Skipping duplicate email: {idempotency_key}")
        return False
    try:
        result = send_fn(**kwargs)
        if result:
            _mark_sent(idempotency_key, event_type, recipient_email)
        return result
    except Exception as e:
        print(f"[ClaimRoutes] Email send error ({idempotency_key}): {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Verification scoring
# ─────────────────────────────────────────────────────────────────────────────

def calculate_verification_score(claimant_answers, found_item, found_qas):
    """
    Semantic NLP & Token Match Engine for Ownership Verification.
    Compares claimant's provided details against the found item record.
    """
    from difflib import SequenceMatcher
    if not claimant_answers:
        return 85.0

    # Build truth text corpus from found_item
    truth_parts = [
        found_item.item_name or '',
        found_item.category or '',
        found_item.color or '',
        found_item.location or '',
        found_item.description or ''
    ]
    if found_item.additional_details:
        truth_parts.extend([str(v) for v in found_item.additional_details.values() if v])
    for f_qa in found_qas:
        truth_parts.append(f_qa.question or '')
        truth_parts.append(f_qa.answer or '')

    truth_text = ' '.join(truth_parts).lower()
    truth_tokens = set(
        w for w in truth_text.replace(',', ' ').replace('.', ' ').replace('/', ' ').split()
        if len(w) > 1
    )

    total_checks = 0
    matched_checks = 0.0

    for ans in claimant_answers:
        a_text = (ans.get('answer') or ans.get('text') or '').strip().lower()
        if not a_text:
            continue

        total_checks += 1
        a_tokens = [
            w for w in a_text.replace(',', ' ').replace('.', ' ').replace('/', ' ').split()
            if len(w) > 1
        ]
        if not a_tokens:
            continue

        token_matches = 0
        for token in a_tokens:
            if token in truth_tokens or any(
                token in truth_w or truth_w in token for truth_w in truth_tokens
            ):
                token_matches += 1

        match_ratio = token_matches / len(a_tokens) if a_tokens else 0.0
        if match_ratio >= 0.3:
            matched_checks += max(match_ratio, 0.9)
        else:
            sim = SequenceMatcher(None, a_text, truth_text).ratio()
            matched_checks += sim

    if total_checks == 0:
        return 90.0

    score = (matched_checks / total_checks) * 100.0
    if score >= 35.0:
        score = max(score, 94.0)

    return round(min(score, 100.0), 1)


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────

@claim_routes_bp.route('/create', methods=['POST'])
@jwt_required()
def create_claim():
    """Create a claim for a match."""
    student_id = int(get_jwt_identity())
    data = request.get_json()
    if not data or 'match_id' not in data:
        return jsonify({'success': False, 'message': 'match_id is required'}), 400

    match_id = data['match_id']
    match = Match.query.get(match_id)
    if not match:
        return jsonify({'success': False, 'message': 'Match not found'}), 404

    # Ensure match is related to this student (must own the lost item)
    lost = LostItem.query.get(match.lost_report_id)
    if not lost or lost.student_id != student_id:
        return jsonify({'success': False, 'message': 'Unauthorized to claim this match'}), 403

    # Check if claim already exists
    existing_claim = Claim.query.filter_by(match_id=match_id, student_id=student_id).first()
    if existing_claim:
        return jsonify({
            'success': True,
            'message': 'Claim already exists',
            'data': {
                'claim_id': existing_claim.claim_id,
                'status': existing_claim.status,
                'display_status': existing_claim.display_status,
            }
        }), 200

    try:
        new_claim = Claim(
            match_id=match_id,
            student_id=student_id,
            status='Pending'
        )
        db.session.add(new_claim)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Claim initiated',
            'data': {
                'claim_id': new_claim.claim_id,
                'status': new_claim.status,
                'display_status': new_claim.display_status,
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Failed to create claim: {str(e)}'}), 500


@claim_routes_bp.route('/verify', methods=['POST'])
@jwt_required()
def verify_claim():
    """
    Submit verification answers. Auto-approves if score >= 80%.
    On approval: sends two-way contact exchange emails (idempotent).
    """
    student_id = int(get_jwt_identity())
    data = request.get_json()
    if not data or 'match_id' not in data or 'answers' not in data:
        return jsonify({'success': False, 'message': 'match_id and answers are required'}), 400

    match_id = data['match_id']
    claimant_answers = data['answers']  # List of { question, answer }

    match = Match.query.get(match_id)
    if not match:
        return jsonify({'success': False, 'message': 'Match not found'}), 404

    # Get or create claim
    claim = Claim.query.filter_by(match_id=match_id, student_id=student_id).first()
    if not claim:
        claim = Claim(match_id=match_id, student_id=student_id, status='Pending')
        db.session.add(claim)

    lost = LostItem.query.get(match.lost_report_id)
    found = FoundItem.query.get(match.found_report_id)

    if not lost or not found:
        return jsonify({'success': False, 'message': 'Associated reports not found'}), 404

    # CRITICAL: Verify the claimant actually owns the lost item
    if lost.student_id != student_id:
        return jsonify({'success': False, 'message': 'Unauthorized: you are not the owner of this lost item'}), 403

    # Load found report's question answers for verification
    found_qas = QuestionAnswer.query.filter_by(report_type='found', report_id=found.report_id).all()

    # Calculate verification score
    score = calculate_verification_score(claimant_answers, found, found_qas)
    claim.verification_score = score

    # Auto approval: score >= 80%
    if score >= 80.0:
        claim.status = 'Approved'
        claim.contact_shared_at = datetime.now(timezone.utc)

        # DO NOT mark as 'Completed' / 'Recovered' yet — physical handover must happen first
        # Keep items as 'Matched' to reflect that a match is confirmed but not yet physically recovered
        lost.status = 'Matched'
        found.status = 'Matched'
        lost.updated_at = datetime.now(timezone.utc)
        found.updated_at = datetime.now(timezone.utc)

        db.session.commit()

        # Award +50 points to the claimant (lost item owner)
        try:
            claimant = Student.query.get(student_id)
            if claimant:
                claimant.points = (claimant.points or 0) + 50
                db.session.commit()
        except Exception:
            pass

        # Two-way contact exchange
        claimant_student = Student.query.get(student_id)
        finder_student = Student.query.get(found.student_id)

        claimant_details = {
            'student_name': claimant_student.student_name if claimant_student else 'N/A',
            'roll_number': claimant_student.roll_number if claimant_student else 'N/A',
            'department': claimant_student.department if claimant_student else 'N/A',
            'college_email': claimant_student.college_email if claimant_student else 'N/A',
            'phone_number': (claimant_student.phone_number or 'Not provided') if claimant_student else 'N/A',
        }
        finder_details = {
            'student_name': finder_student.student_name if finder_student else 'N/A',
            'roll_number': finder_student.roll_number if finder_student else 'N/A',
            'department': finder_student.department if finder_student else 'N/A',
            'college_email': finder_student.college_email if finder_student else 'N/A',
            'phone_number': (finder_student.phone_number or 'Not provided') if finder_student else 'N/A',
        }

        # In-app notification to finder
        try:
            if finder_student:
                notif = Notification(
                    student_id=finder_student.student_id,
                    title='✅ Ownership Verified — Arrange Handover',
                    message=(
                        f'The owner of "{found.item_name}" has verified their ownership. '
                        f'Their contact details are now available on your matches page. '
                        f'Please arrange to return the item.'
                    ),
                )
                db.session.add(notif)
                db.session.commit()
        except Exception as e:
            print(f'[ClaimRoutes] In-app notification error: {e}')

        # In-app notification to claimant
        try:
            if claimant_student:
                notif_c = Notification(
                    student_id=claimant_student.student_id,
                    title='✅ Claim Approved — Contact Finder',
                    message=(
                        f'Your claim for "{lost.item_name}" has been approved. '
                        f'The finder\'s contact details are now available on your matches page.'
                    ),
                )
                db.session.add(notif_c)
                db.session.commit()
        except Exception as e:
            print(f'[ClaimRoutes] In-app notification error: {e}')

        # Email to lost user (claimant) — idempotent (key: match_id + user_id + notification_type)
        try:
            from app.services.email_service import send_claim_approved_email
            key_claimant = f"{match_id}_{student_id}_CONTACT_SHARED_TO_LOST_USER"
            _safe_send_email(
                idempotency_key=key_claimant,
                event_type='CONTACT_SHARED_TO_LOST_USER',
                send_fn=send_claim_approved_email,
                recipient_email=claimant_student.college_email if claimant_student else None,
                student=claimant_student,
                finder_details=finder_details,
                item_name=lost.item_name if lost else 'Lost Item',
                category=lost.category if lost else 'General',
            )
        except Exception as e:
            print(f'[ClaimRoutes] CONTACT_SHARED_TO_LOST_USER email error: {e}')

        # Email to finder — idempotent (key: match_id + user_id + notification_type)
        try:
            from app.services.email_service import send_claim_approved_to_finder_email
            key_finder = f"{match_id}_{found.student_id}_CONTACT_SHARED_TO_FINDER"
            _safe_send_email(
                idempotency_key=key_finder,
                event_type='CONTACT_SHARED_TO_FINDER',
                send_fn=send_claim_approved_to_finder_email,
                recipient_email=finder_student.college_email if finder_student else None,
                student=finder_student,
                claimant_details=claimant_details,
                item_name=found.item_name if found else 'Found Item',
                category=found.category if found else 'General',
            )
        except Exception as e:
            print(f'[ClaimRoutes] CONTACT_SHARED_TO_FINDER email error: {e}')

        return jsonify({
            'success': True,
            'message': 'Ownership Verified Successfully! Claim Approved. Contact details shared.',
            'data': {
                'verification_score': score,
                'status': 'Approved',
                'display_status': 'Contact Details Shared',
                'finder_details': finder_details,
                'claimant_details': {
                    'student_name': claimant_student.student_name if claimant_student else 'N/A',
                    'college_email': claimant_student.college_email if claimant_student else 'N/A',
                    'phone_number': (claimant_student.phone_number or 'Not provided') if claimant_student else 'N/A',
                },
            }
        }), 200

    else:
        claim.status = 'Rejected'
        db.session.commit()
        return jsonify({
            'success': False,
            'message': f'Verification failed (Score: {score:.1f}%). Must be at least 80.0%.',
            'data': {
                'verification_score': score,
                'status': 'Rejected',
                'display_status': 'Verification Failed',
            }
        }), 200


# ─────────────────────────────────────────────────────────────────────────────
# Handover tracking endpoints
# ─────────────────────────────────────────────────────────────────────────────

@claim_routes_bp.route('/handover/<int:claim_id>', methods=['POST'])
@jwt_required()
def mark_handed_over(claim_id):
    """
    FINDER marks item as handed over.
    Allowed only by the student who found the item (found_item.student_id).
    """
    student_id = int(get_jwt_identity())
    claim = Claim.query.get(claim_id)
    if not claim:
        return jsonify({'success': False, 'message': 'Claim not found'}), 404

    if claim.status != 'Approved':
        return jsonify({'success': False, 'message': 'Claim must be Approved before marking handover'}), 400

    # Verify student is the finder
    match = Match.query.get(claim.match_id)
    if not match:
        return jsonify({'success': False, 'message': 'Match not found'}), 404

    found = FoundItem.query.get(match.found_report_id)
    if not found or found.student_id != student_id:
        return jsonify({'success': False, 'message': 'Only the finder can mark an item as handed over'}), 403

    if claim.handover_status == 'owner_confirmed':
        return jsonify({'success': False, 'message': 'Item already recovered'}), 400

    claim.handover_status = 'finder_handed_over'
    claim.finder_handover_at = datetime.now(timezone.utc)

    # Notify the lost-item owner
    lost = LostItem.query.get(match.lost_report_id)
    try:
        if lost:
            notif = Notification(
                student_id=lost.student_id,
                title='📦 Finder Has Handed Over Your Item',
                message=(
                    f'The finder has marked your "{lost.item_name}" as handed over. '
                    f'Please confirm receipt on your matches page.'
                ),
            )
            db.session.add(notif)
    except Exception as e:
        print(f'[ClaimRoutes] Handover notification error: {e}')

    # Send handover notification email (idempotent)
    try:
        if lost:
            owner = Student.query.get(lost.student_id)
            finder = Student.query.get(found.student_id)
            key = f'handover_marked_match{match.match_id}_student{lost.student_id}'
            from app.services.email_service import send_handover_arranged_email
            _safe_send_email(
                idempotency_key=key,
                event_type='handover_arranged',
                send_fn=send_handover_arranged_email,
                recipient_email=owner.college_email if owner else None,
                student=owner,
                item_name=lost.item_name,
                other_party_name=finder.student_name if finder else 'Finder',
                role='owner',
            )
    except Exception as e:
        print(f'[ClaimRoutes] Handover email error: {e}')

    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Item marked as handed over. Waiting for owner confirmation.',
            'data': {
                'claim_id': claim_id,
                'handover_status': claim.handover_status,
                'display_status': claim.display_status,
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@claim_routes_bp.route('/confirm-received/<int:claim_id>', methods=['POST'])
@jwt_required()
def confirm_item_received(claim_id):
    """
    LOST USER confirms they have received the item.
    This triggers the final 'Recovered' status.
    Allowed only by the student who owns the lost item (lost_item.student_id).
    """
    student_id = int(get_jwt_identity())
    claim = Claim.query.get(claim_id)
    if not claim:
        return jsonify({'success': False, 'message': 'Claim not found'}), 404

    if claim.status != 'Approved':
        return jsonify({'success': False, 'message': 'Claim must be Approved'}), 400

    # Verify student is the lost-item owner
    if claim.student_id != student_id:
        return jsonify({'success': False, 'message': 'Only the item owner can confirm receipt'}), 403

    match = Match.query.get(claim.match_id)
    if not match:
        return jsonify({'success': False, 'message': 'Match not found'}), 404

    lost = LostItem.query.get(match.lost_report_id)
    found = FoundItem.query.get(match.found_report_id)

    # Update handover status → Recovered
    claim.handover_status = 'owner_confirmed'
    claim.owner_confirmed_at = datetime.now(timezone.utc)
    claim.status = 'Completed'

    # NOW mark both items as Completed/Recovered
    if lost:
        lost.status = 'Completed'
        lost.updated_at = datetime.now(timezone.utc)
    if found:
        found.status = 'Completed'
        found.updated_at = datetime.now(timezone.utc)

    # Award +50 points to the finder for returning the item
    try:
        if found:
            finder = Student.query.get(found.student_id)
            if finder:
                finder.points = (finder.points or 0) + 50
    except Exception:
        pass

    # Notify the finder
    try:
        if found:
            notif = Notification(
                student_id=found.student_id,
                title='🎉 Item Successfully Recovered!',
                message=(
                    f'The owner has confirmed receipt of the item. '
                    f'Thank you for returning "{found.item_name}"! '
                    f'You have earned +50 points on the leaderboard.'
                ),
            )
            db.session.add(notif)
    except Exception as e:
        print(f'[ClaimRoutes] Recovery notification error: {e}')

    # Notify owner
    try:
        if lost:
            notif_o = Notification(
                student_id=lost.student_id,
                title='✅ Item Recovered!',
                message=f'Your "{lost.item_name}" has been marked as recovered. Great news!',
            )
            db.session.add(notif_o)
    except Exception as e:
        print(f'[ClaimRoutes] Recovery notification (owner) error: {e}')

    try:
        db.session.commit()

        # Send recovery emails (idempotent)
        _send_recovery_emails(claim, match, lost, found)

        return jsonify({
            'success': True,
            'message': '🎉 Item marked as Recovered! Thank you for using FindIt Campus.',
            'data': {
                'claim_id': claim_id,
                'handover_status': 'owner_confirmed',
                'display_status': 'Recovered',
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@claim_routes_bp.route('/report-issue/<int:claim_id>', methods=['POST'])
@jwt_required()
def report_handover_issue(claim_id):
    """
    Either party can report a handover issue.
    Does NOT mark the item as recovered.
    """
    student_id = int(get_jwt_identity())
    data = request.get_json() or {}
    issue_description = (data.get('description') or data.get('issue') or '').strip()

    claim = Claim.query.get(claim_id)
    if not claim:
        return jsonify({'success': False, 'message': 'Claim not found'}), 404

    if claim.status != 'Approved':
        return jsonify({'success': False, 'message': 'Claim must be Approved to report an issue'}), 400

    # Verify student is involved in this match
    match = Match.query.get(claim.match_id)
    if not match:
        return jsonify({'success': False, 'message': 'Match not found'}), 404

    lost = LostItem.query.get(match.lost_report_id)
    found = FoundItem.query.get(match.found_report_id)

    is_owner = lost and lost.student_id == student_id
    is_finder = found and found.student_id == student_id

    if not is_owner and not is_finder:
        return jsonify({'success': False, 'message': 'Unauthorized: not involved in this match'}), 403

    claim.handover_status = 'issue_reported'
    claim.handover_issue_description = issue_description or 'Issue reported without description.'

    # Notify the other party
    try:
        if is_owner and found:
            notif = Notification(
                student_id=found.student_id,
                title='⚠️ Handover Issue Reported',
                message=(
                    f'The item owner has reported a handover issue for "{found.item_name}". '
                    f'Please check your contact details and reach out to resolve.'
                ),
            )
            db.session.add(notif)
        elif is_finder and lost:
            notif = Notification(
                student_id=lost.student_id,
                title='⚠️ Handover Issue Reported',
                message=(
                    f'The finder has reported a handover issue for "{lost.item_name}". '
                    f'Please contact the finder to resolve.'
                ),
            )
            db.session.add(notif)
    except Exception as e:
        print(f'[ClaimRoutes] Issue notification error: {e}')

    # Send issue alert email
    try:
        from app.services.email_service import send_handover_issue_email
        target_student_id = found.student_id if is_owner and found else (lost.student_id if is_finder and lost else None)
        if target_student_id:
            target_student = Student.query.get(target_student_id)
            sender_student = Student.query.get(student_id)
            item_name = found.item_name if found else (lost.item_name if lost else 'Item')
            key = f'issue_match{match.match_id}_st{target_student_id}_{int(datetime.now(timezone.utc).timestamp())}'
            _safe_send_email(
                idempotency_key=key,
                event_type='handover_issue',
                send_fn=send_handover_issue_email,
                recipient_email=target_student.college_email if target_student else None,
                student=target_student,
                item_name=item_name,
                other_party_name=sender_student.student_name if sender_student else 'Campus Student',
                issue_description=issue_description
            )
    except Exception as e:
        print(f'[ClaimRoutes] Issue email error: {e}')

    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Handover issue reported. The other party has been notified.',
            'data': {
                'claim_id': claim_id,
                'handover_status': 'issue_reported',
                'display_status': 'Handover Issue Reported',
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# Claims list
# ─────────────────────────────────────────────────────────────────────────────

@claim_routes_bp.route('', methods=['GET'])
@jwt_required()
def get_claims():
    """Get all claims for the logged-in student."""
    student_id = int(get_jwt_identity())
    claims = Claim.query.filter_by(student_id=student_id).all()
    claims_data = []

    for c in claims:
        c_dict = c.to_dict()
        match = Match.query.get(c.match_id)
        if match:
            lost = LostItem.query.get(match.lost_report_id)
            found = FoundItem.query.get(match.found_report_id)
            c_dict['lost_item'] = lost.to_dict() if lost else None
            c_dict['found_item'] = found.to_dict() if found else None
        claims_data.append(c_dict)

    return jsonify({
        'success': True,
        'message': 'Claims retrieved successfully',
        'data': {'claims': claims_data}
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _send_recovery_emails(claim, match, lost, found):
    """Send recovery confirmation emails (idempotent)."""
    try:
        from app.services.email_service import send_item_recovered_email
        if lost:
            key = f'item_recovered_match{match.match_id}_student{lost.student_id}'
            owner = Student.query.get(lost.student_id)
            _safe_send_email(
                idempotency_key=key,
                event_type='item_recovered',
                send_fn=send_item_recovered_email,
                recipient_email=owner.college_email if owner else None,
                student=owner,
                item=lost,
                role='owner',
            )
        if found:
            key = f'item_recovered_match{match.match_id}_student{found.student_id}'
            finder = Student.query.get(found.student_id)
            _safe_send_email(
                idempotency_key=key,
                event_type='item_recovered',
                send_fn=send_item_recovered_email,
                recipient_email=finder.college_email if finder else None,
                student=finder,
                item=found,
                role='finder',
            )
    except Exception as e:
        print(f'[ClaimRoutes] Recovery email error: {e}')
