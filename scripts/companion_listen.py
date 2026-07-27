"""
Listens for JSON payloads from the Competitive Companion browser extension.
Extracts problem data, sets time limits, and creates test files.
"""
import http.server
import socketserver
import itertools
import json
import os
import glob
import sys
import re
import time
from utils import GREEN, RED, YELLOW, BLUE, RESET

PORT = 10043

class CompanionHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        contentLength = int(self.headers["Content-Length"])
        postData = self.rfile.read(contentLength)
        
        # Respond immediately to extension
        self.send_response(200)
        self.end_headers()

        try:
            data = json.loads(postData)
        except json.JSONDecodeError as e:
            print(f"{RED}ERROR{RESET}: Invalid JSON payload received: {e}")
            return
        
        self.processProblem(data)
        
    def processProblem(self, data):
        print(f"\n{YELLOW}Received problem data from Competitive Companion!{RESET}")
        
        # Extract time limit (Competitive Companion sends ms, we need seconds)
        timeLimitMs = data.get('timeLimit', 'Unknown')
        if isinstance(timeLimitMs, (int, float)):
            timeLimit = timeLimitMs / 1000.0  # store as float for clean JSON
        else:
            timeLimit = 'Unknown'
        
        problemLetter = None
        url = data.get('url', '')
        
        # Codeforces style URLs
        if 'codeforces.com' in url:
            match = re.search(r'/problem/([A-Z0-9]+)$', url, re.IGNORECASE)
            if match:
                raw = match.group(1).upper()
                # Validate: 1-4 alphanumeric chars only
                if raw.isalnum() and 1 <= len(raw) <= 4:
                    problemLetter = raw
        
        if not problemLetter:
            fallback = f"UNKNOWN_{int(time.time())}"
            print(f"{YELLOW}Could not determine problem letter from URL: {url}{RESET}")
            print(f"{YELLOW}Using auto-generated name: {fallback}{RESET}")
            problemLetter = fallback
            
        print(f"Problem Letter: {problemLetter}")
        print(f"Time Limit: {timeLimit}")
        
        os.makedirs("tests", exist_ok=True)
        
        # Delete ghost tests
        for oldFile in itertools.chain(glob.glob(f"tests/{problemLetter}*.in"), glob.glob(f"tests/{problemLetter}*.out")):
            try:
                os.remove(oldFile)
            except OSError:
                pass
                
        tests = data.get('tests', [])
        testCount = len(tests)
        print(f"Writing {testCount} tests...")
        
        for i, test in enumerate(tests, 1):
            inputFile = f"tests/{problemLetter}{i}.in"
            outputFile = f"tests/{problemLetter}{i}.out"
            
            with open(inputFile, "w", encoding="utf-8") as f:
                f.write(test.get('input', '').rstrip() + "\n")
                
            with open(outputFile, "w", encoding="utf-8") as f:
                f.write(test.get('output', '').rstrip() + "\n")
                
        metadataFile = f"tests/{problemLetter}_metadata.json"
        metadata = {
            "contestId": data.get('group', 'Unknown'),
            "problemLetter": problemLetter,
            "timeLimit": timeLimit,
            "testCount": testCount,
            "url": url
        }
        with open(metadataFile, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
            
        print(f"{GREEN}Successfully saved {testCount} tests for {problemLetter}!{RESET}")
        print("Ready for testing.\n")

    def log_message(self, format, *args):
        # Suppress default logging
        pass

def startServer():
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", PORT), CompanionHandler) as httpd:
            print(f"{GREEN}Listening on port {PORT} for Competitive Companion...{RESET}")
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print(f"\n{YELLOW}Shutting down listener.{RESET}")
                sys.exit(0)
    except OSError:
        print(f"{RED}ERROR{RESET}: Port {PORT} is already in use. Is another listener running?")
        sys.exit(1)

if __name__ == '__main__':
    startServer()