#!/usr/bin/env python
import sys
import os

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from app import create_app

# Load environment variables
load_dotenv()

# Create the Flask app
app = create_app()

# This is required for Vercel
if __name__ == "__main__":
    app.run()