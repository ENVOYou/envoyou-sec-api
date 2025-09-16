#!/usr/bin/env python3
"""
Background Task Processor Runner
Run this script to start the Redis-based background task processor
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

if __name__ == "__main__":
    from app.services.task_processor import task_processor
    task_processor.start()