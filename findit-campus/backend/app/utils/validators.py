"""
FindIt Campus — Input Validators
Validation functions for forms, uploads, and API inputs.
"""

import re
from datetime import date
from app.models.lost_item import ItemCategory


# Valid college email pattern (customize for your college)
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
PHONE_PATTERN = re.compile(r'^\+?[1-9]\d{6,14}$')
ROLL_NUMBER_PATTERN = re.compile(r'^[A-Za-z0-9]{3,20}$')

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_IMAGE_SIZE = 16 * 1024 * 1024  # 16MB
MAX_IMAGES_PER_ITEM = 5

DEPARTMENTS = [
    'Computer Science', 'Information Technology', 'Electronics',
    'Electrical', 'Mechanical', 'Civil', 'Chemical',
    'Biotechnology', 'Mathematics', 'Physics', 'Chemistry',
    'MBA', 'MCA', 'Other',
]

BUILDINGS = [
    'Main Building', 'CSE Block', 'IT Block', 'ECE Block',
    'EEE Block', 'Mechanical Block', 'Civil Block',
    'Library', 'Auditorium', 'Cafeteria', 'Hostel A',
    'Hostel B', 'Hostel C', 'Sports Complex', 'Parking',
    'Admin Block', 'Lab Complex', 'Seminar Hall', 'Other',
]


def validate_email(email):
    """Validate email format."""
    if not email or not EMAIL_PATTERN.match(email):
        return False, 'Invalid email format'
    return True, None


def validate_password(password):
    """Validate password strength."""
    if not password or len(password) < 8:
        return False, 'Password must be at least 8 characters long'
    if not re.search(r'[A-Z]', password):
        return False, 'Password must contain at least one uppercase letter'
    if not re.search(r'[a-z]', password):
        return False, 'Password must contain at least one lowercase letter'
    if not re.search(r'\d', password):
        return False, 'Password must contain at least one number'
    return True, None


def validate_phone(phone):
    """Validate phone number format."""
    if not phone:
        return True, None  # Phone is optional
    cleaned = phone.replace(' ', '').replace('-', '')
    if not PHONE_PATTERN.match(cleaned):
        return False, 'Invalid phone number format'
    return True, None


def validate_category(category_str):
    """Validate and convert category string to enum."""
    try:
        return True, ItemCategory(category_str)
    except ValueError:
        valid = [c.value for c in ItemCategory]
        return False, f'Invalid category. Must be one of: {", ".join(valid)}'


def validate_lost_item_data(data):
    """Validate lost item report form data."""
    errors = []

    if not data.get('item_name'):
        errors.append('Item name is required')
    elif len(data['item_name']) > 200:
        errors.append('Item name must be under 200 characters')

    if not data.get('category'):
        errors.append('Category is required')
    else:
        valid, err = validate_category(data['category'])
        if not valid:
            errors.append(err)

    if not data.get('description'):
        errors.append('Description is required')
    elif len(data['description']) < 10:
        errors.append('Description must be at least 10 characters')

    if not data.get('lost_date'):
        errors.append('Lost date is required')
    else:
        try:
            lost_date = date.fromisoformat(data['lost_date'])
            if lost_date > date.today():
                errors.append('Lost date cannot be in the future')
        except ValueError:
            errors.append('Invalid date format. Use YYYY-MM-DD')

    return errors


def validate_found_item_data(data):
    """Validate found item upload form data."""
    errors = []

    if not data.get('item_name'):
        errors.append('Item name is required')

    if not data.get('category'):
        errors.append('Category is required')
    else:
        valid, err = validate_category(data['category'])
        if not valid:
            errors.append(err)

    if not data.get('description'):
        errors.append('Description is required')

    if not data.get('found_date'):
        errors.append('Found date is required')

    return errors


def validate_image_file(file):
    """Validate an uploaded image file."""
    if not file:
        return False, 'No file provided'

    filename = file.filename
    if not filename:
        return False, 'No filename provided'

    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return False, f'File type not allowed. Allowed: {", ".join(ALLOWED_IMAGE_EXTENSIONS)}'

    # Check file size by reading and resetting
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)     # Reset to beginning

    if size > MAX_IMAGE_SIZE:
        return False, f'File too large. Maximum size is {MAX_IMAGE_SIZE // (1024*1024)}MB'

    return True, None
