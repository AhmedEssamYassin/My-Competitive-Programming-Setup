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
        
        # 1. Extract the clean, visible text (ignores HTML tags/scripts)
        pageText = getattr(page, 'text', "")
        
        # 2. Extract the page Title securely using standard .css()
        titleNodes = page.css("title")
        title = titleNodes[0].text if titleNodes else ""
            
        # Check title and visible text (Soft 404s)
        if "Error" in title or "No such problem" in pageText or "Problem not found" in pageText:
            print(f"{RED}ERROR{RESET}: Problem {contestId}{problemLetter} not found!")
            return False
            
        elif "Contest not found" in pageText:
            print(f"{RED}ERROR{RESET}: Contest {contestId} not found or not public!")
            return False 
             
        # Cloudflare might still show a challenge page
        elif "Just a moment" in title or "cf-browser-verification" in pageText:
            print(f"{RED}ERROR{RESET}: Blocked by Cloudflare challenge page!")
            return False
            
        # Use Scrapling's CSS selector to check if test cases exist
        elif not page.css(".sample-test") and not page.css(".input"):
            print(f"{RED}ERROR{RESET}: Problem {contestId}{problemLetter} found but has no sample tests!")
            print("This might be an output-only or interactive problem")
            return False
            
    except Exception as e:
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

        # Extract the text
        inputs = [extractTestText(node) for node in inputNodes]
        outputs = [extractTestText(node) for node in outputNodes]
        
        # Extract Time Limit dynamically using raw HTML
        timeLimit = "Unknown"
        rawPageHtml = getattr(page, 'html_content', getattr(page, 'html', str(page)))        
        # Match the time limit div and grab the number right before the word 'second'
        timeMatch = re.search(r'<div class="time-limit"[^>]*>.*?(\d+(?:\.\d+)?)\s*second', rawPageHtml, re.DOTALL | re.IGNORECASE)
        if timeMatch:
            timeLimit = timeMatch.group(1)
        
        if not inputs or not outputs:
            print(f"{RED}ERROR{RESET}: No sample tests found!")
            print("This could mean:")
            print("  - Wrong contest ID or problem letter")
            print("  - Problem doesn't have sample tests")
            print("  - Codeforces changed their HTML structure")
            
            # Debug: save HTML to file for inspection
            with open(f"debug_{contestId}_{problemLetter}.html", "w", encoding="utf-8") as f:
                f.write(getattr(page, 'html_content', getattr(page, 'html', str(page))))
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