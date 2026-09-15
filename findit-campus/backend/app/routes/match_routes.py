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

    # Query matches matching these IDs
    query = Match.query.filter(
        db.or_(
            Match.lost_report_id.in_(lost_ids) if lost_ids else False,
            Match.found_report_id.in_(found_ids) if found_ids else False
        )
    )

    matches = query.order_by(Match.overall_score.desc()).all()
    matches_data = []

    for m in matches:
        m_dict = m.to_dict()
        # Include lost item name, found item name
        lost = LostItem.query.get(m.lost_report_id)
        found = FoundItem.query.get(m.found_report_id)
        
        m_dict['lost_item'] = lost.to_dict() if lost else None
        m_dict['found_item'] = found.to_dict() if found else None
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
