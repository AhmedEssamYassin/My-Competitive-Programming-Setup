# Competitive Programming Setup

A powerful, automated toolkit for competitive programming that streamlines your workflow from problem fetching to testing. Built with Python and C++, this setup handles everything so you can focus on solving problems.

## Features

### **One-Command Problem Setup**
- Automatically fetch sample test cases from [Codeforces](https://codeforces.com/)
- Parse time limits and metadata
- Ready-to-test environment in seconds

### **Lightning-Fast Testing**
- Parallel test execution with custom timeouts
- Detailed diff output for wrong answers
- Color-coded results (PASSED, FAILED, TLE)
- Smart executable detection (Windows/Linux compatible)

### **Advanced Debugging**
- Comprehensive debug template with colored output
- Variable inspection with type-aware printing
- Performance timing for code sections
- Support for complex STL containers

### **Cross-Platform Build System**
- Optimized compilation flags (`-O3`, `-std=c++2b`)
- Debug builds with full error checking
- Automatic dependency management
- Windows and Linux compatible

## 📁 File Overview

| File | Purpose | Key Features |
|------|---------|--------------|
| `Makefile` | Build automation & workflow management | Cross-platform, contest fetching, testing pipeline |
| `cf_fetch.py` | Codeforces sample test downloader | Auto-detection, HTML parsing, metadata extraction |
| `run_tests.py` | Test runner with advanced verification | Timeout handling, detailed diffs, color output |
| `debug.cpp` | Advanced debugging template | STL container printing, timers, colored output |
| `cpp.json` | VS Code Snippet | Instant template generation with timestamp & debug setup |

## Quick Start

### Most Common Commands (on windows)

```bash
# Fetch problem and run tests (most used!)
make -f Makefile test CONTEST=1789 PROBLEM=C

# For gym contests
make -f Makefile test GYM=104114 PROBLEM=A

# Test existing downloaded samples
make -f Makefile test-only PROBLEM=B

# Compile and run with input.txt
make -f Makefile run

# Debug build with full error checking
make -f Makefile debug
```

## Powerful Features in Action

### 1. VS Code Snippets

This setup includes a custom VS Code snippet (`cpp.json`) that instantly generates your competitive programming template with the current timestamp and debug configurations. (and also any other templates you would like to add).

#### Installation
To make the snippet work, you must place the `cpp.json` file in your VS Code User Snippets directory:

**Required Path:**
```
C:\Users\(username)\AppData\Roaming\Code\User\snippets
```

### 2. **Intelligent Problem Fetching**
```bash
make -f Makefile fetch CONTEST=2139 PROBLEM=B
```
**What happens:**
- 🌐 Fetches from `https://codeforces.com/contest/2139/problem/B`
- 📊 Parses HTML to extract sample inputs/outputs
- ⏱️ Extracts time limit (e.g., "2 seconds")
- 📝 Creates `tests/B1.in`, `tests/B1.out`, `tests/B_metadata.json`

### 3. **Advanced Test Runner**
```bash
make -f Makefile test-only PROBLEM=B
```
**Output Example:**
```
🔵 Using time limit: 2.0 seconds (from tests/B_metadata.json)
🟡 Running tests for problem B...

✅ B1: ACCEPTED
✅ B2: ACCEPTED  
❌ B3: WRONG ANSWER
   Expected:
     1: 42
     2: 13
   Got:
     1: 41
     2: 13
   Differences:
     Line 1: Expected '42', Got '41'

✅ 2 / 3 tests passed ❌
```

### 4. **Powerful Debug Template**
This debug template is mainly by: [Anshul_Johri](https://codeforces.com/profile/Anshul_Johri), you can find the full blog on codeforces [here](https://codeforces.com/blog/entry/125435) and was modified by **me** to add `LabeledTimer`

Include `debug.cpp` in your solution:

```cpp
#ifndef ONLINE_JUDGE
#include "debug.cpp"
#define TIME_BLOCK(name)    \
	if (bool _once = false) \
	{                       \
	}                       \
	else                    \
		for (__DEBUG_UTIL__::LabeledTimer _t(name); !_once; _once = true)
#else
#define debug(...)
#define debugArr(...)
#define TIME_BLOCK(name) if (true)
#endif // Debugging locally
```

#### Example:
```cpp
vector<int> arr{1, 2, 3};
map<string, int> mp;
mp["hello"] = 5;
mp["world"] = 3;
debug(arr, mp);
```

**Debug Output:**
```
🔵 42: [arr = {1,2,3} || mp = {("hello",5),("world",3)}]
```

### Performance Testing
```cpp
TIME_BLOCK ("sorting")
{
    sort(arr.begin(), arr.end());
}
// Timers print automatically when destroyed
```
**Output:**
```
🔴 [TIMER] sorting took: 0.000123 s
```

### 5. **Smart Cross-Platform Compatibility**
- **Windows**: Auto-adds `.exe` extension, handles Windows paths
- **Linux**: Native Unix commands and paths
- **Both**: Color support detection, proper encoding handling

## Typical Workflow

```bash
# 1. Write your solution in Code.cpp
# 2. Fetch and Test
make -f Makefile test CONTEST=1847 PROBLEM=D

# 3. For subsequences testing (no need to fetch again)
make -f Makefile test-only PROBLEM=D

# 5. Submit when all tests pass!
```

### Custom Test Cases
Add your own test cases:
```bash
# Add tests/D4.in and tests/D4.out
make test-only PROBLEM=D  # Will run all tests including custom ones
```

## Why This Setup Rocks

### **Speed**: 
- Fetch and test a problem in under 5 seconds
- No manual copy-pasting of test cases
- Instant feedback with detailed error analysis

### **Accuracy**: 
- Exact time limit enforcement from problem metadata  
- Precise output comparison with whitespace handling
- Catches edge cases other setups miss

### **Flexibility**:
- Works with any Codeforces contest (contest/gym/problemset)
- Supports custom test cases
- Cross-platform compatibility

### **Productivity**:
- Focus on algorithm, not setup
- Visual debugging with colored output
- Automated build optimization

## Setup Requirements

```bash
# Required tools
g++          # C++ compiler with C++2b support
python3      # Python 3.6+

# Optional but recommended  
make         # For using the Makefile commands
```

## 📊 Success Stats

With this setup, you can:
- ✅ Fetch and test a problem: **< 10 seconds**
- ✅ Debug complex data structures: **Visual colored output**
- ✅ Handle 100+ test cases: **Automated with timeouts**
- ✅ Work on any platform: **Windows/Linux/Mac compatible**

---

*"Competitive programming is about solving problems, not fighting tools. This setup gets you there faster."*