import os
import re
import requests

# Define paths
WORKSPACE_DIR = r"c:\Users\harsh\OneDrive\Desktop\find it cam\final year project\final year project\findit-campus\backend"
STATIC_DIR = os.path.join(WORKSPACE_DIR, "app", "static")
JS_DIR = os.path.join(STATIC_DIR, "js")
CSS_DIR = os.path.join(STATIC_DIR, "css")
FONTS_DIR = os.path.join(STATIC_DIR, "fonts")
LEAFLET_IMAGES_DIR = os.path.join(CSS_DIR, "images")

# Create directories if they don't exist
for d in [JS_DIR, CSS_DIR, FONTS_DIR, LEAFLET_IMAGES_DIR]:
    os.makedirs(d, exist_ok=True)

# List of simple files to download
assets = {
    # Tailwind CSS Development CDN Script
    "https://cdn.tailwindcss.com": os.path.join(JS_DIR, "tailwind.js"),
    
    # Lucide Icons
    "https://unpkg.com/lucide@latest": os.path.join(JS_DIR, "lucide.min.js"),
    
    # Chart.js
    "https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js": os.path.join(JS_DIR, "chart.umd.min.js"),
    
    # QRCode JS
    "https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js": os.path.join(JS_DIR, "qrcode.min.js"),
    
    # Leaflet Map
    "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js": os.path.join(JS_DIR, "leaflet.js"),
    "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css": os.path.join(CSS_DIR, "leaflet.css"),
    
    # FullCalendar
    "https://cdn.jsdelivr.net/npm/fullcalendar@6.1.10/index.global.min.js": os.path.join(JS_DIR, "fullcalendar.min.js"),
    "https://cdn.jsdelivr.net/npm/fullcalendar@6.1.10/index.global.min.css": os.path.join(CSS_DIR, "fullcalendar.min.css"),
}

# Leaflet images
leaflet_images = [
    "layers.png",
    "layers-2x.png",
    "marker-icon.png",
    "marker-icon-2x.png",
    "marker-shadow.png"
]
for img in leaflet_images:
    url = f"https://unpkg.com/leaflet@1.9.4/dist/images/{img}"
    assets[url] = os.path.join(LEAFLET_IMAGES_DIR, img)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def download_file(url, dest):
    print(f"Downloading {url} -> {dest}...")
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        with open(dest, 'wb') as f:
            f.write(response.content)
        print("Success.")
    except Exception as e:
        print(f"Failed to download {url}: {e}")

# Download basic assets
for url, dest in assets.items():
    download_file(url, dest)

# Download and patch Inter font
google_font_url = "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"
try:
    print(f"Downloading google font CSS from {google_font_url}...")
    r = requests.get(google_font_url, headers=headers, timeout=20)
    r.raise_for_status()
    css_content = r.text
    
    # Find all url(...) patterns in CSS
    font_urls = re.findall(r'url\((https://[^)]+)\)', css_content)
    
    # Track mapping of remote url to local filename
    url_to_local = {}
    for f_url in set(font_urls):
        # Extract filename (e.g. UcC7_cDrrdyYSJjcuJHlhTyc7wM.woff2)
        font_filename = f_url.split('/')[-1]
        local_path = os.path.join(FONTS_DIR, font_filename)
        download_file(f_url, local_path)
        # In the new CSS file, we reference the fonts relative to /static/css (so ../fonts/filename)
        url_to_local[f_url] = f"../fonts/{font_filename}"
    
    # Replace remote URLs in CSS content with local relative paths
    for remote_url, local_ref in url_to_local.items():
        css_content = css_content.replace(remote_url, local_ref)
        
    # Save the local CSS stylesheet
    inter_css_path = os.path.join(CSS_DIR, "inter.css")
    with open(inter_css_path, "w", encoding="utf-8") as f:
        f.write(css_content)
    print(f"Successfully created local inter.css at {inter_css_path}")
    
except Exception as e:
    print(f"Error processing Google Fonts: {e}")
