"""
FindIt Campus — Rule-Based AI Chatbot Route
Guides students step-by-step through the lost/found reporting process.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

chatbot_bp = Blueprint('chatbot', __name__)

# ---------------------------------------------------------------------------
# Chatbot knowledge base — keyword triggers → responses
# ---------------------------------------------------------------------------

GREETINGS = ['hi', 'hello', 'hey', 'help', 'start', 'hola', 'namaste']

LOST_KEYWORDS = ['lost', 'missing', 'cant find', "can't find", 'lose', 'misplace']
FOUND_KEYWORDS = ['found', 'see', 'saw', 'spotted', 'picked', 'collected', 'have item']
MATCH_KEYWORDS = ['match', 'matches', 'matched', 'result', 'notification', 'alert']
CLAIM_KEYWORDS = ['claim', 'verify', 'collect', 'retrieve', 'get back', 'recover']
PASSWORD_KEYWORDS = ['password', 'forgot', 'change password', 'reset']
BROWSE_KEYWORDS = ['browse', 'search', 'look', 'find someone', 'check']
POINTS_KEYWORDS = ['points', 'leaderboard', 'rank', 'reward']
MAP_KEYWORDS = ['map', 'where', 'location', 'campus']
STATS_KEYWORDS = ['statistics', 'stats', 'data', 'analytics', 'numbers']

RESPONSES = {
    'greeting': {
        'message': "Hi! 👋 I'm the FindIt Campus assistant. I can help you with:\n\n• 📋 **Reporting a lost item**\n• 🟢 **Reporting a found item**\n• 🔔 **Checking match alerts**\n• 🗺️ **Campus map**\n• ⭐ **Points & Leaderboard**\n\nWhat do you need help with?",
        'quick_replies': ['I lost something', 'I found something', 'Check my matches', 'View campus map', 'My points']
    },
    'lost': {
        'message': "I'm sorry to hear that! 😟 Here's how to report a lost item:\n\n1. Click **\"Report Lost\"** in the sidebar\n2. Select the item category (Laptop, Phone, Bag, etc.)\n3. Describe the item with as much detail as possible\n4. Upload a photo if you have one\n5. Specify where and when you last saw it\n\nOur AI will automatically search for matching found items and notify you! 🤖",
        'quick_replies': ['Go to Report Lost', 'What info do I need?', 'How long does matching take?']
    },
    'found': {
        'message': "That's great of you to report it! 🌟 Here's how:\n\n1. Click **\"Report Found\"** in the sidebar\n2. Describe the item clearly\n3. Upload a clear photo\n4. Specify where you found it\n5. Our AI will match it with lost reports\n\nYou'll earn **+10 points** for reporting a found item! 🏆",
        'quick_replies': ['Go to Report Found', 'What happens after I report?', 'My points']
    },
    'match': {
        'message': "🤖 Our AI matching system works 24/7! Here's how it works:\n\n• When you report a lost item, AI immediately scans all found items\n• It compares images, colors, descriptions, location & more\n• When a high-confidence match (>70%) is found, you get a notification 🔔\n• You'll also receive an **email alert** to your college email\n\nCheck your **Match Alerts** page to see current matches!",
        'quick_replies': ['View my matches', 'How accurate is the AI?', 'Claim an item']
    },
    'claim': {
        'message': "To claim an item:\n\n1. Go to **Match Alerts** → find your match\n2. Click **\"Claim This Item\"**\n3. Answer the verification questions about the item\n4. Score **≥80%** → Claim automatically **approved** ✅\n5. You'll receive finder's contact details via email\n\nThe questions verify ownership without revealing sensitive info to unverified users.",
        'quick_replies': ['View my matches', 'What questions are asked?', 'Contact support']
    },
    'password': {
        'message': "To change your password:\n\n1. Go to **Profile** (bottom-left icon)\n2. Under **Change Password** section\n3. Enter current password (your Roll Number by default)\n4. Enter new password — must have uppercase, lowercase, number, and special character\n\n⚠️ If you've forgotten your password, contact the system administrator.",
        'quick_replies': ['Go to Profile', 'Back to main menu']
    },
    'browse': {
        'message': "🔍 You can browse all active lost item reports:\n\n1. Click **\"Browse Lost Items\"** in the sidebar\n2. Use filters: Category, Color, Date Range, Brand\n3. Search by keywords\n4. If you found an item, you can report it from there too!\n\nNote: Found items are kept private for security.",
        'quick_replies': ['Go to Browse', 'Report a found item', 'Back to main menu']
    },
    'points': {
        'message': "⭐ **FindIt Campus Points System:**\n\n• Report Lost Item: **+5 points**\n• Report Found Item: **+10 points**\n• Successful Claim: **+50 points**\n\nCheck the **Leaderboard** to see your rank among all students! 🏆🥇",
        'quick_replies': ['View Leaderboard', 'How to earn more points?', 'Back to main menu']
    },
    'map': {
        'message': "🗺️ The **Campus Map** shows all active lost item reports on an interactive map.\n\n• Click any marker to see item details\n• Filter by category\n• Report items directly from the map\n\nGo to the **Campus Map** from the sidebar menu!",
        'quick_replies': ['Go to Campus Map', 'Back to main menu']
    },
    'stats': {
        'message': "📊 The **Statistics** page shows:\n\n• Most common lost item categories\n• Top hotspot locations on campus\n• Monthly recovery trends\n• Overall recovery rate\n\nGreat for understanding campus loss patterns!",
        'quick_replies': ['View Statistics', 'Back to main menu']
    },
    'fallback': {
        'message': "I'm not sure I understand that. 🤔 Here are some things I can help with:\n\n• Reporting a **lost** or **found** item\n• Understanding how **AI matching** works\n• How to **claim** an item\n• **Points** and leaderboard\n• **Campus map** and statistics\n\nWhat would you like to know?",
        'quick_replies': ['I lost something', 'I found something', 'Check my matches', 'Back to main menu']
    }
}

QUICK_REPLY_ROUTES = {
    'Go to Report Lost': '/report-lost',
    'Go to Report Found': '/report-found',
    'View my matches': '/notifications',
    'Go to Profile': '/profile',
    'Go to Browse': '/browse-lost',
    'View Leaderboard': '/leaderboard',
    'Go to Campus Map': '/map',
    'View Statistics': '/statistics',
    'Back to main menu': None
}


def _detect_intent(message: str) -> str:
    """Detect intent from user message via keyword matching."""
    msg = message.lower().strip()

    if any(g in msg for g in GREETINGS) and len(msg.split()) <= 3:
        return 'greeting'
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
    if 'main menu' in msg or 'back' in msg or 'start over' in msg:
        return 'greeting'
    return 'fallback'


@chatbot_bp.route('/message', methods=['POST'])
@jwt_required()
def chatbot_message():
    """
    Process a chatbot message and return a response.
    Expects: { "message": "..." }
    Returns: { "message": "...", "quick_replies": [...], "redirect_url": "..." }
    """
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'success': False, 'message': 'message field is required'}), 400

    user_message = str(data.get('message', '')).strip()

    if not user_message:
        intent = 'greeting'
    else:
        intent = _detect_intent(user_message)

    response = RESPONSES.get(intent, RESPONSES['fallback'])

    # Check if this quick reply has a redirect
    redirect_url = None
    if user_message in QUICK_REPLY_ROUTES:
        redirect_url = QUICK_REPLY_ROUTES[user_message]

    return jsonify({
        'success': True,
        'data': {
            'message': response['message'],
            'quick_replies': response.get('quick_replies', []),
            'intent': intent,
            'redirect_url': redirect_url
        }
    }), 200
