"""
Test runner for competitive programming.
Runs compiled C++ executables against sample inputs, checks timeouts, and compares outputs.
"""
import sys
import os
import subprocess
import glob
import json
import time
from pathlib import Path
from utils import GREEN, RED, YELLOW, BLUE, RESET
import tui

try:
    import psutil
    _hasPsutil = True
except ImportError:
    _hasPsutil = False

def loadTimeLimit(problem):
    """Load time limit from metadata file, return default if not found"""
    metadataFile = f"tests/{problem}_metadata.json"
    defaultTimeout = 6
    
    try:
        if os.path.exists(metadataFile):
            with open(metadataFile, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            timeLimit = metadata.get('timeLimit', defaultTimeout)
            
            if timeLimit == "Unknown":
                return defaultTimeout
                
            # Ensure it's a number
            timeLimitStr = str(timeLimit).split(" ", 1)[0]
            parsedLimit = float(timeLimitStr)
            return parsedLimit
        else:
            return defaultTimeout
            
    except Exception as e:
        print(f"{YELLOW}Warning: Could not parse time limit from metadata: {e}. Using default.{RESET}")
        return defaultTimeout
    
def runTest(executable, inputFile, expectedOutputFile, timeout=6, onProgress=None):
    """Run a single test case and return (success, message, execTime, details)"""
    startTime = time.perf_counter()
    execTime = 0
    details = {}
    try:
        with open(inputFile, "r", encoding="utf-8") as f:
            inputData = f.read()
        
        with open(expectedOutputFile, "r", encoding="utf-8") as f:
            expectedOutput = f.read().strip()
        
        # Write test data to input.txt for C++ freopen compatibility
        try:
            with open("input.txt", "w", encoding='utf-8') as f:
                f.write(inputData)
        except Exception:
            pass
        
        # Clean up any existing Output.txt to prevent reading stale output
        outputFilePath = "Output.txt"
        if os.path.exists(outputFilePath):
            try:
                os.remove(outputFilePath)
            except Exception:
                pass

        try:
            if _hasPsutil:
                proc = subprocess.Popen(
                    [executable], 
                    stdin=subprocess.PIPE, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE, 
                    text=True, 
                    encoding='utf-8'
                )
                try:
                    p = psutil.Process(proc.pid)
                except Exception:
                    p = None
                
                maxMemory = 0
                try:
                    proc.stdin.write(inputData)
                    proc.stdin.flush()
                    proc.stdin.close()
                except Exception:
                    pass
                
                startPoll = time.perf_counter()
                
                # First immediate read (catches fast programs that exit in 15ms)
                if p:
                    try:
                        memInfo = p.memory_info()
                        mem = getattr(memInfo, 'peak_wset', memInfo.rss)
                        if mem > maxMemory:
                            maxMemory = mem
                    except Exception:
                        pass

                while proc.poll() is None:
                    if p:
                        try:
                            memInfo = p.memory_info()
                            mem = getattr(memInfo, 'peak_wset', memInfo.rss)
                            if mem > maxMemory:
                                maxMemory = mem
                        except Exception:
                            pass
                    if time.perf_counter() - startPoll > timeout:
                        proc.kill()
                        execTime = time.perf_counter() - startTime
                        return False, "TIME LIMIT EXCEEDED", execTime, None, 0
                    if onProgress:
                        onProgress(time.perf_counter() - startTime, maxMemory)
                    time.sleep(0.002) # Faster polling (2ms)
                
                # Check one last time if still zero
                if p and maxMemory == 0:
                    try:
                        memInfo = p.memory_info()
                        mem = getattr(memInfo, 'peak_wset', memInfo.rss)
                        if mem > maxMemory:
                            maxMemory = mem
                    except Exception:
                        pass
                
                resultStdout = proc.stdout.read() if proc.stdout else ""
                resultStderr = proc.stderr.read() if proc.stderr else ""
                resultReturncode = proc.returncode
                memoryUsed = maxMemory
            else:
                result = subprocess.run(
                    [executable], 
                    input=inputData, 
                    capture_output=True, 
                    text=True, 
                    timeout=timeout,
                    encoding='utf-8'
                )
                resultStdout = result.stdout
                resultStderr = result.stderr
                resultReturncode = result.returncode
                memoryUsed = 0
                
        except subprocess.TimeoutExpired:
            execTime = time.perf_counter() - startTime
            return False, "TIME LIMIT EXCEEDED", execTime, None, 0
        except FileNotFoundError:
            execTime = time.perf_counter() - startTime
            details["error"] = f"EXECUTABLE NOT FOUND: {executable}"
            return False, "ERROR", execTime, details, 0
        except Exception as e:
            execTime = time.perf_counter() - startTime
            details["error"] = f"RUNTIME ERROR: {e}"
            return False, "ERROR", execTime, details, 0
        
        execTime = time.perf_counter() - startTime
        
        if resultStderr:
            details["stderr"] = resultStderr

        if resultReturncode != 0:
            details["error"] = f"RUNTIME ERROR (exit code {resultReturncode})"
            return False, "RUNTIME ERROR", execTime, details, memoryUsed
        
        # Prefer stdout captured from subprocess; only read Output.txt as fallback
        # This avoids false AC/WA from a stale Output.txt left by a prior run.
        actualOutput = resultStdout.strip()
        if not actualOutput and os.path.exists(outputFilePath):
            try:
                with open(outputFilePath, 'r', encoding='utf-8') as f:
                    actualOutput = f.read().strip()
            except Exception as e:
                details["error"] = f"ERROR READING OUTPUT FILE: {e}"
                return False, "ERROR", execTime, details, memoryUsed
        
        expectedLines = [line.rstrip() for line in expectedOutput.splitlines()]
        actualLines = [line.rstrip() for line in actualOutput.splitlines()]

        if expectedLines == actualLines:
            return True, "ACCEPTED", execTime, details, memoryUsed
        elif expectedOutput.split() == actualOutput.split():
            return True, "ACCEPTED (Token)", execTime, details, memoryUsed
        else:
            details["expected"] = expectedOutput
            details["actual"] = actualOutput
            return False, "WRONG ANSWER", execTime, details, memoryUsed
    
    except Exception as e:
        execTime = time.perf_counter() - startTime
        details["error"] = f"ERROR: {e}"
        return False, "ERROR", execTime, details, 0

def runTestsForProblem(problem, executable):
    timeout = loadTimeLimit(problem)
    
    # Add .exe extension on Windows if needed
    if os.name == 'nt' and not executable.endswith('.exe'):
        if os.path.exists(executable + '.exe'):
            executable += '.exe'
    
    # Add ./ prefix on Linux/macOS for local executables
    if os.name != 'nt' and not executable.startswith(('./', '/')):
        executable = './' + executable
        
    # Check if executable exists
    if not os.path.exists(executable):
        print(f"{RED}Error: Executable '{executable}' not found{RESET}")
        return False
    
    if not _hasPsutil:
        print(f"{YELLOW}Warning: 'psutil' is not installed. Memory usage will show as N/A. Run 'pip install psutil' to fix this.{RESET}")
        
    # Find test files
    testPattern = f"tests/{problem}*.in"
    inputFiles = glob.glob(testPattern)
    
    if not inputFiles:
        print(f"{RED}No test files found for problem {problem}{RESET}")
        print(f"Looking for pattern: {testPattern}")
        return False
    
    inputFiles.sort()  # Ensure consistent order
    
    reporter = tui.TestReporter(hasPsutil=_hasPsutil)
    reporter.printHeader(problem)
    reporter.startTests(len(inputFiles))
    
    for inputFile in inputFiles:
        baseName = Path(inputFile).stem  # e.g., "B1" from "B1.in"
        expectedFile = f"tests/{baseName}.out"
        
        if not os.path.exists(expectedFile):
            reporter.addResult(baseName, False, 0.0, timeout, "MISSING OUTPUT", details={"error": "Missing expected output file"})
            continue
        
        reporter.updateLiveTest(baseName, 0.0, 0)
        success, message, execTime, details, memoryUsed = runTest(
            executable, inputFile, expectedFile, timeout,
            onProgress=lambda t, m: reporter.updateProgress(t, m)
        )
        
        reporter.addResult(baseName, success, execTime, timeout, message, memory=memoryUsed, details=details)
        
    reporter.stopTests()
    return reporter.passed == reporter.total

def main():
    if len(sys.argv) != 3:
        print("Usage: python run_tests.py <PROBLEM> <EXECUTABLE>")
        print("Example: python run_tests.py B bin/Code")
        sys.exit(1)
    
    problem = sys.argv[1].upper()
    executable = sys.argv[2]
        
    success = runTestsForProblem(problem, executable)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()