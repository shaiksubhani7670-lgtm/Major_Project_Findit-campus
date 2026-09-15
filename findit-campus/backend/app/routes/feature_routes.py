"""
FindIt Campus — Leaderboard, Stats, Timeline, Map, Push, Import, and Message Routes
"""

from datetime import datetime, timezone, date
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.student import Student
from app.models.lost_item import LostItem
from app.models.found_item import FoundItem
from app.models.match import Match
from app.models.claim import Claim
from app.models.notification import Notification
from app.models.messaging import Message, PushSubscription

# ─── Leaderboard ────────────────────────────────────────────────────────────
leaderboard_bp = Blueprint('leaderboard', __name__)

@leaderboard_bp.route('', methods=['GET'])
@jwt_required()
def get_leaderboard():
    """Return top 20 students by points."""
    student_id = int(get_jwt_identity())
    top_students = Student.query.order_by(Student.points.desc()).limit(20).all()
    
    # Get current student's rank
    my_student = Student.query.get(student_id)
    my_rank = None
    if my_student:
        count_above = Student.query.filter(Student.points > my_student.points).count()
        my_rank = count_above + 1

    return jsonify({
        'success': True,
        'data': {
            'leaderboard': [
                {
                    'rank': idx + 1,
                    'student_id': s.student_id,
                    'student_name': s.student_name,
                    'roll_number': s.roll_number,
                    'department': s.department,
                    'points': s.points,
                    'is_me': s.student_id == student_id
                }
                for idx, s in enumerate(top_students)
            ],
            'my_rank': my_rank,
            'my_points': my_student.points if my_student else 0
        }
    }), 200


# ─── Statistics ─────────────────────────────────────────────────────────────
stats_bp = Blueprint('stats', __name__)

@stats_bp.route('', methods=['GET'])
@jwt_required()
def get_stats():
    """Return aggregate statistics for charts."""
    total_lost = LostItem.query.count()
    total_found = FoundItem.query.count()
    completed = LostItem.query.filter_by(status='Completed').count()
    recovery_rate = round((completed / total_lost * 100) if total_lost > 0 else 0, 1)

    # Category breakdown for lost items
    from sqlalchemy import func
    categories = db.session.query(
        LostItem.category, func.count(LostItem.report_id).label('count')
    ).group_by(LostItem.category).order_by(func.count(LostItem.report_id).desc()).limit(8).all()

    # Top locations
    locations = db.session.query(
        LostItem.location, func.count(LostItem.report_id).label('count')
    ).group_by(LostItem.location).order_by(func.count(LostItem.report_id).desc()).limit(6).all()

    # Monthly trend (last 6 months) - simplified
    from datetime import timedelta
    monthly = []
    today = date.today()
    for i in range(5, -1, -1):
        month_start = (today.replace(day=1) - timedelta(days=30 * i)).replace(day=1)
        if i > 0:
            month_end = (today.replace(day=1) - timedelta(days=30 * (i-1))).replace(day=1)
        else:
            month_end = today
        lost_count = LostItem.query.filter(
            LostItem.date >= month_start, LostItem.date < month_end
        ).count()
        recovered = LostItem.query.filter(
            LostItem.date >= month_start, LostItem.date < month_end,
            LostItem.status == 'Completed'
        ).count()
        monthly.append({
            'month': month_start.strftime('%b %Y'),
            'lost': lost_count,
            'recovered': recovered
        })

    return jsonify({
        'success': True,
        'data': {
            'summary': {
                'total_lost': total_lost,
                'total_found': total_found,
                'completed': completed,
                'active_lost': LostItem.query.filter_by(status='Searching').count(),
                'recovery_rate': recovery_rate,
                'total_students_active': Student.query.count()
            },
            'categories': [{'name': c[0], 'count': c[1]} for c in categories],
            'hotspots': [{'location': loc[0], 'count': loc[1]} for loc in locations],
            'monthly_trend': monthly
        }
    }), 200


