GREEN := \033[0;32m
RED := \033[0;31m
YELLOW := \033[1;33m
BLUE := \033[0;34m
RESET := \033[0m

CXX := g++
ifeq ($(OS),Windows_NT)
    # Prioritize venv Python, fallback to system Python
    PYTHON ?= $(if $(wildcard venv/Scripts/python.exe),"venv/Scripts/python.exe","$(shell py -c "import sys; print(sys.executable, end='')" 2>nul || echo python)")
else
    PYTHON ?= $(if $(wildcard venv/bin/python),"venv/bin/python","$(shell which python3 2>/dev/null || which python 2>/dev/null || echo python3)")
endif
CXXFLAGS := -std=c++2b -O3 -DLOCAL -Iinclude
# If PROBLEM is given, derive SRC from it (e.g. PROBLEM=F -> src/F.cpp)
ifdef PROBLEM
    SRC ?= src/$(PROBLEM).cpp
else
    SRC ?= src/Code.cpp
endif
TARGET ?= bin/$(basename $(notdir $(SRC)))

CONTEST ?=
GYM ?=
PROBLEMSET ?=
PROBLEM ?= 

ifeq ($(OS),Windows_NT)
    CLEAN_TESTS := @if exist tests rmdir /S /Q tests 2>nul
    CLEAN_TEST_FILES := @if exist tests\*.* del /Q tests\*.* 2>nul
    CLEAN_TARGET := @if exist bin\*.* del /Q bin\*.* 2>nul
    CLEAN_OUTPUT := @if exist Output.txt del /Q Output.txt 2>nul
    MKDIR_BIN := @if not exist bin mkdir bin
else
    CLEAN_TESTS := @rm -rf tests 2>/dev/null || true
    CLEAN_TEST_FILES := @rm -f tests/* 2>/dev/null || true
    CLEAN_TARGET := @rm -f bin/* 2>/dev/null || true  
    CLEAN_OUTPUT := @rm -f Output.txt 2>/dev/null || true
    MKDIR_BIN := @mkdir -p bin
endif

.PHONY: check-tools
check-tools:
	@$(PYTHON) -c "import shutil, sys; shutil.which('$(CXX)') or sys.exit(1)" || ($(PYTHON) -c "print('$(RED)$(CXX) not found! Install build tools.$(RESET)')" && exit 1)
	@$(PYTHON) -c "import sys; sys.version_info >= (3,0) or sys.exit(1)" || ($(PYTHON) -c "print('$(RED)Python 3 not found!$(RESET)')" && exit 1)
	@$(PYTHON) -c "print('$(GREEN)Tools checked: $(CXX) and $(PYTHON) found.$(RESET)')"

.DEFAULT_GOAL := help
all: $(TARGET)

# Link and compile
$(TARGET): $(SRC)
	$(MKDIR_BIN)
	@$(PYTHON) -c "print('$(YELLOW)Compiling$(RESET) $(SRC)...')"
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(SRC)
	@$(PYTHON) -c "print('$(GREEN)Compilation successful!$(RESET)')"

# Run the binary
run: $(TARGET)
	@$(PYTHON) -c "import os; \
	not os.path.exists('input.txt') and \
	(print('$(RED)Warning: input.txt not found! Creating empty file...$(RESET)'), open('input.txt','w').close()); \
	print(f'$(YELLOW)Running$(RESET) $(TARGET)...')"
	@$(PYTHON) -c "import os; os.system('$(TARGET)'.replace('/', '\\\\') if os.name=='nt' else './$(TARGET)')"

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
	$(MKDIR_BIN)
ifdef CONTEST
	@$(PYTHON) -c "print('$(YELLOW)Fetching$(RESET) contest $(CONTEST) problem $(PROBLEM)...')"
	$(PYTHON) scripts/cf_fetch.py contest $(CONTEST) $(PROBLEM)
endif
ifdef GYM
	@$(PYTHON) -c "print('$(YELLOW)Fetching$(RESET) gym $(GYM) problem $(PROBLEM)...')"
	$(PYTHON) scripts/cf_fetch.py gym $(GYM) $(PROBLEM)
endif
ifdef PROBLEMSET
	@$(PYTHON) -c "print('$(YELLOW)Fetching$(RESET) problemset $(PROBLEMSET) problem $(PROBLEM)...')"
	$(PYTHON) scripts/cf_fetch.py problemset $(PROBLEMSET) $(PROBLEM)
endif

tests:
	$(MKDIR_BIN)

test-only: $(TARGET)
ifeq ($(PROBLEM),)
	@$(PYTHON) -c "print('$(RED)Error$(RESET): PROBLEM parameter is required')"
	@$(PYTHON) -c "print('Usage: make test-only PROBLEM=B')"
	@exit 1
endif
	@$(PYTHON) scripts/run_tests.py $(PROBLEM) $(TARGET)

clean:
	@$(PYTHON) -c "print('$(YELLOW)Cleaning...$(RESET)')"
	$(CLEAN_TEST_FILES)
	$(CLEAN_TARGET)
	$(CLEAN_OUTPUT)
	@$(PYTHON) -c "print('$(GREEN)Clean complete!$(RESET)')"

listen:
	@$(PYTHON) -c "print('$(YELLOW)Starting Competitive Companion listener on port 10043...$(RESET)')"
	@$(PYTHON) scripts/companion_listen.py

test: clean fetch test-only

debug:
	$(MKDIR_BIN)
ifeq ($(OS),Windows_NT)
	@ MSYS2/ucrt64 does not ship libasan/libubsan — sanitizers skipped on Windows
	$(CXX) -std=c++2b -g -O0 -Wall -Wextra -DDEBUG -DLOCAL -Iinclude \
	    -fno-omit-frame-pointer -o $(TARGET) $(SRC)
else
	$(CXX) -std=c++2b -g -O0 -Wall -Wextra -DDEBUG -DLOCAL -Iinclude \
	    -fsanitize=address,undefined -fno-omit-frame-pointer -o $(TARGET) $(SRC)
endif

check: check-tools
	@$(PYTHON) -c "print('$(YELLOW)Checking compiler...$(RESET)')"
	@$(CXX) --version
	@$(PYTHON) -c "print('$(GREEN)Check complete!$(RESET)')"

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