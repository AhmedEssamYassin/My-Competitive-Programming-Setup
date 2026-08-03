"""
Interactive Terminal UI for CodeRunner.
Acts as a continuous shell to compile, fetch, and test problems without re-typing make commands.
"""
import os
import sys
import glob
import subprocess
import time
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.table import Table
from rich import box

import run_tests

# Path to persist command history across sessions
_HISTORY_FILE = os.path.join(os.path.expanduser("~"), ".cp_history")

console = Console()
commandHistory = []


def _loadHistory():
    """Load command history from disk on startup."""
    if os.path.exists(_HISTORY_FILE):
        try:
            with open(_HISTORY_FILE, "r", encoding="utf-8") as f:
                return [line.rstrip("\n") for line in f if line.strip()]
        except Exception:
            pass
    return []


def _saveHistory():
    """Persist the current command history to disk."""
    try:
        with open(_HISTORY_FILE, "w", encoding="utf-8") as f:
            for cmd in commandHistory[-500:]:
                f.write(cmd + "\n")
    except Exception:
        pass

TEMPLATE = """\
#include <bits/stdc++.h>
#ifdef LOCAL
#include "debug.cpp"
#define TIME_BLOCK(name, t) \\
    if (bool _once = false) \\
    {                       \\
    }                       \\
    else                    \\
        for (__DEBUG_UTIL__::LabeledTimer _t(name, t); !_once; _once = true)
#else
#define debug(...) void(0)
#define debugArr(...) void(0)
#define TIME_BLOCK(name, t) if (true)
#endif // Debugging locally
using namespace std;
#define ll long long int
#define endl "\\n"

int main()
{
    ios_base::sync_with_stdio(false);
    cin.tie(nullptr);
#ifdef LOCAL
    freopen("input.txt", "r", stdin);
    freopen("Output.txt", "w", stdout);
#endif
    int t = 1;
    // cin >> t;
    while (t--)
    {
    }
    return 0;
}
"""


def clearScreen():
    os.system("cls" if os.name == "nt" else "clear")


def printHeader():
    header = Panel(
        "[bold #00e5ff]CodeRunner Interactive Shell[/]\n"
        "[#00ff41]Type a command below to compile, fetch, or test problems.[/]",
        title="[bold #e0e0e0]Dashboard[/]",
        border_style="#00e5ff",
        box=box.SQUARE
    )
    console.print(header)


def getAvailableProblems():
    cppFiles = glob.glob("src/*.cpp")
    problems = []
    for f in cppFiles:
        prob = os.path.basename(f).replace('.cpp', '')
        problems.append(prob)
    # Keep Code at the top
    if "Code" in problems:
        problems.remove("Code")
        problems.insert(0, "Code")
    return problems


def printStatus():
    probs = getAvailableProblems()
    if not probs:
        console.print("[#666666]No .cpp files found in src/ directory.[/]")
    else:
        table = Table(box=box.SIMPLE, show_header=False)
        table.add_column("Problem", style="bold #e0e0e0")
        table.add_column("Status", style="#84967e")
        for p in probs:
            exeName = f"bin/{p}" + (".exe" if os.name == "nt" else "")
            status = "[#00ff41]Compiled[/]" if os.path.exists(exeName) else "[#666666]Uncompiled[/]"

            testFiles = glob.glob(f"tests/{p}*.in")
            if testFiles:
                status += f" | [#00e5ff]{len(testFiles)} tests found[/]"
            else:
                status += " | [#ff1744]No tests[/]"

            table.add_row(f"Problem {p}", status)
        console.print(table)

    console.print()
    console.print("[bold #00ff41]Commands:[/]")
    console.print("  [#00e5ff]new \\[prob][/]               - Create src/\\[prob].cpp from template & clean old tests")
    console.print("  [#00e5ff]open \\[prob][/]              - Open src/\\[prob].cpp in VS Code")
    console.print("  [#00e5ff]run \\[file][/]               - Compile & run against input.txt (no test comparison)")
    console.print("  [#00e5ff]test \\[prob][/]              - Compile src/\\[prob].cpp & run tests for \\[prob]")
    console.print("  [#00e5ff]test \\[file] \\[prob][/]       - Compile src/\\[file] & run tests for \\[prob]")
    console.print("  [#00e5ff]debug \\[file] \\[prob][/]      - Compile with sanitizers & run tests")
    console.print("  [#00e5ff]compile \\[file][/]           - Compile only (e.g. compile C.cpp)")
    console.print("  [#00e5ff]addtest \\[prob][/]            - Add a custom test case via editor")
    console.print("  [#00e5ff]listtests \\[prob][/]          - List all test cases for a problem")
    console.print("  [#00e5ff]deltest \\[prob] \\[N][/]       - Delete test case N for a problem")
    console.print("  [#00e5ff]fetch \\[prob][/]             - Fetch tests (contest / gym / problemset)")
    console.print("  [#00e5ff]listen[/]                   - Start Competitive Companion listener")
    console.print("  [#00e5ff]history[/]                  - Show recent commands")
    console.print("  [#00e5ff]help[/]                     - Show detailed usage examples")
    console.print("  [#00e5ff]clear[/]                    - Clear screen and redraw dashboard")
    console.print("  [#00e5ff]quit / exit[/]              - Exit shell")
    console.print()


