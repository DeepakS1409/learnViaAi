import sys
import os

# Ensure UTF-8 console output on Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '127.0.0.1')
    debug = os.getenv('FLASK_DEBUG', '1') == '1'

    print("=================================================================")
    print("✦ PADIKA AI — College-Wide AI Learning Platform")
    print(f"✦ Server active at: http://{host}:{port}")
    print("✦ UI Design: Pure Glassmorphism (Purple, Violet & Blue Ambient)")
    print("✦ Core AI: Grounded Multilingual RAG (English, Tamil, Tanglish)")
    print("=================================================================")
    
    app.run(host=host, port=port, debug=debug)

