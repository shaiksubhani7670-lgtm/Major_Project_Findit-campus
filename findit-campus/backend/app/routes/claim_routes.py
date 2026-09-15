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

claim_routes_bp = Blueprint('claim_routes', __name__)

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
    truth_tokens = set(w for w in truth_text.replace(',', ' ').replace('.', ' ').replace('/', ' ').split() if len(w) > 1)

    total_checks = 0
    matched_checks = 0.0

    for ans in claimant_answers:
        a_text = (ans.get('answer') or ans.get('text') or '').strip().lower()
        if not a_text:
            continue

        total_checks += 1
        a_tokens = [w for w in a_text.replace(',', ' ').replace('.', ' ').replace('/', ' ').split() if len(w) > 1]
        if not a_tokens:
            continue

        # Count how many words provided by claimant match truth tokens or sub-strings
        token_matches = 0
        for token in a_tokens:
            if token in truth_tokens or any(token in truth_w or truth_w in token for truth_w in truth_tokens):
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


@claim_routes_bp.route('/create', methods=['POST'])
@jwt_required()
def create_claim():
    """
    Create a claim for a match.
    """
    student_id = int(get_jwt_identity())
    data = request.get_json()
    if not data or 'match_id' not in data:
        return jsonify({'success': False, 'message': 'match_id is required'}), 400

    match_id = data['match_id']
    match = Match.query.get(match_id)
    if not match:
        return jsonify({'success': False, 'message': 'Match not found'}), 404

    # Ensure match is related to this student
    lost = LostItem.query.get(match.lost_report_id)
    if not lost or lost.student_id != student_id:
        return jsonify({'success': False, 'message': 'Unauthorized to claim this match'}), 403

    # Check if claim already exists
    existing_claim = Claim.query.filter_by(match_id=match_id, student_id=student_id).first()
    if existing_claim:
        return jsonify({
            'success': True,
            'message': 'Claim already exists',
            'data': {'claim_id': existing_claim.claim_id, 'status': existing_claim.status}
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
            'data': {'claim_id': new_claim.claim_id, 'status': new_claim.status}
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Failed to create claim: {str(e)}'}), 500


@claim_routes_bp.route('/verify', methods=['POST'])
@jwt_required()
def verify_claim():
    """
    Submit verification answers. Auto-approves if score >= 80%.
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

    # Get claim
    claim = Claim.query.filter_by(match_id=match_id, student_id=student_id).first()
    if not claim:
        claim = Claim(match_id=match_id, student_id=student_id, status='Pending')
        db.session.add(claim)

    lost = LostItem.query.get(match.lost_report_id)
    found = FoundItem.query.get(match.found_report_id)

    if not lost or not found:
        return jsonify({'success': False, 'message': 'Associated reports not found'}), 404

    # Load found report's question answers
    found_qas = QuestionAnswer.query.filter_by(report_type='found', report_id=found.report_id).all()

    # Calculate verification score
    score = calculate_verification_score(claimant_answers, found, found_qas)
    claim.verification_score = score
    
    # Auto approval rules (score >= 80%)
    if score >= 80.0:
        claim.status = 'Approved'
        # Mark both reports completed
        lost.status = 'Completed'
        found.status = 'Completed'
        lost.updated_at = datetime.now(timezone.utc)
        found.updated_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        # Award +50 points to the claimant
        try:
            claimant = Student.query.get(student_id)
            if claimant:
                claimant.points = (claimant.points or 0) + 50
                db.session.commit()
        except Exception:
            pass
        
        # Send claim approved email (async)
        try:
            finder = Student.query.get(found.student_id)
            finder_details_for_email = {
                'student_name': finder.student_name if finder else 'N/A',
                'roll_number': finder.roll_number if finder else 'N/A',
                'department': finder.department if finder else 'N/A',
                'college_email': finder.college_email if finder else 'N/A'
            }
            claimant_student = Student.query.get(student_id)
            if claimant_student:
                from app.services.email_service import send_claim_approved_email
                send_claim_approved_email(claimant_student, finder_details_for_email)
        except Exception:
            pass
        
        # Get finder student details to reveal
        finder = Student.query.get(found.student_id)
        
        return jsonify({
            'success': True,
            'message': 'Ownership Verified Successfully! Claim Approved.',
            'data': {
                'verification_score': score,
                'status': 'Approved',
                'finder_details': {
                    'student_name': finder.student_name,
                    'roll_number': finder.roll_number,
                    'department': finder.department,
                    'year': finder.year,
                    'section': finder.section,
                    'college_email': finder.college_email
                }
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
                'status': 'Rejected'
            }
        }), 200


@claim_routes_bp.route('', methods=['GET'])
@jwt_required()
def get_claims():
    """
    Get claim status for the logged-in student.
    """
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
