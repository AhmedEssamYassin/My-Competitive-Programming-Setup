# Color definitions
GREEN := \033[0;32m
RED := \033[0;31m
YELLOW := \033[1;33m
BLUE := \033[0;34m
RESET := \033[0m

# Variables
CXX := g++
PYTHON := python3
CXXFLAGS := -std=c++2b -O3 -DLOCAL
TARGET := Code
SRC := Code.cpp

CONTEST ?=
GYM ?=
PROBLEMSET ?=
PROBLEM ?= 

ifeq ($(OS),Windows_NT)
    CLEAN_TESTS := @if exist tests rmdir /S /Q tests 2>nul
    CLEAN_TEST_FILES := @if exist tests\*.* del /Q tests\*.* 2>nul
    CLEAN_TARGET := @if exist $(TARGET).exe del /Q $(TARGET).exe 2>nul
    CLEAN_OUTPUT := @if exist Output.txt del /Q Output.txt 2>nul
else
    CLEAN_TESTS := @rm -rf tests 2>/dev/null || true
    CLEAN_TEST_FILES := @rm -f tests/* 2>/dev/null || true
    CLEAN_TARGET := @rm -f $(TARGET) 2>/dev/null || true  
    CLEAN_OUTPUT := @rm -f Output.txt 2>/dev/null || true
endif

.PHONY: check-tools
check-tools:
	@$(PYTHON) -c "import shutil, sys; shutil.which('$(CXX)') or sys.exit(1)" || ($(PYTHON) -c "print('$(RED)$(CXX) not found! Install build tools.$(RESET)')" && exit 1)
	@$(PYTHON) -c "import sys; sys.version_info >= (3,0) or sys.exit(1)" || ($(PYTHON) -c "print('$(RED)Python 3 not found!$(RESET)')" && exit 1)
	@$(PYTHON) -c "print('$(GREEN)Tools checked: $(CXX) and $(PYTHON) found.$(RESET)')"

# Default target
.DEFAULT_GOAL := help
all: $(TARGET)

# Link and compile
$(TARGET): $(SRC)
	@$(PYTHON) -c "print('$(YELLOW)Compiling$(RESET) $(SRC)...')"
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(SRC)
	@$(PYTHON) -c "print('$(GREEN)Compilation successful!$(RESET)')"

# Run the binary
run: $(TARGET)
	@$(PYTHON) -c "import os; \
	not os.path.exists('input.txt') and \
	(print('$(RED)Warning: input.txt not found! Creating empty file...$(RESET)'), open('input.txt','w').close()); \
	print(f'$(YELLOW)Running$(RESET) $(TARGET)...')"
	@$(PYTHON) -c "import os; os.system('$(TARGET)' if os.name=='nt' else './$(TARGET)')"

# Fetch Codeforces samples
fetch:
ifeq ($(strip $(CONTEST)$(GYM)$(PROBLEMSET)),)
	@$(PYTHON) -c "print('$(RED)Error$(RESET): Contest ID required')"
	@$(PYTHON) -c "print('Usage:')"
	@$(PYTHON) -c "print('  make fetch CONTEST=2139 PROBLEM=B  (for regular contests)')"
	@$(PYTHON) -c "print('  make fetch GYM=106084 PROBLEM=B    (for gym contests)')"
	@$(PYTHON) -c "print('  make fetch PROBLEMSET=1375 PROBLEM=C    (for problemset problems)')"
	@exit 1
endif
ifeq ($(PROBLEM),)
	@$(PYTHON) -c "print('$(RED)Error$(RESET): PROBLEM parameter required')"
	@$(PYTHON) -c "print('Usage: make fetch CONTEST=2139 PROBLEM=B')"
	@exit 1
endif
	@$(MKDIR)
ifdef CONTEST
	@$(PYTHON) -c "print('$(YELLOW)Fetching$(RESET) contest $(CONTEST) problem $(PROBLEM)...')"
	$(PYTHON) cf_fetch.py contest $(CONTEST) $(PROBLEM)
endif
ifdef GYM
	@$(PYTHON) -c "print('$(YELLOW)Fetching$(RESET) gym $(GYM) problem $(PROBLEM)...')"
	$(PYTHON) cf_fetch.py gym $(GYM) $(PROBLEM)
endif
ifdef PROBLEMSET
	@$(PYTHON) -c "print('$(YELLOW)Fetching$(RESET) problemset $(PROBLEMSET) problem $(PROBLEM)...')"
	$(PYTHON) cf_fetch.py PROBLEMSET $(PROBLEMSET) $(PROBLEM)
endif

tests:
	@$(MKDIR)

# Test runner
test-only: $(TARGET)
ifeq ($(PROBLEM),)
	@$(PYTHON) -c "print('$(RED)Error$(RESET): PROBLEM parameter is required')"
	@$(PYTHON) -c "print('Usage: make test-only PROBLEM=B')"
	@exit 1
endif
	@$(PYTHON) run_tests.py $(PROBLEM) $(TARGET)

# Clean test files
clean:
	@$(PYTHON) -c "print('$(YELLOW)Cleaning...$(RESET)')"
	$(CLEAN_TEST_FILES)
	@$(PYTHON) -c "print('$(GREEN)Clean complete!$(RESET)')"

# Contest-style test runner (clean -> fetch -> test)
test: clean fetch test-only

# Debug build
debug:
	$(CXX) -std=c++2b -g -O0 -Wall -Wextra -DDEBUG -o $(TARGET) $(SRC)

# Simple check
check: check-tools
	@$(PYTHON) -c "print('$(YELLOW)Checking compiler...$(RESET)')"
	@$(CXX) --version
	@$(PYTHON) -c "print('$(GREEN)Check complete!$(RESET)')"

# Show available tests
show-tests:
	@$(PYTHON) -c "print('$(BLUE)Available test files:$(RESET)')"
ifeq ($(OS),Windows_NT)
	@dir tests 2>nul || $(PYTHON) -c "print('$(RED)No tests directory found$(RESET)')"
else
	@ls -la tests/ 2>/dev/null || $(PYTHON) -c "print('$(RED)No tests directory found$(RESET)')"
endif

help:
	@$(PYTHON) -c "print('$(BLUE)Competitive Programming Makefile$(RESET)')"
	@echo ""
	@$(PYTHON) -c "print('$(YELLOW)Fetch Tests:$(RESET)')"
	@echo "  make -f makefile fetch CONTEST=1789 PROBLEM=C"
	@echo "  make -f makefile fetch GYM=104114 PROBLEM=A"
	@echo ""
	@$(PYTHON) -c "print('$(YELLOW)Build:$(RESET)')"
	@echo "  make -f makefile          - Compile optimized"
	@echo "  make -f makefile debug    - Compile with debug"
	@echo ""
	@$(PYTHON) -c "print('$(YELLOW)Test:$(RESET)')"
	@echo "  make -f makefile test CONTEST=1789 PROBLEM=C  - Fetch + test"
	@echo "  make -f makefile test GYM=104114 PROBLEM=A    - Fetch + test"
	@echo "  make -f makefile test-only PROBLEM=C          - Test only"
	@echo ""
	@$(PYTHON) -c "print('$(YELLOW)Other:$(RESET)')"
	@echo "  make -f makefile run      - Run with input.txt"
	@echo "  make -f makefile clean    - Clean files"
	@echo "  make -f makefile check    - Verify setup"

.PHONY: all run clean debug check fetch test test-only show-tests help