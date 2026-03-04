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
    """Fetch sample tests from Codeforces problem page using Scrapling."""
    typeParam = typeParam.lower()
    problemLetter = problemLetter.upper()
    if(typeParam == "problemset"):
        url = f"https://codeforces.com/{typeParam}/problem/{contestId}/{problemLetter}"
    else:
        url = f"https://codeforces.com/{typeParam}/{contestId}/problem/{problemLetter}"

    print(f"{YELLOW}Fetching{RESET} from: {url}")
    
    try:
        from scrapling.fetchers import StealthyFetcher
    except ImportError:
        print(f"{RED}ERROR{RESET}: Scrapling library not found.")
        print("Please install it by running: pip install \"scrapling[all]\"")
        return False
        
    try:
        # Use Scrapling's StealthyFetcher to bypass Cloudflare and 403 errors
        page = StealthyFetcher.fetch(url, headless=True)
        
        # Get the raw HTML content
        html = getattr(page, 'html_content', getattr(page, 'html', str(page)))
            
        # Error detection
        if "404" in html or "Problem not found" in html:
            print(f"{RED}ERROR{RESET}: Problem {contestId}{problemLetter} not found!")
            return False
        elif "Contest not found" in html:
            print(f"{RED}ERROR{RESET}: Contest {contestId} not found or not public!")
            return False  
        # Cloudflare might still show a challenge page
        elif "cf-browser-verification" in html or "Just a moment..." in html:
            print(f"{RED}ERROR{RESET}: Blocked by Cloudflare challenge page!")
            return False
        elif not re.search(r'<div class="(input|sample-test)"', html):
            print(f"{RED}ERROR{RESET}: Problem {contestId}{problemLetter} found but has no sample tests!")
            print("This might be an output-only or interactive problem")
            # Save to debug file to see what Scrapling actually saw
            with open(f"debug_{contestId}_{problemLetter}.html", "w", encoding="utf-8") as f:
                f.write(html)
            return False
            
    except Exception as e:
        print(f"{RED}ERROR{RESET}: Unexpected error while fetching: {e}")
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
        timeLimit = cleanText(timeLimit[0]) if timeLimit else "Unknown"
        
        if not inputs or not outputs:
            print(f"{RED}ERROR{RESET}: No sample tests found!")
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
        
        print(f"{GREEN}Downloaded{RESET} {len(inputs)} sample tests for {typeParam} {contestId} problem {problemLetter}")
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
        
    if len(problemLetter) != 1 or not problemLetter.isalpha():
        print(f"{RED}ERROR{RESET}: INVALID PROBLEM LETTER: Problem letter must be a single letter (A, B, C, etc.)")
        sys.exit(1)
    
    success = fetchTests(typeParam, contestId, problemLetter)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()