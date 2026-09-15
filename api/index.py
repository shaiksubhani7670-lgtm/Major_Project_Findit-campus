import sys
import os

# Add the Flask backend directory to Python's module search path
# so that 'from app import create_app' and 'from config import get_config' work
backend_dir = os.path.join(os.path.dirname(__file__), '..', 'findit-campus', 'backend')
sys.path.insert(0, os.path.abspath(backend_dir))

# Import the Flask app — Vercel expects a variable named 'app'
from run import app
