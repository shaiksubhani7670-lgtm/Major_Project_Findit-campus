"""
FindIt Campus — Match Routes
Lists AI matches for the logged-in student, including handover status
and two-way contact exchange (only after claim approval, never before).

Privacy rules:
  - Contact details are ONLY exposed when claim.status == 'Approved'
  - Lost user sees Finder's contact; Finder sees Owner's contact
  - Identities (owner vs finder) are never mixed up
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.match import Match
from app.models.lost_item import LostItem
from app.models.found_item import FoundItem
from app.models.student import Student
from app.models.claim import Claim

match_routes_bp = Blueprint('match_routes', __name__)


def _build_contact(student: Student, role: str) -> dict:
    """Return safe contact details for an approved claim. Never call before approval."""
    return {
        'role': role,
        'student_name': student.student_name,
        'roll_number': student.roll_number,
        'department': student.department,
        'college_email': student.college_email,
        'phone_number': student.phone_number or 'Not provided',
    }


def _enrich_match(m: Match, student_id: int) -> dict:
    """Add contact, claim status, and handover info to a match dict."""
    m_dict = m.to_dict()

    lost = LostItem.query.get(m.lost_report_id)
    found = FoundItem.query.get(m.found_report_id)

    m_dict['lost_item'] = lost.to_dict() if lost else None
    m_dict['found_item'] = found.to_dict() if found else None

    # Default — no contact, no claim info
    m_dict['approved_contact'] = None
    m_dict['claim_status'] = None
    m_dict['display_status'] = 'Possible Match'
    m_dict['handover_status'] = None
    m_dict['claim_id'] = None

    try:
        approved_claim = Claim.query.filter_by(
            match_id=m.match_id, status='Approved'
        ).first()

        # Also check Completed claims
        if not approved_claim:
            approved_claim = Claim.query.filter_by(
                match_id=m.match_id, status='Completed'
            ).first()

        if approved_claim:
            m_dict['claim_status'] = approved_claim.status
            m_dict['display_status'] = approved_claim.display_status
            m_dict['handover_status'] = approved_claim.handover_status
            m_dict['claim_id'] = approved_claim.claim_id

            is_lost_owner = bool(lost and lost.student_id == student_id)
            is_finder = bool(found and found.student_id == student_id)
            m_dict['is_lost_owner'] = is_lost_owner
            m_dict['is_finder'] = is_finder

            # Lost user → sees Finder's contact
            if is_lost_owner and found:
                finder = Student.query.get(found.student_id)
                if finder:
                    m_dict['approved_contact'] = _build_contact(finder, 'Finder')

            # Finder → sees Owner's contact
            elif is_finder and lost:
                # The owner is the student who filed the claim (lost item owner)
                owner = Student.query.get(approved_claim.student_id)
                if owner:
                    m_dict['approved_contact'] = _build_contact(owner, 'Owner')

        else:
            # Check for pending claim
            pending_claim = Claim.query.filter_by(
                match_id=m.match_id, student_id=student_id
            ).first()
            if pending_claim:
                m_dict['claim_status'] = pending_claim.status
                m_dict['display_status'] = pending_claim.display_status
                m_dict['claim_id'] = pending_claim.claim_id

    except Exception as e:
        print(f'[MatchRoutes] Error enriching match {m.match_id}: {e}')

    return m_dict


@match_routes_bp.route('/run', methods=['POST'])
@jwt_required()
def run_matching_endpoint():
    """
    Manually trigger AI matching.
    Expects JSON body: { "report_id": 1, "type": "lost" }
    """
    data = request.get_json()
    if not data or 'report_id' not in data or 'type' not in data:
        return jsonify({'success': False, 'message': 'report_id and type are required'}), 400

    report_id = data['report_id']
    report_type = data['type']

    if report_type not in ['lost', 'found']:
        return jsonify({'success': False, 'message': 'type must be lost or found'}), 400

    from app.services.matching_service import matching_service
    try:
        matches = matching_service.run_matching(report_id, report_type)
        return jsonify({
            'success': True,
            'message': f'AI Matching completed. Found {len(matches)} match(es).',
            'data': {'matches_count': len(matches)}
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'AI Matching failed: {str(e)}'}), 500


@match_routes_bp.route('', methods=['GET'])
@jwt_required()
def list_matches():
    """
    List all matches related to the logged-in student's lost or found items.
    Includes handover status and contact details (only when claim is Approved).
    """
    student_id = int(get_jwt_identity())

    lost_reports = LostItem.query.filter_by(student_id=student_id).all()
    found_reports = FoundItem.query.filter_by(student_id=student_id).all()

    lost_ids = [r.report_id for r in lost_reports]
    found_ids = [r.report_id for r in found_reports]

    if not lost_ids and not found_ids:
        return jsonify({
            'success': True,
            'message': 'No matches found',
            'data': {'matches': []}
        }), 200

    conditions = []
    if lost_ids:
        conditions.append(Match.lost_report_id.in_(lost_ids))
    if found_ids:
        conditions.append(Match.found_report_id.in_(found_ids))

    if not conditions:
        return jsonify({
            'success': True,
            'message': 'No matches found',
            'data': {'matches': []}
        }), 200

    matches = Match.query.filter(db.or_(*conditions)).order_by(
        Match.created_at.desc(), Match.match_id.desc()
    ).all()

    matches_data = [_enrich_match(m, student_id) for m in matches]

    return jsonify({
        'success': True,
        'message': 'Matches retrieved successfully',
        'data': {'matches': matches_data}
    }), 200


@match_routes_bp.route('/<int:match_id>', methods=['GET'])
@jwt_required()
def get_match_detail(match_id):
    """
    Get full details of a match including handover status and contact info.
    Only accessible to students involved in the match.
    """
    student_id = int(get_jwt_identity())
    match = Match.query.get(match_id)
    if not match:
        return jsonify({'success': False, 'message': 'Match not found'}), 404

    lost = LostItem.query.get(match.lost_report_id)
    found = FoundItem.query.get(match.found_report_id)

    if not lost or not found:
        return jsonify({'success': False, 'message': 'Associated items not found'}), 404

    # Authorization: student must own either lost or found report
    if lost.student_id != student_id and found.student_id != student_id:
        return jsonify({'success': False, 'message': 'Access denied'}), 403

    m_dict = _enrich_match(match, student_id)

    return jsonify({
        'success': True,
        'message': 'Match details retrieved successfully',
        'data': m_dict
    }), 200
