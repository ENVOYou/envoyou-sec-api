#!/usr/bin/env python
"""
Production startup script for the Permit API.
Optimized for AWS App Runner and other cloud platforms.
"""
import os
import sys

def setup_environment():
    """Setup environment and paths."""
    # Add the project root to Python path
    try:
        project_root = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        # Handle case when __file__ is not defined (exec context)
        project_root = os.getcwd()

    sys.path.insert(0, project_root)
    
    # Create necessary directories
    os.makedirs('data/eea/renewable-energy', exist_ok=True)
    os.makedirs('data/eea/pollution', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('reference', exist_ok=True)
    
    return project_root

def main():
    """Main application entry point."""
    project_root = setup_environment()
    
    # Import after path setup
    from app.api_server import app
    
    # Configure for production/cloud deployment
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    env = os.environ.get('FLASK_ENV', 'development')
    host = '0.0.0.0'
    
    print(f"🚀 Starting Permit API")
    print(f"   Port: {port}")
    print(f"   Environment: {env}")
    print(f"   Debug mode: {debug}")
    print(f"   Project root: {project_root}")
    print(f"   Host: {host}")
    
    # Run the FastAPI app with uvicorn
    try:
        import uvicorn
        uvicorn.run(
            "app.api_server:app",
            host=host,
            port=port,
            reload=debug,
            log_level="info" if not debug else "debug"
        )
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
