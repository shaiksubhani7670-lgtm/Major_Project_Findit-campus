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

import io
from PIL import Image
from flask import send_from_directory, Response

def _get_upload_dir(report_type):
    """Get or create separate directory for lost/found uploads inside static folder."""
    # On Vercel or serverless (where /var/task is read-only), ALWAYS use /tmp/uploads
    if os.getenv('VERCEL') or (os.path.exists('/tmp') and not os.access(current_app.root_path, os.W_OK)):
        tmp_dir = os.path.join('/tmp', 'uploads', report_type)
        os.makedirs(tmp_dir, exist_ok=True)
        return tmp_dir

    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', report_type)
    try:
        os.makedirs(upload_dir, exist_ok=True)
        test_file = os.path.join(upload_dir, '.write_test')
        with open(test_file, 'w') as f:
            f.write('1')
        os.remove(test_file)
        return upload_dir
    except (OSError, PermissionError):
        tmp_dir = os.path.join('/tmp', 'uploads', report_type)
        os.makedirs(tmp_dir, exist_ok=True)
        return tmp_dir

def _save_file_local(file, report_type):
    """Save a single file locally and to database for serverless persistence."""
    upload_dir = _get_upload_dir(report_type)
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(upload_dir, unique_name)
    
    file_bytes = file.read()
    file.seek(0)
    
    # Optimize image using Pillow to keep size compact
    content_type = 'image/jpeg' if ext in ['jpg', 'jpeg'] else f'image/{ext}'
    image_bytes = file_bytes
    try:
        with Image.open(io.BytesIO(file_bytes)) as pil_img:
            pil_img = pil_img.convert('RGB')
            pil_img.thumbnail((800, 800), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            pil_img.save(buf, format='JPEG', quality=85)
            image_bytes = buf.getvalue()
            content_type = 'image/jpeg'
    except Exception as opt_err:
        print(f"[Upload] Optimization notice: {opt_err}")

    # 1. Save to database (persists across all Vercel instances)
    try:
        from app import db
        from app.models.uploaded_image import UploadedImage
        db_img = UploadedImage(
            filename=unique_name,
            report_type=report_type,
            content_type=content_type,
            image_data=image_bytes
        )
        db.session.merge(db_img)
        db.session.commit()
    except Exception as db_err:
        print(f"[Upload] DB image save error: {db_err}")

    # 2. Also save to disk/tmp if writable
    try:
        with open(filepath, 'wb') as f:
            f.write(image_bytes)
    except (OSError, PermissionError):
        try:
            tmp_dir = os.path.join('/tmp', 'uploads', report_type)
            os.makedirs(tmp_dir, exist_ok=True)
            with open(os.path.join(tmp_dir, unique_name), 'wb') as f:
                f.write(image_bytes)
        except Exception:
            pass

    url = f"/static/uploads/{report_type}/{unique_name}"
    return url, unique_name

def serve_uploaded_file_by_path(path):
    """Serve an uploaded file from disk or database fallback."""
    # Check static uploads folder
    static_base = os.path.join(current_app.root_path, 'static', 'uploads')
    disk_path = os.path.join(static_base, path)
    if os.path.exists(disk_path) and os.path.isfile(disk_path):
        return send_from_directory(static_base, path)

    # Check /tmp/uploads
    tmp_path = os.path.join('/tmp', 'uploads', path)
    if os.path.exists(tmp_path) and os.path.isfile(tmp_path):
        return send_from_directory(os.path.dirname(tmp_path), os.path.basename(tmp_path))

    # Query from database table
    filename = os.path.basename(path)
    try:
        from app.models.uploaded_image import UploadedImage
        img = UploadedImage.query.get(filename)
        if img and img.image_data:
            raw_data = bytes(img.image_data)
            resp = Response(raw_data, mimetype=img.content_type or 'image/jpeg')
            resp.headers['Cache-Control'] = 'public, max-age=86400'
            return resp
    except Exception as db_err:
        print(f"[Upload] DB image fetch error for {filename}: {db_err}")

    return jsonify({'error': 'Image not found'}), 404

@upload_bp.route('/file/<path:filename>')
def serve_tmp_file(filename):
    return serve_uploaded_file_by_path(filename)

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
