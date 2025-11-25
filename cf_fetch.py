import urllib.request
import urllib.error
import sys
import os
import re
import json

def detectContestType(contestId: str) -> str:
    """Auto-detect contest type based on contest ID patterns"""
    try:
        contestNum = int(contestId)
        if contestNum >= 100000:  # Gym contests
            return "gym"
        elif contestNum >= 1:     # Regular contests
            return "contest"
    except:
        pass
    
    # Default fallback
    return "contest"

def fetchTests(typeParam:str, contestId: str, problemLetter: str):
    """Fetch sample tests from Codeforces problem page using only built-in modules."""
    # Auto-detect if type is not specified properly
    if typeParam.lower() not in ['contest', 'gym', 'problemset']:
        typeParam = detectContestType(contestId)
        print(f"🔄 Auto-detected contest type: {typeParam}")
    typeParam = typeParam.lower()
    problemLetter = problemLetter.upper()
    url = f"https://codeforces.com/{typeParam}/{contestId}/problem/{problemLetter}"

    print(f"Fetching from: {url}")
    
    try:
        # Create request with headers
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        # Create SSL context that doesn't verify certificates (for problematic systems)
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
            html = response.read().decode('utf-8')
            
        # Error detection
        if "404" in html or "Problem not found" in html:
            print(f"❌ Problem {contestId}{problemLetter} not found!")
            return False
        elif "Contest not found" in html:
            print(f"❌ Contest {contestId} not found or not public!")
            print("💡 Try: gym contest, check contest ID, or wait if contest is running")
            return False  
        elif not re.search(r'<div class="(input|sample-test)"', html):
            print(f"❌ Problem {contestId}{problemLetter} found but has no sample tests!")
            print("💡 This might be an output-only or interactive problem")
            return False
            
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP error {e.code}: {e.reason}")
        return False
    except urllib.error.URLError as e:
        print(f"❌ Connection error: {e.reason}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
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
            print("❌ No sample tests found!")
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
            print(f"⚠️  Warning: Found {len(inputs)} inputs but {len(outputs)} outputs")
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
        
        print(f"✅ Downloaded {len(inputs)} sample tests for {type} {contestId} problem {problemLetter}")
        print(f"   ⏱️  Time limit: {timeLimit}")
        
        # Show what we downloaded
        for i in range(1, len(inputs) + 1):
            print(f"   📁 {problemLetter}{i}.in, {problemLetter}{i}.out")
        print(f"   📄 {problemLetter}_metadata.json")
            
        return True
        
    except Exception as e:
        print(f"❌ Error parsing HTML: {e}")
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
        print("❌ Contest ID must be a number")
        sys.exit(1)
        
    if len(problemLetter) != 1 or not problemLetter.isalpha():
        print("❌ Problem letter must be a single letter (A, B, C, etc.)")
        sys.exit(1)
    
    success = fetchTests(type, contestId, problemLetter)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()