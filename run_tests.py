import sys
import os
import subprocess
import glob
import json
from pathlib import Path

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

def loadTimeLimit(problem):
    """Load time limit from metadata file, return default if not found"""
    metadataFile = f"tests/{problem}_metadata.json"
    defaultTimeout = 6
    
    try:
        if os.path.exists(metadataFile):
            with open(metadataFile, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            timeLimit = metadata.get('timeLimit', defaultTimeout)
            # Ensure it's a number
            timeLimit = float(timeLimit.split(" ", 1)[0])
            print(f"{BLUE}Using time limit: {timeLimit} seconds (from {metadataFile}){RESET}")
            return timeLimit
        else:
            print(f"{YELLOW}No metadata file found ({metadataFile}), using default timeout: {defaultTimeout}s{RESET}")
            return float(defaultTimeout)
    except Exception as e:
        print(f"{YELLOW}Error reading metadata file: {e}, using default timeout: {defaultTimeout}s{RESET}")
        return float(defaultTimeout)
    
def runTest(executable, inputFile, expectedOutputFile, timeout = 6):
    """Run a single test case and return (passed, message)"""
    try:
        # Read input
        with open(inputFile, 'r', encoding='utf-8') as f:
            inputData = f.read()
        
        # Read expected output
        with open(expectedOutputFile, 'r', encoding='utf-8') as f:
            expectedOutput = f.read().strip()
        
        # Run the program
        try:
            result = subprocess.run(
                [executable], 
                input=inputData, 
                capture_output=True, 
                text=True, 
                timeout=timeout,
                encoding='utf-8'
            )
        except subprocess.TimeoutExpired:
            return False, "TIME LIMIT EXCEEDED"
        except FileNotFoundError:
            return False, f"EXECUTABLE NOT FOUND: {executable}"
        except Exception as e:
            return False, f"RUNTIME ERROR: {e}"
        
        if result.returncode != 0:
            return False, f"RUNTIME ERROR (exit code {result.returncode})"
        
        # Clean up any existing Output.txt
        outputFilePath = "Output.txt"

        # ... (run the program) ...

        # Read actual output from Output.txt
        outputFilePath = "Output.txt"
        actualOutput = ""
        if os.path.exists(outputFilePath):
            try:
                with open(outputFilePath, 'r', encoding='utf-8') as f:
                    actualOutput = f.read().strip()
            except Exception as e:
                return False, f"ERROR READING OUTPUT FILE: {e}"        
        elif result.stdout.strip():
            # Fallback to stdout for local testing
            actualOutput = result.stdout.strip()
        else:
            return False, "NO OUTPUT GENERATED: Neither Output.txt nor stdout contains output"    
        
        # Compare outputs (ignore trailing whitespace)
        expectedLines = [line.rstrip() for line in expectedOutput.splitlines()]
        actualLines = [line.rstrip() for line in actualOutput.splitlines()]

        if expectedLines == actualLines:
            return True, "ACCEPTED"
        else:
            # Format output comparison nicely
            expectedLines = expectedOutput.split('\n')
            actualLines = actualOutput.split('\n')
            
            errorMsg = "WRONG ANSWER\n"
            errorMsg += "   Expected:\n"
            for i, line in enumerate(expectedLines):
                errorMsg += f"     {i + 1}: {line}\n"
            errorMsg += "   Got:\n"
            for i, line in enumerate(actualLines):
                errorMsg += f"     {i + 1}: {line}\n"
            
            # Show line-by-line differences
            maxLines = max(len(expectedLines), len(actualLines))
            differences = []
            for i in range(maxLines):
                expLine = expectedLines[i] if i < len(expectedLines) else "[MISSING]"
                actLine = actualLines[i] if i < len(actualLines) else "[MISSING]"
                if expLine != actLine:
                    differences.append(f"Line {i + 1}: Expected '{expLine}', Got '{actLine}'")
            
            if differences:
                errorMsg += "   Differences:\n"
                for diff in differences:  # Show all
                    errorMsg += f"     {diff}\n"
            
            return False, errorMsg.rstrip()
    
    except Exception as e:
        return False, f"ERROR: {e}"

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 run_tests.py <PROBLEM> <EXECUTABLE>")
        print("Example: python3 run_tests.py B Code")
        sys.exit(1)
    
    problem = sys.argv[1].upper()
    executable = sys.argv[2]
    # Load time limit from metadata
    timeout = loadTimeLimit(problem)

    # Add .exe extension on Windows if needed
    if os.name == 'nt' and not executable.endswith('.exe'):
        if os.path.exists(executable + '.exe'):
            executable += '.exe'
    
    # Check if executable exists
    if not os.path.exists(executable):
        print(f"{RED}Error: Executable '{executable}' not found{RESET}")
        sys.exit(1)
    
    # Find test files
    testPattern = f"tests/{problem}*.in"
    inputFiles = glob.glob(testPattern)
    
    if not inputFiles:
        print(f"{RED}No test files found for problem {problem}{RESET}")
        print(f"Looking for pattern: {testPattern}")
        sys.exit(1)
    
    inputFiles.sort()  # Ensure consistent order
    
    passed = 0
    total = 0
    
    print(f"{YELLOW}Running tests for problem {problem}...{RESET}")
    print()
    
    for inputFile in inputFiles:
        total += 1
        baseName = Path(inputFile).stem  # e.g., "B1" from "B1.in"
        expectedFile = f"tests/{baseName}.out"
        
        if not os.path.exists(expectedFile):
            print(f"{RED}{baseName}: MISSING OUTPUT FILE{RESET}")
            continue
        
        success, message = runTest(executable, inputFile, expectedFile, timeout)
        
        if success:
            print(f"{GREEN}{baseName}: {message}{RESET}")
            passed += 1
        else:
            print(f"{RED}{baseName}: {message}{RESET}")
    
    print()
    if passed == total and total > 0:
        print(f"{GREEN}All {total} tests passed ✅{RESET}")
        sys.exit(0)
    else:
        print(f"{RED}{passed} / {total} tests passed ❌{RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()