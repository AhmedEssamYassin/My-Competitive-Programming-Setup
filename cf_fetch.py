import urllib.request
import urllib.error
import sys
import os
import re
import json

# ANSI color codes (work in Windows Terminal, Git Bash, but not old cmd)
try:
    # Enable ANSI colors on Windows 10+
    os.system('')
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    RESET = '\033[0m'
except:
    GREEN = RED = YELLOW = BLUE =  RESET = ''

def fetchTests(typeParam:str, contestId: str, problemLetter: str):
    """Fetch sample tests from Codeforces problem page using only built-in modules."""
    typeParam = typeParam.lower()
    problemLetter = problemLetter.upper()
    if(typeParam == "problemset"):
        url = f"https://codeforces.com/{typeParam}/problem/{contestId}/{problemLetter}"
    else:
        url = f"https://codeforces.com/{typeParam}/{contestId}/problem/{problemLetter}"

    print(f"{YELLOW}Fetching{RESET} from: {url}")
    
    try:
        # Create request with headers
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7')
        req.add_header('Accept-Language', 'en-US,en;q=0.9')
        req.add_header('Connection', 'keep-alive')
        req.add_header('Upgrade-Insecure-Requests', '1')
        req.add_header('Sec-Fetch-Dest', 'document')
        req.add_header('Sec-Fetch-Mode', 'navigate')
        req.add_header('Sec-Fetch-Site', 'none')
        req.add_header('Sec-Fetch-User', '?1')
        req.add_header('Cache-Control', 'max-age=0')
        req.add_header('DNT', '1')
        req.add_header('Referer', 'https://codeforces.com/')
        
        # Create SSL context that doesn't verify certificates (for problematic systems)
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
            html = response.read().decode('utf-8')
            
        # Error detection
        if "404" in html or "Problem not found" in html:
            print(f"{RED}ERROR{RESET}: Problem {contestId}{problemLetter} not found!")
            return False
        elif "Contest not found" in html:
            print(f"{RED}ERROR{RESET}: Contest {contestId} not found or not public!")
            print("Try: gym contest, check contest ID, or wait if contest is running")
            return False  
        elif not re.search(r'<div class="(input|sample-test)"', html):
            print(f"{RED}ERROR{RESET}: Problem {contestId}{problemLetter} found but has no sample tests!")
            print("This might be an output-only or interactive problem")
            return False
            
    except urllib.error.HTTPError as e:
        print(f"{RED}ERROR{RESET}: HTTP error {e.code}: {e.reason}")
        return False
    except urllib.error.URLError as e:
        print(f"{RED}ERROR{RESET}: Connection error: {e.reason}")
        return False
    except Exception as e:
        print(f"{RED}ERROR{RESET}: Unexpected error: {e}")
        return False

    try:
        # Extract sample inputs and outputs using regex
        # Look for sample test blocks
        inputPattern = r'<div class="input">.*?<pre[^>]*>(.*?)</pre>'
        outputPattern = r'<div class="output">.*?<pre[^>]*>(.*?)</pre>'
        timePattern = r'<div class="time-limit"[^>]*>.*?(\d+(?:\.\d+)?\s*seconds?)'
        # Alternative patterns for different layouts
        altInputPattern = r'<div class="sample-test">.*?<div class="input">.*?<pre[^>]*>(.*?)</pre>'
        altOutputPattern = r'<div class="sample-test">.*?<div class="output">.*?<pre[^>]*>(.*?)</pre>'
        
        inputs = []
        outputs = []
        
        # Try main pattern first
        inputs = re.findall(inputPattern, html, re.DOTALL)
        outputs = re.findall(outputPattern, html, re.DOTALL)
        timeLimit = re.findall(timePattern,html,re.DOTALL)
        # If that didn't work, try alternative pattern
        if not inputs or not outputs:
            inputs = re.findall(altInputPattern, html, re.DOTALL)
            outputs = re.findall(altOutputPattern, html, re.DOTALL)
        
        # Clean up HTML entities and tags
        def cleanText(text: str) -> str:
            # Decode common HTML entities
            text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
            text = text.replace('&quot;', '"').replace('&#39;', "'")
            text = text.replace('&nbsp;', ' ')

            # Convert <br> tags to newlines
            text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
            
            # Convert closing </div> tags to newlines (this is the key fix!)
            text = re.sub(r'</div>', '\n', text, flags=re.IGNORECASE)
            
            # Remove all other HTML tags
            text = re.sub(r'<[^>]+>', '', text)

            # Return exactly as-is (preserve spacing and newlines)
            return text.strip()

        
        inputs = [cleanText(inp) for inp in inputs]
        outputs = [cleanText(out) for out in outputs]
        timeLimit = cleanText(timeLimit[0])
        if not inputs or not outputs:
            print("{RED}ERROR{RESET}: No sample tests found!")
            print("This could mean:")
            print("  - Wrong contest ID or problem letter")
            print("  - Problem doesn't have sample tests")
            print("  - Codeforces changed their HTML structure")
            
            # Debug: save HTML to file for inspection
            with open(f"debug_{contestId}_{problemLetter}.html", "w", encoding="utf-8") as f:
                f.write(html)
            print(f"  - HTML saved to debug_{contestId}_{problemLetter}.html for inspection")
            return False
            
        if len(inputs) != len(outputs):
            print(f"{YELLOW}Warning{RESET}: Found {len(inputs)} inputs but {len(outputs)} outputs")
            minCount = min(len(inputs), len(outputs))
            inputs = inputs[:minCount]
            outputs = outputs[:minCount]

        # Create tests directory
        os.makedirs("tests", exist_ok=True)
        
        # Write test files
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
        
        print(f"{GREEN}Downloaded{RESET} {len(inputs)} sample tests for {type} {contestId} problem {problemLetter}")
        print(f"   Time limit: {timeLimit}")
        
        # Show what we downloaded
        for i in range(1, len(inputs) + 1):
            print(f"   {problemLetter}{i}.in, {problemLetter}{i}.out")
        print(f"   {problemLetter}_metadata.json")
            
        return True
        
    except Exception as e:
        print(f"{RED}ERROR{RESET}: Error parsing HTML: {e}")
        return False

def main():
    # print(len(sys.argv))
    if len(sys.argv) != 4:
        print("Usage: python3 cf_fetch.py <type> <contestId> <problemLetter>")
        print("Example: python3 cf_fetch.py 2139 B")
        sys.exit(1)
    # print(sys.argv)
    type = sys.argv[1].strip()
    contestId = sys.argv[2].strip()
    problemLetter = sys.argv[3].strip().upper()
    
    if not contestId.isdigit():
        print("{RED}ERROR{RESET}: INVALID ID: Contest ID must be a number")
        sys.exit(1)
        
    if len(problemLetter) != 1 or not problemLetter.isalpha():
        print("{RED}ERROR{RESET}: INVALID PROBLEM LETTER: Problem letter must be a single letter (A, B, C, etc.)")
        sys.exit(1)
    
    success = fetchTests(type, contestId, problemLetter)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()