# ─── Timeline ────────────────────────────────────────────────────────────────
timeline_bp = Blueprint('timeline', __name__)

@timeline_bp.route('', methods=['GET'])
@jwt_required()
def get_timeline():
    """Return chronological activity feed for the logged-in student."""
    student_id = int(get_jwt_identity())
    events = []

    # Lost reports
    for item in LostItem.query.filter_by(student_id=student_id).order_by(LostItem.created_at.desc()).limit(20).all():
        events.append({
            'type': 'lost_report',
            'icon': 'alert-circle',
            'color': 'red',
            'title': f'Reported Lost: {item.item_name}',
            'subtitle': f'{item.category} · {item.location}',
            'status': item.status,
            'report_id': item.report_id,
            'timestamp': item.created_at.isoformat()
        })

    # Found reports
    for item in FoundItem.query.filter_by(student_id=student_id).order_by(FoundItem.created_at.desc()).limit(20).all():
        events.append({
            'type': 'found_report',
            'icon': 'check-circle',
            'color': 'green',
            'title': f'Reported Found: {item.item_name}',
            'subtitle': f'{item.category} · {item.location}',
            'status': item.status,
            'report_id': item.report_id,
            'timestamp': item.created_at.isoformat()
        })

    # Matches
    lost_ids = [r.report_id for r in LostItem.query.filter_by(student_id=student_id).all()]
    found_ids = [r.report_id for r in FoundItem.query.filter_by(student_id=student_id).all()]
    if lost_ids or found_ids:
        filter_cond = []
        if lost_ids:
            filter_cond.append(Match.lost_report_id.in_(lost_ids))
        if found_ids:
            filter_cond.append(Match.found_report_id.in_(found_ids))
        for m in Match.query.filter(db.or_(*filter_cond)).order_by(Match.created_at.desc()).limit(10).all():
            lost = LostItem.query.get(m.lost_report_id)
            events.append({
                'type': 'match',
                'icon': 'zap',
                'color': 'blue',
                'title': f'AI Match Found: {lost.item_name if lost else "Item"}',
                'subtitle': f'Match confidence: {round(m.overall_score, 1)}%',
                'match_id': m.match_id,
                'timestamp': m.created_at.isoformat()
            })

    # Claims
    for c in Claim.query.filter_by(student_id=student_id).order_by(Claim.created_at.desc()).limit(10).all():
        events.append({
            'type': 'claim',
            'icon': 'shield-check' if c.status == 'Approved' else 'shield',
            'color': 'gold' if c.status == 'Approved' else 'gray',
            'title': f'Claim {c.status}',
            'subtitle': f'Verification score: {round(c.verification_score or 0, 1)}%',
            'claim_id': c.claim_id,
            'timestamp': c.created_at.isoformat()
        })

    # Sort by timestamp descending
    events.sort(key=lambda x: x['timestamp'], reverse=True)

    return jsonify({
        'success': True,
        'data': {'events': events[:40]}
    }), 200


# ─── Campus Map ──────────────────────────────────────────────────────────────
map_bp = Blueprint('campus_map', __name__)

# Known building/location → coordinates (GIST campus approximate)
LOCATION_COORDS = {
    'cse block': (17.4150, 78.4750),
    'library': (17.4148, 78.4745),
    'cafeteria': (17.4155, 78.4760),
    'main gate': (17.4140, 78.4740),
    'hostel': (17.4160, 78.4770),
    'lab': (17.4152, 78.4755),
    'ground': (17.4145, 78.4748),
    'canteen': (17.4155, 78.4758),
    'auditorium': (17.4143, 78.4752),
    'admin': (17.4142, 78.4744),
    'parking': (17.4138, 78.4738),
    'seminar': (17.4151, 78.4757)
}

DEFAULT_CENTER = (17.4148, 78.4750)

