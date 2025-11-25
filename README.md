# 🚀 Competitive Programming Setup

A powerful, automated toolkit for competitive programming that streamlines your workflow from problem fetching to testing. Built with Python and C++, this setup handles everything so you can focus on solving problems.

## ✨ Features

### 🎯 **One-Command Problem Setup**
- Automatically fetch sample test cases from Codeforces
- Auto-detect contest type (regular/gym)
- Parse time limits and metadata
- Ready-to-test environment in seconds

### ⚡ **Lightning-Fast Testing**
- Parallel test execution with custom timeouts
- Detailed diff output for wrong answers
- Color-coded results (✅ PASSED, ❌ FAILED, ⏰ TLE)
- Smart executable detection (Windows/Linux compatible)

### 🔧 **Advanced Debugging**
- Comprehensive debug template with colored output
- Variable inspection with type-aware printing
- Performance timing for code sections
- Support for complex STL containers

### 🛠️ **Cross-Platform Build System**
- Optimized compilation flags (`-O3`, `-std=c++2b`)
- Debug builds with full error checking
- Automatic dependency management
- Windows and Linux compatible

## 📁 File Overview

| File | Purpose | Key Features |
|------|---------|--------------|
| `MakeFile` | Build automation & workflow management | Cross-platform, contest fetching, testing pipeline |
| `cf_fetch.py` | Codeforces sample test downloader | Auto-detection, HTML parsing, metadata extraction |
| `run_tests.py` | Test runner with advanced verification | Timeout handling, detailed diffs, color output |
| `debug.cpp` | Advanced debugging template | STL container printing, timers, colored output |

## 🚀 Quick Start

### Most Common Commands

```bash
# Fetch problem and run tests (most used!)
make test CONTEST=1789 PROBLEM=C

# For gym contests
make test GYM=104114 PROBLEM=A

# Test existing downloaded samples
make test-only PROBLEM=B

# Compile and run with input.txt
make run

# Debug build with full error checking
make debug
```

## 💪 Power Features in Action

### 1. **Intelligent Problem Fetching**
```bash
make fetch CONTEST=2139 PROBLEM=B
```
**What happens:**
- 🌐 Fetches from `https://codeforces.com/contest/2139/problem/B`
- 📊 Parses HTML to extract sample inputs/outputs
- ⏱️ Extracts time limit (e.g., "2 seconds")
- 📝 Creates `tests/B1.in`, `tests/B1.out`, `tests/B_metadata.json`
- 🎯 Auto-detects contest type based on ID patterns

### 2. **Advanced Test Runner**
```bash
make test-only PROBLEM=B
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

### 3. **Powerful Debug Template**
Include `debug.cpp` in your solution:
```cpp
#include "debug.cpp"

int main() {
    vector<int> arr = {1, 2, 3};
    map<string, int> mp = {{"hello", 5}, {"world", 3}};
    
    debug(arr, mp);  // Colored output with variable names
    
    LabeledTimer timer("sorting");
    sort(arr.begin(), arr.end());
    // Timer automatically prints elapsed time
}
```

**Debug Output:**
```
🔵 42: [arr = {1,2,3} || mp = {("hello",5),("world",3)}]
🔴 [TIMER] sorting took: 0.000123 s
```

### 4. **Smart Cross-Platform Compatibility**
- **Windows**: Auto-adds `.exe` extension, handles Windows paths
- **Linux**: Native Unix commands and paths
- **Both**: Color support detection, proper encoding handling

## 🎯 Typical Workflow

```bash
# 1. Start a new problem
make test CONTEST=1847 PROBLEM=D

# 2. Write your solution in Code.cpp
vim Code.cpp

# 3. Test your solution
make test-only PROBLEM=D

# 4. Debug if needed
make debug
make test-only PROBLEM=D

# 5. Submit when all tests pass! ✅
```

## 🔧 Advanced Usage

### Custom Test Cases
Add your own test cases:
```bash
# Add tests/D4.in and tests/D4.out
make test-only PROBLEM=D  # Will run all tests including custom ones
```

### Performance Testing
```cpp
#include "debug.cpp"
int main() {
    LabeledTimer total("solution");
    
    // Your solution here
    {
        LabeledTimer sort_phase("sorting");
        sort(arr.begin(), arr.end());
    }
    
    {
        LabeledTimer search_phase("binary_search");
        // binary search code
    }
    
    // Timers print automatically when destroyed
}
```

### Batch Testing
```bash
# Test multiple problems
for problem in A B C D; do
    echo "Testing $problem..."
    make test-only PROBLEM=$problem
done
```

## 🌟 Why This Setup Rocks

### ⚡ **Speed**: 
- Fetch and test a problem in under 5 seconds
- No manual copy-pasting of test cases
- Instant feedback with detailed error analysis

### 🎯 **Accuracy**: 
- Exact time limit enforcement from problem metadata  
- Precise output comparison with whitespace handling
- Catches edge cases other setups miss

### 🔧 **Flexibility**:
- Works with any Codeforces contest (regular/gym/problemset)
- Supports custom test cases
- Cross-platform compatibility

### 🚀 **Productivity**:
- Focus on algorithm, not setup
- Visual debugging with colored output
- Automated build optimization

## 🛠️ Setup Requirements

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

*"Competitive programming is about solving problems, not fighting tools. This setup gets you there faster."* 🏆