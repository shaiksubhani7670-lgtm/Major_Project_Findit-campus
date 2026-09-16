from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.match import Match
from app.models.lost_item import LostItem
from app.models.found_item import FoundItem
from app.models.student import Student

match_routes_bp = Blueprint('match_routes', __name__)

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
    """
    student_id = int(get_jwt_identity())

    # Find matches where student is the owner of the lost item or the finder of the found item
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

    query = Match.query.filter(db.or_(*conditions))

    matches = query.order_by(Match.overall_score.desc()).all()
    matches_data = []

    for m in matches:
        m_dict = m.to_dict()
        # Include lost item name, found item name
        lost = LostItem.query.get(m.lost_report_id)
        found = FoundItem.query.get(m.found_report_id)

        m_dict['lost_item'] = lost.to_dict() if lost else None
        m_dict['found_item'] = found.to_dict() if found else None

        # If claim is approved, expose contact details of the other party ONLY
        m_dict['approved_contact'] = None
        m_dict['claim_status'] = None

        try:
            from app.models.claim import Claim
            approved_claim = Claim.query.filter_by(match_id=m.match_id, status='Approved').first()
            if approved_claim:
                m_dict['claim_status'] = 'Approved'

                is_lost_owner = lost and lost.student_id == student_id
                is_finder = found and found.student_id == student_id

                if is_lost_owner and found:
                    # Lost user sees finder's contact details
                    finder = Student.query.get(found.student_id)
                    if finder:
                        m_dict['approved_contact'] = {
                            'role': 'Finder',
                            'student_name': finder.student_name,
                            'roll_number': finder.roll_number,
                            'department': finder.department,
                            'college_email': finder.college_email,
                            'phone_number': finder.phone_number or 'Not provided'
                        }
                elif is_finder and lost:
                    # Finder sees owner/claimant's contact details
                    owner_claim = Claim.query.filter_by(match_id=m.match_id, status='Approved').first()
                    if owner_claim:
                        owner = Student.query.get(owner_claim.student_id)
                        if owner:
                            m_dict['approved_contact'] = {
                                'role': 'Owner',
                                'student_name': owner.student_name,
                                'roll_number': owner.roll_number,
                                'department': owner.department,
                                'college_email': owner.college_email,
                                'phone_number': owner.phone_number or 'Not provided'
                            }
        except Exception:
            pass

        matches_data.append(m_dict)

    return jsonify({
        'success': True,
        'message': 'Matches retrieved successfully',
        'data': {'matches': matches_data}
    }), 200



@match_routes_bp.route('/<int:match_id>', methods=['GET'])
@jwt_required()
def get_match_detail(match_id):
    """
    Get details of a match.
    """
    student_id = int(get_jwt_identity())
    match = Match.query.get(match_id)
    if not match:
        return jsonify({'success': False, 'message': 'Match not found'}), 404

    # Verify authorization: student must own either lost or found report
    lost = LostItem.query.get(match.lost_report_id)
    found = FoundItem.query.get(match.found_report_id)

    if not lost or not found:
        return jsonify({'success': False, 'message': 'Associated items not found'}), 404

    if lost.student_id != student_id and found.student_id != student_id:
        return jsonify({'success': False, 'message': 'Access denied'}), 403

    m_dict = match.to_dict()
    m_dict['lost_item'] = lost.to_dict()
    m_dict['found_item'] = found.to_dict()

    return jsonify({
        'success': True,
        'message': 'Match details retrieved successfully',
        'data': m_dict
    }), 200
