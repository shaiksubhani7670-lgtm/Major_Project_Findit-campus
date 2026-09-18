"""
FindIt Campus — Intelligent AI Chatbot Route
Guides students step-by-step through lost/found reporting, claim verification,
handover assistance, campus locations, and FAQ support.
Works for both authenticated students and campus visitors.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.student import Student
from app.models.lost_item import LostItem
from app.models.found_item import FoundItem
from app.models.match import Match

chatbot_bp = Blueprint('chatbot', __name__)

# ---------------------------------------------------------------------------
# Chatbot Knowledge Base & Keyword Rules
# ---------------------------------------------------------------------------

GREETINGS = ['hi', 'hello', 'hey', 'help', 'start', 'hola', 'namaste', 'morning', 'afternoon', 'evening']
LOST_KEYWORDS = ['lost', 'missing', 'cant find', "can't find", 'lose', 'misplace', 'disappeared', 'dropped']
FOUND_KEYWORDS = ['found', 'see', 'saw', 'spotted', 'picked', 'collected', 'have item', 'retrieved']
MATCH_KEYWORDS = ['match', 'matches', 'matched', 'result', 'notification', 'alert', 'ai']
CLAIM_KEYWORDS = ['claim', 'verify', 'ownership', 'proof', 'collect', 'retrieve', 'get back', 'recover']
HANDOVER_KEYWORDS = ['handover', 'meet', 'exchange', 'contact', 'call finder', 'email finder', 'return item']
CONTACT_KEYWORDS = ['contact', 'helpdesk', 'office', 'room', 'phone', 'support', 'email', 'admin']
QR_KEYWORDS = ['qr', 'kiosk', 'scan', 'code']
POSTER_KEYWORDS = ['poster', 'flyer', 'print', 'pdf']
PRIVACY_KEYWORDS = ['privacy', 'safe', 'phone number', 'hidden', 'security', 'secure']
PASSWORD_KEYWORDS = ['password', 'forgot', 'change password', 'reset', 'login issue']
BROWSE_KEYWORDS = ['browse', 'search', 'look', 'find someone', 'check list', 'all items']
POINTS_KEYWORDS = ['points', 'leaderboard', 'rank', 'reward', 'score']
MAP_KEYWORDS = ['map', 'where', 'location', 'campus', 'building', 'library', 'canteen']
STATS_KEYWORDS = ['statistics', 'stats', 'data', 'analytics', 'numbers', 'rate']
STATUS_KEYWORDS = ['status', 'my report', 'my item', 'is it found', 'track']

RESPONSES = {
    'greeting': {
        'message': "Hi there! 👋 I'm **FindIt Assistant**, your campus Lost & Found companion at GIST.\n\nHere is how I can assist you right now:\n\n• 📋 **Report a Lost Item** (AI matching starts instantly)\n• 🟢 **Report a Found Item** (Help a classmate & earn +10 pts)\n• 🔍 **Check Match Alerts & Ownership Claims**\n• 🤝 **Handover & Contact Exchange Guidance**\n• 📍 **Campus Map & Hotspot Locations**\n• 📞 **Helpdesk Contact & Support**\n\nWhat would you like help with today?",
        'quick_replies': ['I lost something', 'I found something', 'Check my matches', 'How handover works', 'Helpdesk info']
    },
    'lost': {
        'message': "Don't worry, we're here to help you get it back! 🛡️\n\n**To report your lost item:**\n1. Go to **\"Report Lost Item\"** in the menu.\n2. Select the category (Laptop, Phone, Wallet, Keys, ID Card, etc.).\n3. Provide specific details (Brand, Color, distinctive marks, wallpaper).\n4. Upload photos if you have reference pictures.\n5. Answer a few security questions to protect your item.\n\nOur **AI Matching Engine** immediately scans existing found records and alerts you the moment a match appears! 🤖",
        'quick_replies': ['Go to Report Lost', 'How does AI match?', 'Browse all lost items']
    },
    'found': {
        'message': "Thank you for being a helpful member of our campus community! 🌟\n\n**How to report a found item:**\n1. Click **\"Report Found Item\"** (or scan a campus QR kiosk).\n2. Take or upload a clear photo of the item.\n3. Mention where on campus you found it (e.g. Library 2nd Floor, Canteen, CSE Lab 3).\n4. You will earn **+10 Campus Community Points**! 🏆\n\nOur system will autonomously connect you with the verified owner once ownership is proven.",
        'quick_replies': ['Go to Report Found', 'Where to deposit item?', 'How handover works']
    },
    'match': {
        'message': "🤖 **How FindIt Autonomous AI Matching Works:**\n\n• **Computer Vision**: YOLOv8 neural network extracts category, colors, and bounding details from uploaded photos.\n• **Semantic NLP**: Sentence-transformer vectors calculate similarity across item descriptions.\n• **Multi-Factor Scoring**: Image, color, text description, brand, and location are combined into a match confidence score.\n• **Instant Alerts**: When confidence is high, both students receive in-app notifications and email alerts!",
        'quick_replies': ['View my matches', 'How to claim an item', 'Back to main menu']
    },
    'claim': {
        'message': "🔐 **Verifying Ownership & Claiming Items:**\n\n1. When a match appears on your **Match Alerts** page, click **\"Verify Ownership\"**.\n2. Answer the specific verification questions about your item (e.g. stickers, lock screen, contents).\n3. If your answers match the found item, your claim is **automatically approved** (≥80% score)! ✅\n4. You earn **+50 reward points**!\n5. Both you and the finder receive contact details to coordinate a quick handover.",
        'quick_replies': ['View my matches', 'How handover works', 'Contact support']
    },
    'handover': {
        'message': "🤝 **Safe Handover Process:**\n\n• **After Claim Approval**: Contact details (College Email and Phone Number) are revealed only to the two matched students.\n• **Coordination**: Call or email the finder directly to arrange a meetup.\n• **Recommended Safe Meetup Spots**:\n  - Campus Security Desk (Main Gate)\n  - Administrative Block Helpdesk (Room 104)\n  - Central Library Foyer\n• **Completion**: The finder marks *'Item Handed Over'*, and you confirm *'Item Received'* to close the report!",
        'quick_replies': ['View my matches', 'Helpdesk info', 'Back to main menu']
    },
    'contact': {
        'message': "🏛️ **FindIt Campus Helpdesk & Support:**\n\n• **Location**: Administrative Block, Room 104, Geethanjali Institute of Science & Technology (GIST)\n• **Email**: [finditcampus@gmail.com](mailto:finditcampus@gmail.com)\n• **Operating Hours**: Monday – Saturday, 9:00 AM – 5:00 PM\n• **Security Intercom**: Ext. 204\n\nYou can also submit questions directly here to this AI assistant anytime 24/7!",
        'quick_replies': ['Campus map', 'Report a lost item', 'Back to main menu']
    },
    'qr': {
        'message': "📱 **Campus QR Quick-Reporting Kiosks:**\n\nQR stickers are deployed at key campus checkpoints:\n• 📚 **Central Library Entrance**\n• 🍽️ **Student Canteen & Cafeteria**\n• 💻 **Computer Science & IT Labs**\n• ⚽ **Sports Complex & Ground**\n\nScan any code with your phone camera to report a found item in under 30 seconds without typing!",
        'quick_replies': ['Go to QR Locations', 'Report a found item', 'Back to main menu']
    },
    'poster': {
        'message': "🖨️ **Printable Missing Item Posters:**\n\nNeed to raise awareness on campus noticeboards?\n1. Open **\"My Activity Logs\"** from your dashboard.\n2. Locate your active lost item report.\n3. Click the **\"🖨️ Poster\"** button.\n4. A high-resolution missing flyer with QR code and photos will generate instantly for print or sharing!",
        'quick_replies': ['My Activity Logs', 'Report a lost item', 'Back to main menu']
    },
    'privacy': {
        'message': "🔒 **Student Privacy Guarantee:**\n\n• Your phone number and email are **strictly protected** and NEVER shown publicly.\n• Other students cannot see who owns a found item or search for specific students.\n• Two-way contact is ONLY revealed after the claimant answers security questions and the ownership claim is approved.",
        'quick_replies': ['How to claim an item', 'Helpdesk info', 'Back to main menu']
    },
    'password': {
        'message': "🔑 **Password & Login Assistance:**\n\n• **Default Password**: Your College Roll Number (e.g. `222U1A0501`).\n• **To Change Password**: Go to **Student Profile** → Enter current password → Set a new secure password.\n• If you are having trouble logging in, please contact the campus IT administrator or helpdesk at **finditcampus@gmail.com**.",
        'quick_replies': ['Go to Profile', 'Go to Login', 'Back to main menu']
    },
    'browse': {
        'message': "🔍 **Browse Campus Lost Items:**\n\nCheck active items currently being searched for on campus. You can filter by category, date, and building. If you recognize something you saw, report it right away to help a classmate!",
        'quick_replies': ['Go to Browse', 'Report a found item', 'Back to main menu']
    },
    'points': {
        'message': "⭐ **FindIt Campus Reward Points System:**\n\n• Report Lost Item: **+5 points**\n• Report Found Item: **+10 points**\n• Successful Claim / Return: **+50 points**\n\nEarn badges and climb the campus Leaderboard as a top helpful student! 🏆🥇",
        'quick_replies': ['View Leaderboard', 'Report a found item', 'Back to main menu']
    },
    'map': {
        'message': "🗺️ **Interactive Campus Map & Heatmaps:**\n\nView where items are most frequently lost and recovered across campus (Library, Canteen, Labs, Classroom Block). Click pins on the map to see details!",
        'quick_replies': ['Go to Campus Map', 'Helpdesk info', 'Back to main menu']
    },
    'stats': {
        'message': "📊 **Campus Recovery Metrics:**\n\n• Over **87+** items successfully returned to verified owners.\n• Average AI matching turnaround: **Under 15 minutes**.\n• Top hotspot: Central Library & Classroom corridors.",
        'quick_replies': ['View Statistics', 'Browse all lost items', 'Back to main menu']
    },
    'status': {
        'message': "📋 You can check the real-time status of all your reports on your **Dashboard** or **My Activity Logs** page. Active reports participate continuously in AI matching!",
        'quick_replies': ['Go to Dashboard', 'My Activity Logs', 'Check my matches']
    },
    'fallback': {
        'message': "I'm not quite sure about that specific phrase, but I can assist you with:\n\n• 📋 Reporting lost or found items\n• 🤖 How AI image & text matching works\n• 🔐 How to claim an item with proof of ownership\n• 🤝 Arranging safe handovers\n• 🏛️ Helpdesk location & contact details\n\nWhat would you like to do?",
        'quick_replies': ['I lost something', 'I found something', 'How handover works', 'Helpdesk info']
    }
}

QUICK_REPLY_ROUTES = {
    'Go to Report Lost': '/report-lost',
    'Go to Report Found': '/report-found',
    'View my matches': '/matches',
    'Check my matches': '/matches',
    'Go to Profile': '/profile',
    'Go to Browse': '/browse-lost',
    'Browse all lost items': '/browse-lost',
    'View Leaderboard': '/leaderboard',
    'Go to Campus Map': '/map',
    'Campus map': '/map',
    'View Statistics': '/statistics',
    'Go to QR Locations': '/qr-locations',
    'My Activity Logs': '/my-reports',
    'Go to Dashboard': '/dashboard',
    'Go to Login': '/login',
    'Helpdesk info': None,
    'Back to main menu': None
}


def _detect_intent(message: str) -> str:
    """Detect intent from user message via keyword matching."""
    msg = message.lower().strip()

    if any(g in msg for g in GREETINGS) and len(msg.split()) <= 4:
        return 'greeting'
    if any(k in msg for k in HANDOVER_KEYWORDS):
        return 'handover'
    if any(k in msg for k in CONTACT_KEYWORDS):
        return 'contact'
    if any(k in msg for k in QR_KEYWORDS):
        return 'qr'
    if any(k in msg for k in POSTER_KEYWORDS):
        return 'poster'
    if any(k in msg for k in PRIVACY_KEYWORDS):
        return 'privacy'
    if any(k in msg for k in STATUS_KEYWORDS):
        return 'status'
    if any(k in msg for k in LOST_KEYWORDS):
        return 'lost'
    if any(k in msg for k in FOUND_KEYWORDS):
        return 'found'
    if any(k in msg for k in MATCH_KEYWORDS):
        return 'match'
    if any(k in msg for k in CLAIM_KEYWORDS):
        return 'claim'
    if any(k in msg for k in PASSWORD_KEYWORDS):
        return 'password'
    if any(k in msg for k in BROWSE_KEYWORDS):
        return 'browse'
    if any(k in msg for k in POINTS_KEYWORDS):
        return 'points'
    if any(k in msg for k in MAP_KEYWORDS):
        return 'map'
    if any(k in msg for k in STATS_KEYWORDS):
        return 'stats'
    if 'main menu' in msg or 'back' in msg or 'start over' in msg or 'menu' in msg:
        return 'greeting'
    return 'fallback'


@chatbot_bp.route('/message', methods=['POST'])
@jwt_required(optional=True)
def chatbot_message():
    """
    Process a chatbot message and return an informative response.
    Accessible to logged-in students AND campus visitors.
    Expects: { "message": "..." }
    Returns: { "message": "...", "quick_replies": [...], "redirect_url": "..." }
    """
    data = request.get_json() or {}
    user_message = str(data.get('message', '')).strip()

    student_id = get_jwt_identity()
    student = None
    if student_id:
        try:
            student = Student.query.get(int(student_id))
        except Exception:
            student = None

    if not user_message:
        intent = 'greeting'
    else:
        intent = _detect_intent(user_message)

    response = RESPONSES.get(intent, RESPONSES['fallback'])
    message_text = response['message']
    quick_replies = list(response.get('quick_replies', []))

    # Personalized greeting for logged-in students
    if intent == 'greeting' and student:
        first_name = (student.student_name or 'Student').split()[0]
        points = student.points or 0
        active_lost = LostItem.query.filter_by(student_id=student.student_id, is_active=True).count()
        message_text = (
            f"Hi **{first_name}**! 👋 Welcome back to FindIt Campus.\n\n"
            f"⭐ **Your Points**: `{points} pts`\n"
            f"📋 **Active Lost Reports**: `{active_lost}`\n\n"
            f"How can I help you right now?"
        )
        quick_replies = ['Check my matches', 'I lost something', 'I found something', 'My Activity Logs', 'Helpdesk info']

    # Personalized status inquiry
    elif intent == 'status' and student:
        latest_lost = LostItem.query.filter_by(student_id=student.student_id).order_by(LostItem.created_at.desc()).first()
        if latest_lost:
            matches_count = Match.query.filter_by(lost_report_id=latest_lost.report_id).count()
            message_text = (
                f"📋 **Your Latest Report Status:**\n\n"
                f"• **Item**: {latest_lost.item_name}\n"
                f"• **Current Status**: `{latest_lost.status}`\n"
                f"• **AI Matches**: `{matches_count}` possible match{'es' if matches_count != 1 else ''}\n\n"
                f"Go to **Match Alerts** to view matched items and verify ownership."
            )
            quick_replies = ['View my matches', 'Report a lost item', 'Back to main menu']
        else:
            message_text = "You haven't reported any lost items yet. Click below to file a report if you are missing something on campus!"
            quick_replies = ['Go to Report Lost', 'Go to Report Found', 'Back to main menu']

    # Check if this quick reply has a redirect
    redirect_url = QUICK_REPLY_ROUTES.get(user_message)

    return jsonify({
        'success': True,
        'data': {
            'message': message_text,
            'quick_replies': quick_replies,
            'intent': intent,
            'redirect_url': redirect_url
        }
    }), 200
