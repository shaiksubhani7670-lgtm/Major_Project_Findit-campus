"""
FindIt Campus — QR Code & Campus Location Routes
Provides QR code generation and campus location management.

Endpoints:
    GET  /api/qr/locations          — List all active campus locations
    GET  /api/qr/<location_key>     — Return QR code PNG image
    GET  /api/qr/validate/<key>     — Validate a location key exists
    POST /api/qr/seed               — Seed default campus locations (one-time setup)
"""

import io
from flask import Blueprint, jsonify, request, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.campus_location import CampusLocation

qr_routes_bp = Blueprint('qr_routes', __name__)


# --------------------------------------------------------------------------
# Default campus locations — seeded on first /api/qr/seed call
# --------------------------------------------------------------------------
DEFAULT_LOCATIONS = [
    {'key': 'library',          'name': 'Library',              'building': 'Main Block'},
    {'key': 'canteen',          'name': 'Canteen',              'building': 'Ground Floor'},
    {'key': 'lab_cse',          'name': 'CSE Laboratory',       'building': 'Lab Block'},
    {'key': 'lab_ece',          'name': 'ECE Laboratory',       'building': 'Lab Block'},
    {'key': 'lab_mech',         'name': 'Mechanical Lab',       'building': 'Lab Block'},
    {'key': 'classroom_block_a','name': 'Classroom Block A',    'building': 'Academic Block A'},
    {'key': 'classroom_block_b','name': 'Classroom Block B',    'building': 'Academic Block B'},
    {'key': 'hostel_boys',      'name': 'Boys Hostel',          'building': 'Hostel Complex'},
    {'key': 'hostel_girls',     'name': 'Girls Hostel',         'building': 'Hostel Complex'},
    {'key': 'ground',           'name': 'Sports Ground',        'building': 'Sports Area'},
    {'key': 'corridor_main',    'name': 'Main Corridor',        'building': 'Main Block'},
    {'key': 'parking',          'name': 'Parking Area',         'building': 'Campus Entrance'},
    {'key': 'washroom_block_a', 'name': 'Washroom Block A',     'building': 'Academic Block A'},
    {'key': 'main_entrance',    'name': 'Main Entrance Gate',   'building': 'Campus Gate'},
    {'key': 'auditorium',       'name': 'Auditorium',           'building': 'Main Block'},
    {'key': 'seminar_hall',     'name': 'Seminar Hall',         'building': 'Main Block'},
    {'key': 'placement_cell',   'name': 'Placement Cell',       'building': 'Admin Block'},
    {'key': 'admin_block',      'name': 'Administration Block', 'building': 'Admin Block'},
    {'key': 'medical_room',     'name': 'Medical Room',         'building': 'Main Block'},
    {'key': 'other',            'name': 'Other Location',       'building': 'Campus'},
]


def _generate_qr_png(url: str) -> bytes:
    """Generate a QR code PNG and return raw bytes."""
    try:
        import qrcode
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color='#1e40af', back_color='white')
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return buf.read()
    except Exception as e:
        # Resilient fallback: use requests if local library not available
        try:
            import requests
            import urllib.parse
            encoded = urllib.parse.quote(url)
            resp = requests.get(f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={encoded}&color=1e40af", timeout=4)
            if resp.status_code == 200 and len(resp.content) > 100:
                return resp.content
        except Exception:
            pass
        raise RuntimeError(f'Could not generate QR code: {e}')


@qr_routes_bp.route('/locations', methods=['GET'])
@jwt_required()
def list_locations():
    """Return all active campus QR locations."""
    locations = CampusLocation.query.filter_by(is_active=True).order_by(
        CampusLocation.location_name
    ).all()
    return jsonify({
        'success': True,
        'message': f'{len(locations)} campus locations found',
        'data': {'locations': [loc.to_dict() for loc in locations]}
    }), 200


@qr_routes_bp.route('/validate/<string:location_key>', methods=['GET'])
@jwt_required()
def validate_location(location_key):
    """Validate that a location key exists and return its display name."""
    loc = CampusLocation.query.filter_by(
        location_key=location_key, is_active=True
    ).first()
    if not loc:
        # Accept 'other' or unknown keys gracefully — treat as "Other Location"
        return jsonify({
            'success': True,
            'data': {
                'valid': False,
                'location_key': location_key,
                'location_name': location_key.replace('_', ' ').title(),
            }
        }), 200
    return jsonify({
        'success': True,
        'data': {
            'valid': True,
            'location_key': loc.location_key,
            'location_name': loc.location_name,
            'building': loc.building,
            'description': loc.description,
        }
    }), 200


@qr_routes_bp.route('/<string:location_key>', methods=['GET'])
def get_qr_code(location_key):
    """
    Return a QR code PNG for the given location key.
    The QR code encodes the URL: /report-found?location=<location_key>

    This endpoint does NOT require JWT so physical QR codes can be scanned
    by students who haven't logged in yet. The /report-found page will
    redirect to /login if not authenticated, preserving the ?location= param.
    """
    loc = CampusLocation.query.filter_by(
        location_key=location_key, is_active=True
    ).first()

    # If unknown key, still generate QR for it (graceful degradation)
    if not loc:
        display_name = location_key.replace('_', ' ').title()
    else:
        display_name = loc.location_name

    # Determine the base URL
    try:
        base_url = current_app.config.get('APP_URL', 'https://findit-virid.vercel.app')
    except Exception:
        base_url = 'https://findit-virid.vercel.app'

    target_url = f"{base_url}/report-found?location={location_key}"

    try:
        png_bytes = _generate_qr_png(target_url)
        return send_file(
            io.BytesIO(png_bytes),
            mimetype='image/png',
            as_attachment=False,
            download_name=f'qr_{location_key}.png'
        )
    except RuntimeError as e:
        # Fallback: return JSON with the URL if qrcode library isn't installed
        return jsonify({
            'success': False,
            'message': str(e),
            'data': {
                'location_key': location_key,
                'location_name': display_name,
                'target_url': target_url,
                'fallback': True,
            }
        }), 200


@qr_routes_bp.route('/seed', methods=['POST'])
@jwt_required()
def seed_locations():
    """
    Seed the default campus locations into the database.
    Safe to call multiple times — uses upsert logic (skip if key exists).
    """
    created = 0
    for loc_data in DEFAULT_LOCATIONS:
        existing = CampusLocation.query.filter_by(
            location_key=loc_data['key']
        ).first()
        if not existing:
            new_loc = CampusLocation(
                location_key=loc_data['key'],
                location_name=loc_data['name'],
                building=loc_data.get('building'),
                is_active=True,
            )
            db.session.add(new_loc)
            created += 1
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'Seeded {created} new campus locations ({len(DEFAULT_LOCATIONS) - created} already existed)',
            'data': {'created': created}
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