def _get_coords(location_str: str):
    loc = location_str.lower()
    for key, coords in LOCATION_COORDS.items():
        if key in loc:
            return coords
    # Add small random offset for default so markers don't all stack
    import random
    rng = random.Random(hash(location_str))
    return (
        DEFAULT_CENTER[0] + rng.uniform(-0.003, 0.003),
        DEFAULT_CENTER[1] + rng.uniform(-0.003, 0.003)
    )

@map_bp.route('/lost-items', methods=['GET'])
@jwt_required()
def get_map_items():
    """Return lost items with coordinates for campus map."""
    category = request.args.get('category')
    query = LostItem.query.filter(LostItem.status.in_(['Searching', 'Matched']))
    if category:
        query = query.filter_by(category=category)

    items = query.order_by(LostItem.created_at.desc()).limit(100).all()
    features = []
    for item in items:
        lat, lng = _get_coords(item.location)
        student = Student.query.get(item.student_id)
        features.append({
            'report_id': item.report_id,
            'item_name': item.item_name,
            'category': item.category,
            'color': item.color,
            'location': item.location,
            'description': item.description[:120] + '...' if len(item.description) > 120 else item.description,
            'status': item.status,
            'date': item.date.isoformat() if item.date else None,
            'image_path': item.image_path,
            'student_name': student.student_name if student else 'Unknown',
            'lat': lat,
            'lng': lng
        })

    return jsonify({'success': True, 'data': {'items': features}}), 200


# ─── Push Notifications ──────────────────────────────────────────────────────
push_bp = Blueprint('push', __name__)

@push_bp.route('/subscribe', methods=['POST'])
@jwt_required()
def subscribe_push():
    """Save browser push subscription."""
    student_id = int(get_jwt_identity())
    data = request.get_json()
    if not data or 'subscription' not in data:
        return jsonify({'success': False, 'message': 'subscription data required'}), 400

    try:
        # Remove old subscription for this student
        PushSubscription.query.filter_by(student_id=student_id).delete()
        sub = PushSubscription(student_id=student_id, subscription_json=data['subscription'])
        db.session.add(sub)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Push subscription saved'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@push_bp.route('/vapid-public-key', methods=['GET'])
def get_vapid_key():
    """Return the VAPID public key for push subscription."""
    key = current_app.config.get('VAPID_PUBLIC_KEY', '')
    return jsonify({'success': True, 'data': {'public_key': key}}), 200


# ─── In-App Messages ─────────────────────────────────────────────────────────
message_bp = Blueprint('messages', __name__)

@message_bp.route('/<int:match_id>', methods=['GET'])
@jwt_required()
def get_messages(match_id):
    """Get message thread for a match."""
    student_id = int(get_jwt_identity())
    match = Match.query.get(match_id)
    if not match:
        return jsonify({'success': False, 'message': 'Match not found'}), 404

    lost = LostItem.query.get(match.lost_report_id)
    found = FoundItem.query.get(match.found_report_id)

    # Authorize: student must be in this match
    if not lost or not found:
        return jsonify({'success': False, 'message': 'Associated items not found'}), 404
    if lost.student_id != student_id and found.student_id != student_id:
        return jsonify({'success': False, 'message': 'Access denied'}), 403

    # Mark messages as read
    Message.query.filter_by(match_id=match_id, is_read=False).filter(
        Message.sender_id != student_id
    ).update({'is_read': True})
    db.session.commit()

    msgs = Message.query.filter_by(match_id=match_id).order_by(Message.created_at.asc()).all()
    return jsonify({
        'success': True,
        'data': {
            'messages': [m.to_dict() for m in msgs],
            'match_id': match_id,
            'lost_item': lost.to_dict(),
            'found_item': found.to_dict()
        }
    }), 200