def parseFileAndProblem(args):
    """Parses arguments into (source_file, target_exe, prob_prefix)."""
    if len(args) == 0:
        return "Code.cpp", "Code", "CODE"
    elif len(args) == 1:
        # test F  ->  src/F.cpp, bin/F, problem F
        prob = args[0].upper()
        src = prob + ".cpp"
        return src, prob, prob
    else:
        # test F.cpp F  ->  src/F.cpp, bin/F, problem F
        src = args[0]
        if not src.endswith(".cpp"):
            src += ".cpp"
        prob = args[1].upper()
        target = src.replace(".cpp", "").upper()
        return src, target, prob


def openInVscode(filePath):
    """Open a file in VS Code (silent if 'code' CLI is unavailable)."""
    import shutil
    codePath = shutil.which("code")
    if codePath is None:
        console.print("[#ff9100]VS Code CLI ('code') not found in PATH.[/]")
        return
    subprocess.run([codePath, filePath], shell=(os.name == "nt"), check=False)


def mainLoop():
    # Make sure we are in the project root by going up if run inside scripts/
    if os.path.basename(os.getcwd()) == "scripts":
        os.chdir("..")

    # Load persisted history from previous sessions
    commandHistory.extend(_loadHistory())

    clearScreen()
    try:
        while True:
            printHeader()
            printStatus()

            cmdInput = Prompt.ask("[bold #ff9100]>[/]").strip()

            if not cmdInput:
                clearScreen()
                continue

            commandHistory.append(cmdInput)

            parts = cmdInput.split()
            action = parts[0].lower()
            args = parts[1:]

            # ── quit ────────────────────────────────────────────────────────────────
            if action in ["quit", "exit"]:
                break

            # ── clear ───────────────────────────────────────────────────────────────
            elif action == "clear":
                clearScreen()

            # ── history ─────────────────────────────────────────────────────────────
            elif action == "history":
                console.print("\n[bold #00e5ff]Recent Commands:[/]")
                recentCmds = commandHistory[-20:]
                for i, cmd in enumerate(recentCmds, 1):
                    console.print(f"  [#666666]{i:2}.[/] [#e0e0e0]{cmd}[/]")
                Prompt.ask("\n[#666666]Press Enter to continue...[/]")
                clearScreen()

            # ── help ────────────────────────────────────────────────────────────────
            elif action == "help":
                console.print("\n[bold #00e5ff]CodeRunner Interactive Shell Help[/]")
                console.print("\n[#00ff41]1. new \\[prob][/]")
                console.print("   Creates a fresh C++ file and opens it in VS Code. (e.g. [#e0e0e0]new C[/])")
                console.print("\n[#00ff41]2. open \\[prob][/]")
                console.print("   Opens the problem's C++ file in VS Code. (e.g. [#e0e0e0]open C[/] or just [#e0e0e0]open[/])")
                console.print("\n[#00ff41]3. run \\[file][/]")
                console.print("   Compiles a file and runs it against input.txt. No test comparison. (e.g. [#e0e0e0]run[/] or [#e0e0e0]run C[/])")
                console.print("\n[#00ff41]4. test \\[prob][/]")
                console.print("   Compiles src/C.cpp and runs it against tests for problem C. (e.g. [#e0e0e0]test C[/])")
                console.print("\n[#00ff41]5. test \\[file] \\[prob][/]")
                console.print("   Compiles a specific file and runs tests. (e.g. [#e0e0e0]test C.cpp C[/])")
                console.print("\n[#00ff41]6. debug \\[file] \\[prob][/]")
                console.print("   Same as test, but compiles with sanitizer flags. (e.g. [#e0e0e0]debug C.cpp C[/])")
                console.print("\n[#00ff41]7. compile \\[file][/]")
                console.print("   Just compiles a file without running tests. (e.g. [#e0e0e0]compile C.cpp[/])")
                console.print("\n[#00ff41]8. addtest \\[prob][/]")
                console.print("   Opens a textual editor to write a custom test case (input + expected output). (e.g. [#e0e0e0]addtest C[/])")
                console.print("\n[#00ff41]9. listtests \\[prob][/]")
                console.print("   Lists all test files for a problem with sizes and status. (e.g. [#e0e0e0]listtests C[/])")
                console.print("\n[#00ff41]10. deltest \\[prob] \\[N][/]")
                console.print("   Deletes test case N for a problem (with confirmation). (e.g. [#e0e0e0]deltest C 3[/])")
                console.print("\n[#00ff41]11. fetch \\[prob][/]")
                console.print("   Fetches sample tests interactively (contest/gym/problemset). (e.g. [#e0e0e0]fetch C[/])")
                console.print("\n[#00ff41]12. listen[/]")
                console.print("   Starts Competitive Companion listener to fetch tests from your browser.")
                console.print("\n[#00ff41]13. history[/]")
                console.print("   Shows a list of the last 20 commands you typed.")
                Prompt.ask("\n[#666666]Press Enter to continue...[/]")
                clearScreen()

            # ── new ─────────────────────────────────────────────────────────────────
            elif action == "new":
                if not args:
                    console.print("\n[bold #ff1744]Specify a problem (e.g., new C)[/]")
                else:
                    prob = args[0].upper()
                    cppFile = f"src/{prob}.cpp"

                    os.makedirs("src", exist_ok=True)
                    with open(cppFile, "w", encoding="utf-8") as f:
                        f.write(TEMPLATE)
                    console.print(f"\n[#00ff41]Created {cppFile} with template.[/]")

                    console.print(f"[#666666]Opening {cppFile} in VS Code...[/]")
                    openInVscode(cppFile)

                    # Offer to fetch sample tests immediately
                    fetchNow = Prompt.ask(
                        "\n[#00e5ff]Fetch sample tests now?[/]",
                        choices=["y", "n"],
                        default="n"
                    )
                    if fetchNow == "y":
                        # Only delete old tests when we are about to replace them
                        oldTests = glob.glob(f"tests/{prob}*")
                        for testFile in oldTests:
                            try:
                                os.remove(testFile)
                            except Exception:
                                pass
                        if oldTests:
                            console.print(f"[#666666]Deleted {len(oldTests)} old test files for {prob}.[/]")

                        fetchType = Prompt.ask(
                            "[#00e5ff]Fetch type[/]",
                            choices=["contest", "gym", "problemset"],
                            default="contest"
                        )
                        labelMap = {"contest": "Contest ID", "gym": "Gym ID", "problemset": "Problemset ID"}
                        fetchId = Prompt.ask(f"[#00e5ff]Enter {labelMap[fetchType]}[/]").strip()
                        if not fetchId:
                            console.print("\n[bold #ff1744]No ID provided. Skipping fetch.[/]")
                        else:
                            console.print(f"\n[#666666]Fetching {fetchType} {fetchId} problem {prob}...[/]")
                            makeVar = fetchType.upper()
                            subprocess.run(["make", "fetch", f"{makeVar}={fetchId}", f"PROBLEM={prob}"])

                Prompt.ask("\n[#666666]Press Enter to continue...[/]")
                clearScreen()

            # ── open ─────────────────────────────────────────────────────────────────
            elif action == "open":
                if not args:
                    prob = "Code"
                else:
                    prob = "Code" if args[0].lower() == "code" else args[0].upper()
                
                cppFile = f"src/{prob}.cpp"
                if os.path.exists(cppFile):
                    console.print(f"\n[#00ff41]Opening {cppFile}...[/]")
                    openInVscode(cppFile)
                else:
                    console.print(f"\n[bold #ff1744]{cppFile} not found.[/]")
                Prompt.ask("\n[#666666]Press Enter to continue...[/]")
                clearScreen()

            # ── run ─────────────────────────────────────────────────────────────
            elif action == "run":
                if not args:
                    src = "Code.cpp"
                    target = "Code"
                else:
                    src = args[0]
                    if not src.endswith(".cpp"):
                        src += ".cpp"
                    target = src.replace(".cpp", "")

                console.print(f"\n[#666666]Compiling src/{src}...[/]")
                res = subprocess.run(["make", "all", f"SRC=src/{src}", f"TARGET=bin/{target}"])
                if res.returncode != 0:
                    console.print("\n[bold #ff1744]Compilation failed.[/]")
                    Prompt.ask("\n[#666666]Press Enter to continue...[/]")
                    clearScreen()
                    continue

                if not os.path.exists("input.txt"):
                    console.print("[#ff9100]\u26a0 input.txt not found. Creating empty file.[/]")
                    open("input.txt", "w").close()

                exeName = f"bin/{target}"
                if os.name == "nt" and not exeName.endswith(".exe"):
                    if os.path.exists(exeName + ".exe"):
                        exeName += ".exe"

                console.print(f"\n[bold #00e5ff]\u25b6 Running[/] [#e0e0e0]{exeName}[/] [#666666](stdin ← input.txt)[/]\n")
                console.print(f"[#333333]{'\u2500' * 50}[/]")

                try:
                    with open("input.txt", "r", encoding="utf-8") as f:
                        inputData = f.read()

                    startTime = time.perf_counter()
                    proc = subprocess.Popen(
                        [exeName],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        encoding="utf-8",
                    )
                    stdout, stderr = proc.communicate(input=inputData)
                    elapsed = time.perf_counter() - startTime

                    if stdout:
                        console.print(stdout, end="", highlight=False)
                    if stderr:
                        console.print(f"\n[bold #ff9100]Stderr:[/]")
                        console.print(stderr, end="", highlight=False)

                    console.print(f"\n[#333333]{'\u2500' * 50}[/]")
                    exitStyle = "#00ff41" if proc.returncode == 0 else "#ff1744"
                    console.print(
                        f"[{exitStyle}]Exit {proc.returncode}[/]  "
                        f"[#666666]Time: [#e0e0e0]{elapsed:.3f}s[/][/]"
                    )

                except FileNotFoundError:
                    console.print(f"[bold #ff1744]Executable not found: {exeName}[/]")
                except Exception as e:
                    console.print(f"[bold #ff1744]Error: {e}[/]")

                Prompt.ask("\n[#666666]Press Enter to continue...[/]")
                clearScreen()

            # ── compile ─────────────────────────────────────────────────────────
            elif action == "compile":
                if not args:
                    console.print("\n[bold #ff1744]Specify a file to compile (e.g., compile F.cpp)[/]")
                else:
                    src = args[0]
                    # Ensure it has a .cpp extension so bare names like "F" also work
                    if not src.endswith(".cpp"):
                        src += ".cpp"
                    target = src.replace(".cpp", "")
                    console.print(f"\n[#666666]Compiling src/{src}...[/]")
                    res = subprocess.run(["make", "all", f"SRC=src/{src}", f"TARGET=bin/{target}"])
                    if res.returncode == 0:
                        console.print("\n[bold #00ff41]Compilation successful.[/]")
                    else:
                        console.print("\n[bold #ff1744]Compilation failed.[/]")
                Prompt.ask("\n[#666666]Press Enter to continue...[/]")
                clearScreen()

            # ── test / debug ─────────────────────────────────────────────────────────
            elif action in ["test", "debug"]:
                src, target, probPrefix = parseFileAndProblem(args)
                makeTarget = "debug" if action == "debug" else "all"

                console.print(f"\n[#666666]Compiling src/{src} ({makeTarget})...[/]")
                res = subprocess.run(["make", makeTarget, f"SRC=src/{src}", f"TARGET=bin/{target}"])
                if res.returncode != 0:
                    console.print("\n[bold #ff1744]Compilation failed. Aborting tests.[/]")
                    Prompt.ask("\n[#666666]Press Enter to continue...[/]")
                    clearScreen()
                    continue

                console.print(f"\n[#666666]Running tests for {probPrefix}...[/]")
                run_tests.runTestsForProblem(probPrefix, f"bin/{target}")

                Prompt.ask("\n[#666666]Press Enter to continue...[/]")
                clearScreen()

            # ── addtest ──────────────────────────────────────────────────────────────
            elif action == "addtest":
                try:
                    from test_editor import TestEditorApp
                except ModuleNotFoundError:
                    console.print("\n[bold #ff1744]✖ 'textual' is not installed in this environment.[/]")
                    console.print("[#666666]Run: [#e0e0e0]pip install textual[/][/]")
                    Prompt.ask("\n[#666666]Press Enter to continue...[/]")
                    clearScreen()
                    continue

                prob = args[0].upper() if args else "CODE"

                existingIns = glob.glob(f"tests/{prob}*.in")
                indices = []
                for inF in existingIns:
                    suffix = Path(inF).stem[len(prob):]
                    if suffix.isdigit():
                        indices.append(int(suffix))
                nextIdx = max(indices, default=0) + 1
                testName = f"{prob}{nextIdx}"

                console.print(f"\n[#00e5ff]Creating test case [bold]{testName}[/][/]")
                console.print(f"[#666666]Opening editor for input...  (Ctrl+S to save, Esc to cancel)[/]\n")

                inputApp = TestEditorApp(title=f"Input  →  {testName}.in")
                inputApp.run()

                if inputApp.result is None:
                    console.print("[#ff9100]Cancelled — no files written.[/]")
                    Prompt.ask("\n[#666666]Press Enter to continue...[/]")
                    clearScreen()
                    continue

                console.print(f"[#666666]Opening editor for expected output...  (Ctrl+S to save, Esc to cancel)[/]\n")

                outputApp = TestEditorApp(title=f"Expected Output  →  {testName}.out")
                outputApp.run()

                if outputApp.result is None:
                    console.print("[#ff9100]Cancelled — no files written.[/]")
                    Prompt.ask("\n[#666666]Press Enter to continue...[/]")
                    clearScreen()
                    continue

                os.makedirs("tests", exist_ok=True)
                inFile  = f"tests/{testName}.in"
                outFile = f"tests/{testName}.out"

                with open(inFile,  "w", encoding="utf-8") as f:
                    f.write(inputApp.result)
                with open(outFile, "w", encoding="utf-8") as f:
                    f.write(outputApp.result)

                console.print(f"\n[bold #00ff41]\u2714 Saved:[/] [#e0e0e0]{inFile}[/]  [#666666]&[/]  [#e0e0e0]{outFile}[/]")
                console.print(f"[#666666]Run [#00e5ff]test {prob}[/] to include this case in your test suite.[/]")
                Prompt.ask("\n[#666666]Press Enter to continue...[/]")
                clearScreen()

            # ── listtests ─────────────────────────────────────────────────────────────
            elif action == "listtests":
                prob = args[0].upper() if args else "CODE"
                inputFiles = sorted(glob.glob(f"tests/{prob}*.in"))

                if not inputFiles:
                    console.print(f"\n[#ff1744]No test files found for problem {prob}.[/]")
                else:
                    table = Table(
                        title=f"[bold #e0e0e0]Tests for Problem {prob}[/]",
                        border_style="#00e5ff",
                        header_style="bold #00e5ff",
                        box=box.SQUARE,
                    )
                    table.add_column("Test", style="bold #e0e0e0", width=12)
                    table.add_column("Input Size", justify="right", style="#84967e")
                    table.add_column(".out", justify="center", width=8)
                    table.add_column("Output Size", justify="right", style="#84967e")

                    for inPath in inputFiles:
                        stem    = Path(inPath).stem
                        outPath = f"tests/{stem}.out"
                        inSize  = f"{os.path.getsize(inPath)} B"
                        if os.path.exists(outPath):
                            outBadge = "[#00ff41]\u2714[/]"
                            outSize  = f"{os.path.getsize(outPath)} B"
                        else:
                            outBadge = "[#ff1744]\u2716 missing[/]"
                            outSize  = "—"
                        table.add_row(stem, inSize, outBadge, outSize)

                    console.print()
                    console.print(table)
                    console.print(f"[#666666]Tip: [#00e5ff]deltest {prob} <N>[/] removes a test case.[/]")

                Prompt.ask("\n[#666666]Press Enter to continue...[/]")
                clearScreen()

            # ── deltest ───────────────────────────────────────────────────────────────
            elif action == "deltest":
                if len(args) < 2:
                    console.print("\n[bold #ff1744]Usage: deltest <PROB> <N>  (e.g. [#e0e0e0]deltest C 3[/])[/]")
                else:
                    prob     = args[0].upper()
                    idx      = args[1]
                    testName = f"{prob}{idx}"
                    inFile   = f"tests/{testName}.in"
                    outFile  = f"tests/{testName}.out"

                    toDelete = [f for f in [inFile, outFile] if os.path.exists(f)]

                    if not toDelete:
                        console.print(f"\n[#ff1744]No files found for test [bold]{testName}[/].[/]")
                    else:
                        console.print(f"\n[#ff9100]About to delete:[/]")
                        for f in toDelete:
                            console.print(f"  [#e0e0e0]{f}[/]")

                        confirm = Prompt.ask(
                            "\n[bold #ff9100]Are you sure?[/]",
                            choices=["y", "n"],
                            default="n"
                        )
                        if confirm == "y":
                            for f in toDelete:
                                os.remove(f)
                            console.print(f"[#00ff41]\u2714 Deleted {len(toDelete)} file(s).[/]")
                        else:
                            console.print("[#666666]Cancelled.[/]")

                Prompt.ask("\n[#666666]Press Enter to continue...[/]")
                clearScreen()

            # ── fetch ─────────────────────────────────────────────────────────────────
            elif action == "fetch":
                if not args:
                    console.print("\n[bold #ff1744]Specify a problem (e.g., fetch C)[/]")
                    Prompt.ask("\n[#666666]Press Enter to continue...[/]")
                    clearScreen()
                    continue

                prob = args[0].upper()
                fetchType = Prompt.ask(
                    "[#00e5ff]Fetch type[/]",
                    choices=["contest", "gym", "problemset"],
                    default="contest"
                )

                labelMap = {"contest": "Contest ID", "gym": "Gym ID", "problemset": "Problemset ID"}
                fetchId = Prompt.ask(f"[#00e5ff]Enter {labelMap[fetchType]}[/]").strip()

                if not fetchId:
                    console.print("\n[bold #ff1744]No ID provided. Aborting.[/]")
                else:
                    console.print(f"\n[#666666]Fetching {fetchType} {fetchId} problem {prob}...[/]")
                    makeVar = fetchType.upper()  # CONTEST=, GYM=, PROBLEMSET=
                    subprocess.run(["make", "fetch", f"{makeVar}={fetchId}", f"PROBLEM={prob}"])

                Prompt.ask("\n[#666666]Press Enter to continue...[/]")
                clearScreen()

            # ── listen ────────────────────────────────────────────────────────────────
            elif action == "listen":
                console.print("\n[#666666]Starting Competitive Companion listener on port 10043...[/]")
                console.print("[#666666]Press Ctrl+C to stop.[/]\n")
                try:
                    subprocess.run(["make", "listen"])
                except KeyboardInterrupt:
                    pass
                Prompt.ask("\n[#666666]Press Enter to continue...[/]")
                clearScreen()

            # ── unknown ───────────────────────────────────────────────────────────────
            else:
                console.print(f"\n[bold #ff1744]Unknown command: {action}[/]")
                Prompt.ask("\n[#666666]Press Enter to continue...[/]")
                clearScreen()

    except (KeyboardInterrupt, EOFError):
        console.print("\n[#00e5ff]Exiting CodeRunner...[/]")
    finally:
        _saveHistory()


if __name__ == "__main__":
    mainLoop()
