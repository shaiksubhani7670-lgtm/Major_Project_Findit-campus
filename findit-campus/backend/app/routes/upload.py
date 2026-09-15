import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required

upload_bp = Blueprint('upload', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_IMAGES = 5

# Auto-category keyword heuristics
CATEGORY_KEYWORDS = {
    'Laptop': ['laptop', 'notebook', 'computer', 'dell', 'hp', 'lenovo', 'asus', 'macbook', 'thinkpad'],
    'Mobile': ['phone', 'mobile', 'iphone', 'samsung', 'redmi', 'oneplus', 'realme', 'oppo', 'vivo', 'pixel'],
    'Bag': ['bag', 'backpack', 'satchel', 'purse', 'handbag', 'rucksack', 'pouch'],
    'Wallet': ['wallet', 'purse', 'card holder', 'money clip'],
    'Keys': ['key', 'keys', 'keychain', 'keyring', 'lock'],
    'Earphones': ['earphone', 'headphone', 'earbud', 'airpod', 'headset', 'earpiece'],
    'Glasses': ['glass', 'glasses', 'spectacle', 'spects', 'lens', 'sunglasses'],
    'Watch': ['watch', 'smartwatch', 'fitbit', 'wristwatch'],
    'ID Card': ['id card', 'identity', 'student id', 'college card', 'library card'],
    'Book': ['book', 'notebook', 'notes', 'textbook', 'register'],
    'Charger': ['charger', 'adapter', 'cable', 'power bank', 'powerbank'],
    'Umbrella': ['umbrella', 'raincoat'],
    'Water Bottle': ['water bottle', 'bottle', 'flask', 'thermos'],
    'Pen / Stationery': ['pen', 'pencil', 'stationery', 'ruler', 'calculator'],
}

def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def _detect_category(filename: str) -> str | None:
    """Try to detect category from filename keywords."""
    name = filename.lower().replace('_', ' ').replace('-', ' ')
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in name for kw in keywords):
            return category
    return None

def _is_cloudinary_configured():
    """Check if Cloudinary credentials are available."""
    return all([
        current_app.config.get('CLOUDINARY_CLOUD_NAME'),
        current_app.config.get('CLOUDINARY_API_KEY'),
        current_app.config.get('CLOUDINARY_API_SECRET'),
    ])

def _upload_to_cloudinary(file, report_type):
    """Upload file to Cloudinary and return (url, public_id)."""
    import cloudinary
    import cloudinary.uploader
    cloudinary.config(
        cloud_name=current_app.config['CLOUDINARY_CLOUD_NAME'],
        api_key=current_app.config['CLOUDINARY_API_KEY'],
        api_secret=current_app.config['CLOUDINARY_API_SECRET'],
        secure=True
    )
    folder = f"findit_campus/{report_type}"
    result = cloudinary.uploader.upload(
        file,
        folder=folder,
        resource_type="image"
    )
    return result['secure_url'], result['public_id']

def _get_upload_dir(report_type):
    """Get or create separate directory for lost/found uploads inside static folder."""
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', report_type)
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir

def _save_file_local(file, report_type):
    """Save a single file locally, return (url, filename) or raise."""
    upload_dir = _get_upload_dir(report_type)
    ext = file.filename.rsplit('.', 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(upload_dir, unique_name)
    file.save(filepath)
    url = f"/static/uploads/{report_type}/{unique_name}"
    return url, unique_name

def _save_file(file, report_type):
    """
    Save a file — uses Cloudinary if configured (required on Vercel),
    falls back to local disk for development.
    Returns (url, identifier).
    """
    if _is_cloudinary_configured():
        url, public_id = _upload_to_cloudinary(file, report_type)
        return url, public_id
    else:
        return _save_file_local(file, report_type)


@upload_bp.route('/image', methods=['POST'])
@jwt_required()
def upload_image():
    """
    Upload a single image for lost or found items.
    Expects multi-part form with key 'image' and 'type' ('lost' or 'found').
    Returns: url, filename, suggested_category
    """
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': 'No image file provided'}), 400

    file = request.files['image']
    report_type = request.form.get('type', 'lost').strip().lower()
    if report_type not in ['lost', 'found']:
        report_type = 'lost'

    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400

    if not _allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'Invalid image format. Only jpg, jpeg, png, webp allowed.'}), 400

    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > MAX_FILE_SIZE:
        return jsonify({'success': False, 'message': 'Maximum image size is 5 MB'}), 400

    try:
        url, unique_name = _save_file(file, report_type)
        suggested_category = _detect_category(file.filename)
        return jsonify({
            'success': True,
            'message': 'Image uploaded successfully',
            'data': {
                'url': url,
                'filename': unique_name,
                'suggested_category': suggested_category
            }
        }), 201
    except Exception as e:
        return jsonify({'success': False, 'message': f'Upload failed: {str(e)}'}), 500


@upload_bp.route('/images', methods=['POST'])
@jwt_required()
def upload_multiple_images():
    """
    Upload up to 5 images at once.
    Expects multi-part form with keys 'images[]' and 'type'.
    Returns: list of urls, first url, suggested_category
    """
    files = request.files.getlist('images[]')
    if not files:
        return jsonify({'success': False, 'message': 'No image files provided'}), 400

    report_type = request.form.get('type', 'lost').strip().lower()
    if report_type not in ['lost', 'found']:
        report_type = 'lost'

    if len(files) > MAX_IMAGES:
        return jsonify({'success': False, 'message': f'Maximum {MAX_IMAGES} images allowed'}), 400

    urls = []
    suggested_category = None
    errors = []

    for file in files:
        if file.filename == '':
            continue
        if not _allowed_file(file.filename):
            errors.append(f'{file.filename}: invalid format')
            continue
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        if size > MAX_FILE_SIZE:
            errors.append(f'{file.filename}: too large (max 5MB)')
            continue
        try:
            url, _ = _save_file(file, report_type)
            urls.append(url)
            if not suggested_category:
                suggested_category = _detect_category(file.filename)
        except Exception as e:
            errors.append(f'{file.filename}: {str(e)}')

    if not urls:
        return jsonify({'success': False, 'message': 'No images were saved.', 'errors': errors}), 400

    return jsonify({
        'success': True,
        'message': f'{len(urls)} image(s) uploaded successfully',
        'data': {
            'urls': urls,
            'primary_url': urls[0],
            'suggested_category': suggested_category,
            'errors': errors
        }
    }), 201