@message_bp.route('/<int:match_id>', methods=['POST'])
@jwt_required()
def send_message(match_id):
    """Send a message in a match thread."""
    student_id = int(get_jwt_identity())
    match = Match.query.get(match_id)
    if not match:
        return jsonify({'success': False, 'message': 'Match not found'}), 404

    lost = LostItem.query.get(match.lost_report_id)
    found = FoundItem.query.get(match.found_report_id)
    if not lost or not found:
        return jsonify({'success': False, 'message': 'Associated items not found'}), 404
    if lost.student_id != student_id and found.student_id != student_id:
        return jsonify({'success': False, 'message': 'Access denied'}), 403

    data = request.get_json()
    content = str(data.get('content', '')).strip() if data else ''
    if not content:
        return jsonify({'success': False, 'message': 'Message content is required'}), 400
    if len(content) > 1000:
        return jsonify({'success': False, 'message': 'Message too long (max 1000 chars)'}), 400

    try:
        msg = Message(match_id=match_id, sender_id=student_id, content=content)
        db.session.add(msg)

        # Create in-app notification for the other party
        other_id = found.student_id if lost.student_id == student_id else lost.student_id
        notif = Notification(
            student_id=other_id,
            title='New Message',
            message=f'You have a new message in Match #{match_id}'
        )
        db.session.add(notif)
        db.session.commit()

        return jsonify({'success': True, 'data': msg.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ─── Bulk Student Import ──────────────────────────────────────────────────────
import_bp = Blueprint('import_students', __name__)

@import_bp.route('/students', methods=['POST'])
@jwt_required()
def import_students():
    """
    Import students from an uploaded Excel file.
    Expects multipart form with key 'file'.
    """
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No Excel file provided'}), 400

    f = request.files['file']
    if not f.filename.lower().endswith('.xlsx'):
        return jsonify({'success': False, 'message': 'Only .xlsx files are supported'}), 400

    try:
        import zipfile, xml.etree.ElementTree as ET, io

        data = f.read()
        with zipfile.ZipFile(io.BytesIO(data), 'r') as z:
            shared_strings = []
            if 'xl/sharedStrings.xml' in z.namelist():
                tree = ET.fromstring(z.read('xl/sharedStrings.xml'))
                for elem in tree.iter():
                    if elem.tag.endswith('t') and elem.text:
                        shared_strings.append(elem.text)
            sheet_tree = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
            rows = []
            for row in sheet_tree.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row'):
                row_vals = []
                for cell in row.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c'):
                    t = cell.attrib.get('t')
                    v = cell.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                    val = v.text if v is not None else ''
                    if t == 's' and val.isdigit() and int(val) < len(shared_strings):
                        val = shared_strings[int(val)]
                    row_vals.append(val)
                rows.append(row_vals)

        if not rows:
            return jsonify({'success': False, 'message': 'Excel file is empty'}), 400

        headers = [str(h).strip().lower() for h in rows[0]]
        added, skipped = 0, 0

        from app.models.account import Account
        import random
        rng = random.Random(99)

        for row in rows[1:]:
            rec = {headers[i]: row[i] if i < len(row) else '' for i in range(len(headers))}
            login = str(rec.get('login', '')).strip()
            password = str(rec.get('password', '')).strip() or login
            name_val = str(rec.get('names', rec.get('name', ''))).strip() or f'Student {login}'

            if not login:
                continue

            existing = Student.query.filter_by(roll_number=login).first()
            if existing:
                skipped += 1
                continue

            student = Student(
                roll_number=login,
                student_name=name_val,
                department='AI&ML',
                year=3,
                section=rng.choice(['A', 'B', 'C']),
                college_email=f'{login.lower()}@gist.edu.in'
            )
            db.session.add(student)
            db.session.flush()

            acc = Account(student_id=student.student_id, status='active')
            acc.set_password(password)
            db.session.add(acc)
            added += 1

        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'Import complete: {added} added, {skipped} already existed.',
            'data': {'added': added, 'skipped': skipped}
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Import failed: {str(e)}'}), 500
