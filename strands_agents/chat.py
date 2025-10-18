#!/usr/bin/env python3
"""
Quick Chat Launcher

Simple launcher for the chat interface.
Just run: python chat.py
"""

import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from llm_interface.chat import main

if __name__ == "__main__":
    main()
