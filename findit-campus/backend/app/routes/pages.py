from flask import Blueprint, render_template, redirect

pages_bp = Blueprint('pages', __name__)

@pages_bp.route('/')
@pages_bp.route('/landing')
def landing():
    return render_template('landing.html')

@pages_bp.route('/login')
def login():
    return render_template('login.html')

@pages_bp.route('/register')
def register():
    return redirect('/login')

@pages_bp.route('/dashboard')
@pages_bp.route('/student/dashboard')
def dashboard():
    return render_template('student_dashboard.html')

@pages_bp.route('/report-lost')
@pages_bp.route('/student/report')
def report_lost():
    return render_template('student_report.html')

@pages_bp.route('/report-found')
@pages_bp.route('/student/found')
def report_found():
    return render_template('student_found.html')

@pages_bp.route('/matches')
@pages_bp.route('/student/matches')
def matches_page():
    return render_template('student_matches.html')

@pages_bp.route('/claims')
@pages_bp.route('/student/claims')
def claims_page():
    return render_template('student_claims.html')

@pages_bp.route('/my-reports')
def my_reports():
    return render_template('student_reports.html')

@pages_bp.route('/notifications')
def notifications():
    return render_template('notifications.html')

@pages_bp.route('/profile')
def profile():
    return render_template('profile.html')

@pages_bp.route('/browse-lost')
def browse_lost():
    return render_template('browse_lost.html')

# ─── New Feature Pages ──────────────────────────────────────────────
@pages_bp.route('/leaderboard')
def leaderboard():
    return render_template('leaderboard.html')

@pages_bp.route('/statistics')
def statistics():
    return render_template('statistics.html')

@pages_bp.route('/calendar')
def calendar():
    return render_template('calendar_view.html')

@pages_bp.route('/timeline')
def timeline():
    return render_template('timeline.html')

@pages_bp.route('/map')
def campus_map():
    return render_template('campus_map.html')

@pages_bp.route('/messages/<int:match_id>')
def messages(match_id):
    return render_template('messages.html', match_id=match_id)

@pages_bp.route('/import-students')
def import_students():
    return render_template('import_students.html')

@pages_bp.route('/poster/<int:report_id>')
def poster(report_id):
    return render_template('poster.html', report_id=report_id)

@pages_bp.route('/qr-locations')
def qr_locations():
    return render_template('qr_locations.html')

@pages_bp.route('/campus-alerts')
def campus_alerts_page():
    return render_template('campus_alerts.html')

import os
from flask import send_from_directory, current_app

@pages_bp.route('/verify-email')
def verify_email_page():
    return render_template('verify_email.html')

@pages_bp.route('/static/uploads/<report_type>/<filename>')
def serve_static_upload(report_type, filename):
    from app.routes.upload import serve_uploaded_file_by_path
    return serve_uploaded_file_by_path(f"{report_type}/{filename}")



