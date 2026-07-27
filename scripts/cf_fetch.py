"""
Fetches problem sample tests from Codeforces.
Handles HTML parsing, Cloudflare evasion, and metadata extraction.
"""
import sys
import os
import re
import json
import glob
import time
from utils import GREEN, RED, YELLOW, BLUE, RESET

def fetchTests(typeParam: str, contestId: str, problemLetter: str, _retryCount: int = 0):
    """Fetch sample tests from Codeforces problem page using Scrapling.
    Retries up to 3 times on transient network errors with a 1-second backoff."""
    _maxRetries = 2
    typeParam = typeParam.lower()
    problemLetter = problemLetter.upper()
    if typeParam == "problemset":
        url = f"https://codeforces.com/{typeParam}/problem/{contestId}/{problemLetter}"
    else:
        url = f"https://codeforces.com/{typeParam}/{contestId}/problem/{problemLetter}"

    print(f"{YELLOW}Fetching{RESET} from: {url}")
    
    try:
        from scrapling.fetchers import Fetcher
    except ImportError:
        print(f"{RED}ERROR{RESET}: Scrapling library not found.")
        print("Please install it by running: pip install \"scrapling[all]\"")
        return False
        
    try:
        print(f"{BLUE}Attempting fast fetch...{RESET}")
        page = Fetcher.get(url)
        
        # 1. Extract the clean, visible text (ignores HTML tags/scripts)
        pageText = getattr(page, 'text', "")
        
        # 2. Extract the page Title securely using standard .css()
        titleNodes = page.css("title")
        title = titleNodes[0].text if titleNodes else ""
        
        # Check if fast fetch was blocked by Cloudflare
        isBlocked = ("Just a moment" in title or 
                      "cf-browser-verification" in pageText or 
                      getattr(page, 'status', 200) in (403, 503))
                      
        if isBlocked:
            isWindows = sys.platform == "win32"
            strategy = "StealthyFetcher (Windows)" if isWindows else "curl_cffi (Linux)"
            print(f"{YELLOW}Fast fetch blocked. Retrying with {strategy}...{RESET}")

            try:
                if isWindows:
                    from scrapling.fetchers import StealthyFetcher
                    page = StealthyFetcher.fetch(url, headless=True)
                else:
                    from curl_cffi import requests
                    from scrapling.parser import Selector
                    page = Selector(requests.get(url, impersonate="chrome").text)

                pageText = getattr(page, "text", "")
                title = next((n.text for n in page.css("title")), "")

            except ImportError as e:
                hint = (
                    "Ensure playwright/patchright is installed."
                    if isWindows
                    else "Please run: pip install curl_cffi."
                )
                print(f"{RED}ERROR{RESET}: {hint} Exact error: {e}")
                return False
            
        # Check title and visible text (Soft 404s)
        if "Error" in title or "No such problem" in pageText or "Problem not found" in pageText:
            print(f"{RED}ERROR{RESET}: Problem {contestId}{problemLetter} not found!")
            return False
            
        elif "Contest not found" in pageText:
            print(f"{RED}ERROR{RESET}: Contest {contestId} not found or not public!")
            return False 
             
        # Cloudflare might still show a challenge page even after StealthyFetcher
        elif "Just a moment" in title or "cf-browser-verification" in pageText:
            print(f"{RED}ERROR{RESET}: Blocked by Cloudflare challenge page!")
            return False
            
        elif not page.css(".sample-test") and not page.css(".input"):
            print(f"{RED}ERROR{RESET}: Problem {contestId}{problemLetter} found but has no sample tests!")
            print("This might be an output-only or interactive problem")
            return False
            
    except Exception as e:
        errorMsg = str(e).lower()
        if "playwright" in errorMsg or "executable doesn't exist" in errorMsg or "chromium" in errorMsg:
            print(f"\n{YELLOW}Environment Hint:{RESET} If you are running this on a headless Linux server, WSL, or Docker,")
            print("you likely need to install system dependencies for the headless browser.")
            print(f"Run this command to fix it: {GREEN}npx playwright install chromium --with-deps{RESET}\n")

        # Retry on transient network errors
        if _retryCount < _maxRetries:
            waitSecs = _retryCount + 1
            print(f"{YELLOW}Network error ({e}). Retrying in {waitSecs}s... ({_retryCount + 1}/{_maxRetries}){RESET}")
            time.sleep(waitSecs)
            return fetchTests(typeParam, contestId, problemLetter, _retryCount + 1)

        print(f"{RED}ERROR{RESET}: Unexpected error while fetching: {e}")
        return False

    try:
        # 1. Grab the <pre> blocks inside the input/output divs directly using CSS
        inputNodes = page.css(".input pre")
        outputNodes = page.css(".output pre")
        
        # Helper to safely clean Codeforces <pre> blocks
        def extractTestText(node) -> str:
            # Get the raw HTML of just this small <pre> block
            rawHtml = node.html_content
            
            # Codeforces sometimes uses <br> or <div class="test-example-line"> for newlines inside <pre>
            text = re.sub(r'<br\s*/?>', '\n', rawHtml, flags=re.IGNORECASE)
            text = re.sub(r'</div>', '\n', text, flags=re.IGNORECASE)
            text = re.sub(r'<[^>]+>', '', text) # Strip remaining tags
            
            # Scrapling usually handles entities, but just to be safe:
            text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
            text = text.replace('&quot;', '"').replace('&#39;', "'").replace('&nbsp;', ' ')
            
            return text.strip()

        inputs = [extractTestText(node) for node in inputNodes]
        outputs = [extractTestText(node) for node in outputNodes]
        
        timeLimit = "Unknown"
        rawPageHtml = getattr(page, "html_content", getattr(page, "html", str(page)))        
        timeMatch = re.search(r'<div class="time-limit"[^>]*>.*?(\d+(?:\.\d+)?)\s*second', rawPageHtml, re.DOTALL | re.IGNORECASE)
        if timeMatch:
            timeLimit = timeMatch.group(1)
        
        if not inputs or not outputs:
            print(f"{RED}ERROR{RESET}: No sample tests found!")
            print("This could mean:")
            print("  - Wrong contest ID or problem letter")
            print("  - Problem doesn't have sample tests")
            print("  - Codeforces changed their HTML structure")
            
            # Save debug HTML to debug/ subdirectory to avoid polluting project root
            debugDir = "debug"
            os.makedirs(debugDir, exist_ok=True)
            debugPath = os.path.join(debugDir, f"debug_{contestId}_{problemLetter}.html")
            with open(debugPath, "w", encoding="utf-8") as f:
                f.write(getattr(page, 'html_content', getattr(page, 'html', str(page))))
            print(f"  - HTML saved to {debugPath} for inspection")
            return False
            
        if len(inputs) != len(outputs):
            print(f"{YELLOW}Warning{RESET}: Found {len(inputs)} inputs but {len(outputs)} outputs")
            minCount = min(len(inputs), len(outputs))
            inputs = inputs[:minCount]
            outputs = outputs[:minCount]

        os.makedirs("tests", exist_ok=True)
        
        # Delete ghost tests
        for oldFile in glob.glob(f"tests/{problemLetter}*.in") + glob.glob(f"tests/{problemLetter}*.out"):
            try:
                os.remove(oldFile)
            except OSError:
                pass
        
        for i, (inp, out) in enumerate(zip(inputs, outputs), 1):
            inputFile = f"tests/{problemLetter}{i}.in"
            outputFile = f"tests/{problemLetter}{i}.out"
            
            with open(inputFile, "w", encoding="utf-8") as f:
                f.write(inp.rstrip() + "\n")
                
            with open(outputFile, "w", encoding="utf-8") as f:
                f.write(out.rstrip() + "\n")
        metadataFile = f"tests/{problemLetter}_metadata.json"
        metadata = {
            "contestId": contestId,
            "problemLetter": problemLetter,
            "timeLimit": timeLimit,
            "testCount": len(inputs)
        }
        with open(metadataFile, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        
        print(f"{GREEN}Downloaded{RESET} {len(inputs)} sample tests for {typeParam} {contestId} problem {problemLetter}")
        print(f"   Time limit: {timeLimit}")
        
        for i in range(1, len(inputs) + 1):
            print(f"   {problemLetter}{i}.in, {problemLetter}{i}.out")
        print(f"   {problemLetter}_metadata.json")
            
        return True
        
    except Exception as e:
        print(f"{RED}ERROR{RESET}: Error parsing HTML: {e}")
        return False

def main():
    if len(sys.argv) != 4:
        print("Usage: python cf_fetch.py <type> <contestId> <problemLetter>")
        print("Example: python cf_fetch.py contest 2139 B")
        sys.exit(1)
        
    typeParam = sys.argv[1].strip()
    contestId = sys.argv[2].strip()
    problemLetter = sys.argv[3].strip().upper()
    
    if not contestId.isdigit():
        print(f"{RED}ERROR{RESET}: INVALID ID: Contest ID must be a number")
        sys.exit(1)
        
    if len(problemLetter) > 4 or not problemLetter.isalnum():
        print(f"{RED}ERROR{RESET}: INVALID PROBLEM LETTER: Problem letter must be alphanumeric (1-4 chars like A, B, A1, J2)")
        sys.exit(1)
    
    success = fetchTests(typeParam, contestId, problemLetter)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()