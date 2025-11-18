#!/usr/bin/env python3
"""
Simple HTTP Server to serve local files and avoid CORS issues
Run this script in your project directory, then open cuaca.html in your browser
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

# Configuration
PORT = 80

DIRECTORY = os.getcwd()

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers to allow cross-origin requests
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        # Handle preflight requests
        self.send_response(200)
        self.end_headers()

def main():
    # Change to the project directory
    os.chdir(DIRECTORY)
    
    # Create server
    with socketserver.TCPServer(("", PORT), CORSHTTPRequestHandler) as httpd:
        print(f"🚀 Server started at http://localhost:{PORT}")
        print(f"📁 Serving files from: {DIRECTORY}")
        print(f"🌐 Open your browser and go to: http://localhost:{PORT}")
        print(f"⏹️  Press Ctrl+C to stop the server")
        print("-" * 50)
        
        # Try to open the browser automatically
        try:
            webbrowser.open(f'http://localhost:{PORT}')
        except:
            print("Could not open browser automatically. Please open manually.")
        
        # Start serving
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")
            httpd.shutdown()

if __name__ == "__main__":
    main() 