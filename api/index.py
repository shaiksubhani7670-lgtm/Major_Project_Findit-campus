import sys
import os

# Add the Flask backend directory to Python's module search path
backend_dir = os.path.join(os.path.dirname(__file__), '..', 'findit-campus', 'backend')
campus_dir = os.path.join(os.path.dirname(__file__), '..', 'findit-campus')
sys.path.insert(0, os.path.abspath(campus_dir))
sys.path.insert(0, os.path.abspath(backend_dir))

# Import the Flask app — Vercel expects a variable named 'app'
from run import app
