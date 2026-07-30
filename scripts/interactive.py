"""
Interactive Terminal UI for CodeRunner.
Acts as a continuous shell to compile, fetch, and test problems without re-typing make commands.
"""
import os
import sys
import glob
import subprocess
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
    console.print("  [#00e5ff]new \\[prob][/]          - Create src/\\[prob].cpp from template & clean old tests")
    console.print("  [#00e5ff]open \\[prob][/]         - Open src/\\[prob].cpp in VS Code")
    console.print("  [#00e5ff]test \\[prob][/]         - Compile src/\\[prob].cpp & run tests for \\[prob]")
    console.print("  [#00e5ff]test \\[file] \\[prob][/]  - Compile src/\\[file] & run tests for \\[prob]")
    console.print("  [#00e5ff]debug \\[file] \\[prob][/] - Compile with sanitizers & run tests")
    console.print("  [#00e5ff]compile \\[file][/]      - Compile only (e.g. compile C.cpp)")
    console.print("  [#00e5ff]fetch \\[prob][/]        - Fetch tests (contest / gym / problemset)")
    console.print("  [#00e5ff]listen[/]              - Start Competitive Companion listener")
    console.print("  [#00e5ff]history[/]             - Show recent commands")
    console.print("  [#00e5ff]help[/]                - Show detailed usage examples")
    console.print("  [#00e5ff]clear[/]               - Clear screen and redraw dashboard")
    console.print("  [#00e5ff]quit / exit[/]         - Exit shell")
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
                console.print("\n[#00ff41]3. test \\[prob][/]")
                console.print("   Compiles src/C.cpp and runs it against tests for problem C. (e.g. [#e0e0e0]test C[/])")
                console.print("\n[#00ff41]4. test \\[file] \\[prob][/]")
                console.print("   Compiles a specific file and runs tests. (e.g. [#e0e0e0]test C.cpp C[/])")
                console.print("\n[#00ff41]5. debug \\[file] \\[prob][/]")
                console.print("   Same as test, but compiles with sanitizer flags. (e.g. [#e0e0e0]debug C.cpp C[/])")
                console.print("\n[#00ff41]6. compile \\[file][/]")
                console.print("   Just compiles a file without running tests. (e.g. [#e0e0e0]compile C.cpp[/])")
                console.print("\n[#00ff41]7. fetch \\[prob][/]")
                console.print("   Fetches sample tests interactively (contest/gym/problemset). (e.g. [#e0e0e0]fetch C[/])")
                console.print("\n[#00ff41]8. listen[/]")
                console.print("   Starts Competitive Companion listener to fetch tests from your browser.")
                console.print("\n[#00ff41]9. history[/]")
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
