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

def extractProblemIdentifier(data):
    """
    Extracts a clean problem identifier (e.g., 'A', 'B1', '1068', 'Watermelon')
    using a multi-tier resolution strategy across different online judges.
    """
    url = data.get('url', '')
    name = data.get('name', '')

    # Tier 1: Domain-specific URL parsing
    if url:
        cleanUrl = url.split('?')[0].split('#')[0].rstrip('/')
        
        # Codeforces: .../problem/A or .../problem/1234/A
        if 'codeforces.com' in cleanUrl:
            lastSegment = cleanUrl.split('/')[-1].upper()
            if lastSegment.isalnum() and 1 <= len(lastSegment) <= 4:
                return lastSegment

        # AtCoder: .../tasks/abc300_a -> A
        if 'atcoder.jp' in cleanUrl:
            lastSegment = cleanUrl.split('/')[-1]
            if '_' in lastSegment:
                letter = lastSegment.split('_')[-1].upper()
                if letter.isalnum() and 1 <= len(letter) <= 4:
                    return letter

        # CodeChef: .../problems/FLOW001 -> FLOW001
        if 'codechef.com' in cleanUrl:
            lastSegment = cleanUrl.split('/')[-1].upper()
            if lastSegment.isalnum() and 1 <= len(lastSegment) <= 8:
                return lastSegment

        # CSES: .../task/1068 -> 1068
        if 'cses.fi' in cleanUrl:
            lastSegment = cleanUrl.split('/')[-1].upper()
            if lastSegment.isalnum() and 1 <= len(lastSegment) <= 8:
                return lastSegment

    # Tier 2: Flexible problem name parsing
    if name:
        patterns = [
            r'^(?:problem|task)?\s*([A-Z0-9]{1,4})\s*[\.\:\-\]\s]',  # "A. ", "Task A:", "A - "
            r'^\[([A-Z0-9]{1,4})\]',                                   # "[A]"
            r'^([A-Z0-9]{1,4})\.'                                      # "A.Watermelon"
        ]
        for pattern in patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                identifier = match.group(1).upper()
                if identifier.isalnum() and 1 <= len(identifier) <= 4:
                    return identifier

    # Tier 3: Slugify problem name if available
    if name:
        cleanedName = re.sub(r'[^a-zA-Z0-9]', '', name)
        if cleanedName:
            return cleanedName[:15]

    # Tier 4: Timestamp fallback
    return f"UNKNOWN_{int(time.time())}"

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
        
        url = data.get('url', '')
        # Extract time limit (Competitive Companion sends ms, we need seconds)
        timeLimitMs = data.get('timeLimit', 'Unknown')
        if isinstance(timeLimitMs, (int, float)):
            timeLimit = timeLimitMs / 1000.0  # store as float for clean JSON
        else:
            timeLimit = 'Unknown'
        
        problemLetter = extractProblemIdentifier(data)
            
        print(f"Problem Letter: {problemLetter}")
        print(f"Time Limit: {timeLimit}")
        
        os.makedirs("tests", exist_ok=True)
        
        # Remove existing test files for this problem to prevent stale data
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
        # Override BaseHTTPRequestHandler's stderr logging to keep output clean
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