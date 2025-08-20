#!/usr/bin/env python3
"""
Backend runner script for Coder-lite Provision System
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'fastapi', 'uvicorn', 'redis', 'pydantic'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing required packages: {', '.join(missing_packages)}")
        logger.info("Install with: pip install -r requirements.txt")
        return False
    
    return True

def check_redis():
    """Check if Redis is running"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        logger.info("✅ Redis is running")
        return True
    except Exception as e:
        logger.error(f"❌ Redis is not running: {e}")
        logger.info("Start Redis with: sudo systemctl start redis-server")
        return False

def check_coder_lite_path():
    """Check if Coder-lite paths exist"""
    coder_lite_path = os.getenv('CODER_LITE_PATH', '/opt/coder-lite')
    
    if not os.path.exists(coder_lite_path):
        logger.warning(f"⚠️  Coder-lite path does not exist: {coder_lite_path}")
        logger.info("This is fine for development/testing")
        return True
    
    required_files = [
        'docker-compose.yml',
        'Caddyfile',
        'scripts/dev-provision'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(os.path.join(coder_lite_path, file)):
            missing_files.append(file)
    
    if missing_files:
        logger.warning(f"⚠️  Missing Coder-lite files: {', '.join(missing_files)}")
        logger.info("Some features may not work without full Coder-lite setup")
    
    return True

def setup_environment():
    """Setup environment variables"""
    env_file = Path(__file__).parent / 'env.example'
    
    if env_file.exists():
        logger.info("📝 Loading environment from env.example")
        from dotenv import load_dotenv
        load_dotenv(env_file)
    else:
        logger.info("📝 Using default environment variables")

def start_backend():
    """Start the FastAPI backend"""
    logger.info("🚀 Starting Coder-lite Provision System Backend...")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Setup environment
    setup_environment()
    
    # Check Redis (optional for development)
    if os.getenv('CHECK_REDIS', 'true').lower() == 'true':
        if not check_redis():
            logger.warning("Continuing without Redis (some features disabled)")
    
    # Check Coder-lite paths
    check_coder_lite_path()
    
    # Import and run the main app
    try:
        from main import app
        import uvicorn
        
        host = os.getenv('HOST', '0.0.0.0')
        port = int(os.getenv('PORT', 8000))
        reload = os.getenv('RELOAD', 'false').lower() == 'true'
        log_level = os.getenv('LOG_LEVEL', 'info')
        
        logger.info(f"🌐 Starting server on {host}:{port}")
        logger.info(f"📊 API docs: http://{host}:{port}/docs")
        logger.info(f"❤️  Health check: http://{host}:{port}/health")
        logger.info(f"📈 Metrics: http://{host}:{port}/metrics")
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=reload,
            log_level=log_level
        )
        
    except ImportError as e:
        logger.error(f"Failed to import main app: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start backend: {e}")
        sys.exit(1)

def run_tests():
    """Run backend tests"""
    logger.info("🧪 Running backend tests...")
    
    try:
        result = subprocess.run([
            'python', '-m', 'pytest', 'tests/', '-v'
        ], cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            logger.info("✅ All tests passed!")
        else:
            logger.error("❌ Some tests failed!")
            sys.exit(result.returncode)
            
    except FileNotFoundError:
        logger.warning("⚠️  pytest not found, skipping tests")
        logger.info("Install with: pip install pytest")

def show_help():
    """Show help information"""
    print("""
🚀 Coder-lite Provision System Backend

Usage:
  python run_backend.py [command]

Commands:
  start     Start the backend server (default)
  test      Run backend tests
  help      Show this help message

Environment:
  Copy env.example to .env and configure your settings
  
Examples:
  # Start backend
  python run_backend.py start
  
  # Start with custom port
  PORT=9000 python run_backend.py start
  
  # Run tests
  python run_backend.py test
  
  # Development mode with auto-reload
  RELOAD=true python run_backend.py start
""")

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'test':
            run_tests()
        elif command == 'help':
            show_help()
        elif command == 'start':
            start_backend()
        else:
            logger.error(f"Unknown command: {command}")
            show_help()
            sys.exit(1)
    else:
        # Default: start backend
        start_backend()

if __name__ == "__main__":
    main()
