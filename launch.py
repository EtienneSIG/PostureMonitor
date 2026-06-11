#!/usr/bin/env python3
"""
Posture Monitor Pro - Unified Launcher

Starts both backend (FastAPI) and frontend (Vue 3 + Vite) servers.

Usage:
    python launch.py                    # Start both servers
    python launch.py --backend-only    # Start backend only
    python launch.py --frontend-only   # Start frontend only
    python launch.py --help            # Show help

The app will be available at http://localhost:5173 (frontend)
Backend API available at http://127.0.0.1:8000 (local-only for privacy)
"""

import subprocess
import sys
import time
from pathlib import Path
import signal
import threading

# Directories
ROOT_DIR = Path(__file__).parent
FRONTEND_DIR = ROOT_DIR / "frontend"

# Process references
backend_process = None
frontend_process = None


def start_backend():
    """Start FastAPI backend server."""
    global backend_process
    
    print("\n" + "="*60)
    print("🚀 Starting Backend (FastAPI)")
    print("="*60)
    print("Backend URL: http://127.0.0.1:8000")
    print("Docs: http://127.0.0.1:8000/docs")
    print()
    
    try:
        backend_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.app:app", 
             "--host", "127.0.0.1", "--port", "8000", "--reload"],
            cwd=ROOT_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Stream output
        def read_output(pipe, label):
            for line in pipe:
                print(f"[{label}] {line}", end='')
        
        threading.Thread(target=read_output, args=(backend_process.stdout, "Backend"), daemon=True).start()
        threading.Thread(target=read_output, args=(backend_process.stderr, "Backend"), daemon=True).start()
        
        print("✓ Backend started successfully")
        return True
    except Exception as e:
        print(f"✗ Error starting backend: {e}")
        return False


def start_frontend():
    """Start Vue 3 + Vite dev server."""
    global frontend_process
    
    print("\n" + "="*60)
    print("🎨 Starting Frontend (Vue 3 + Vite)")
    print("="*60)
    print("Frontend URL: http://localhost:5173")
    print()
    
    # Check if node_modules exists
    if not (FRONTEND_DIR / "node_modules").exists():
        print("📦 Installing dependencies (first run)...")
        install_deps = subprocess.Popen(
            ["npm", "install"],
            cwd=FRONTEND_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        install_deps.wait()
        print("✓ Dependencies installed")
    
    try:
        frontend_process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=FRONTEND_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Stream output
        def read_output(pipe, label):
            for line in pipe:
                print(f"[{label}] {line}", end='')
        
        threading.Thread(target=read_output, args=(frontend_process.stdout, "Frontend"), daemon=True).start()
        threading.Thread(target=read_output, args=(frontend_process.stderr, "Frontend"), daemon=True).start()
        
        print("✓ Frontend started successfully")
        return True
    except Exception as e:
        print(f"✗ Error starting frontend: {e}")
        return False


def cleanup(signum=None, frame=None):
    """Clean shutdown of both processes."""
    global backend_process, frontend_process
    
    print("\n" + "="*60)
    print("🛑 Shutting down Posture Monitor Pro...")
    print("="*60)
    
    if backend_process:
        print("Stopping backend...")
        backend_process.terminate()
        try:
            backend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend_process.kill()
    
    if frontend_process:
        print("Stopping frontend...")
        frontend_process.terminate()
        try:
            frontend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            frontend_process.kill()
    
    print("✓ Shutdown complete")
    sys.exit(0)


def main():
    """Main launcher."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Posture Monitor Pro - Unified Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python launch.py                    # Start both backend and frontend
  python launch.py --backend-only    # Start backend only (for API testing)
  python launch.py --frontend-only   # Start frontend only (requires backend running)
        """
    )
    
    parser.add_argument(
        "--backend-only", 
        action="store_true", 
        help="Start only backend server"
    )
    parser.add_argument(
        "--frontend-only", 
        action="store_true", 
        help="Start only frontend server"
    )
    
    args = parser.parse_args()
    
    # Signal handlers
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    print("\n" + "="*60)
    print("🧍 Posture Monitor Pro v2.0.0")
    print("Modern | Compliant | Local-First")
    print("="*60)
    
    if args.backend_only:
        start_backend()
    elif args.frontend_only:
        start_frontend()
    else:
        # Start both
        backend_ok = start_backend()
        time.sleep(2)  # Wait for backend to start
        frontend_ok = start_frontend()
        
        if backend_ok and frontend_ok:
            print("\n" + "="*60)
            print("✓ Posture Monitor Pro is running!")
            print("="*60)
            print("\n🌐 Open your browser: http://localhost:5173")
            print("\n📚 API Documentation: http://127.0.0.1:8000/docs")
            print("Press Ctrl+C to stop\n")
            
            # Keep running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                cleanup()
        else:
            print("\n✗ Failed to start all services")
            cleanup()
            sys.exit(1)


if __name__ == "__main__":
    main()
