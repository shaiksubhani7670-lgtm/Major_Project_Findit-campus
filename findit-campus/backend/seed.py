import sys
import os

# Ensure the backend directory is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.seed import seed_data

if __name__ == '__main__':
    seed_data()
