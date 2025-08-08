#!/usr/bin/env python
from dotenv import load_dotenv
import os
from app import create_app

# Load environment variables
# Prefer .env.development.local for local runs if present (e.g., Upstash creds)
if os.path.exists(".env.development.local"):
    load_dotenv(".env.development.local", override=True)
else:
    load_dotenv()

if __name__ == "__main__":
    app = create_app()
    # Changed port to 5001 to avoid conflict with AirPlay
    app.run(host="0.0.0.0", port=5001, debug=True)
