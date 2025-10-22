"""
Vercel entry point for the FastAPI backend
This file imports and exposes the FastAPI app from backend/api/server.py
"""

import os
import sys

# Add the project root to Python path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

# Import the FastAPI app from the backend
from backend.api.server import app

# Export the app for Vercel
handler = app
