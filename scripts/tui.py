"""
Terminal UI module for the competitive programming test runner.
Sleek, minimal, cyber-circuit aesthetic.
"""
import sys
import difflib

VERSION = "1.0"

try:
    from rich.console import Console
    from rich.text import Text
    from rich.panel import Panel
    from rich.table import Table
    from rich.live import Live
    from rich import box
except ImportError:
    print("Error: The 'rich' library is required for the TUI.")
    print("Please install it using: pip install rich")
    sys.exit(1)


def formatMemory(bytesVal):
    if bytesVal <= 0:
        return "N/A"
    elif bytesVal < 1024:
        return f"{bytesVal} B"
    elif bytesVal < 1024 * 1024:
        return f"{bytesVal / 1024:.2f} KB"
    else:
        return f"{bytesVal / (1024 * 1024):.2f} MB"


class TestReporter:
    def __init__(self, hasPsutil=True):
        self.console = Console()
        self.hasPsutil = hasPsutil
        self.passed = 0
        self.failed = 0
        self.total = 0
        self.panelsToPrint = []
        self.results = []
        self.currentTest = None
        self.currentTime = 0.0
        self.currentMemory = 0
        self.live = None

    def printInfo(self, msg):
        self.console.print(f"[#666666]{msg}[/]")

    def printWarning(self, msg):
        self.console.print(f"[bold #ff9100]⚠ {msg}[/]")

    def printError(self, msg):
        self.console.print(f"[bold #ff1744]✖ {msg}[/]")

    def printHeader(self, problem):
        self.console.print()
        self.console.print(f"[bold #00e5ff]CODE_RUNNER_v{VERSION} - RUNNING: Problem {problem}[/]")
        self.console.print(f"[#666666]" + "—" * 40 + "[/]")

    def startTests(self, totalTests):
        self.total = totalTests
        self.passed = 0
        self.failed = 0
        self.results = []
        self.panelsToPrint = []
        self.currentTest = None
        self.currentTime = 0.0
        self.currentMemory = 0
        self.live = Live(self._generateTable(), refresh_per_second=10, console=self.console)
        self.live.start()

    def updateLiveTest(self, testCase, execTime, memory):
        self.currentTest = testCase
        self.currentTime = execTime
        self.currentMemory = memory
        if self.live:
            self.live.update(self._generateTable())

    def updateProgress(self, execTime, memory):
        """Update elapsed time during polling; auto_refresh (10 fps) handles display."""
        self.currentTime = execTime
        self.currentMemory = memory

    def _timeStyle(self, execTime, timeout, success):
        """Return a color based on how close execTime is to the timeout limit."""
        if not success:
            return "#ff1744"
        ratio = execTime / timeout if timeout > 0 else 0
        if ratio >= 1.0:
            return "#ff1744"
        elif ratio >= 0.5:
            return "#ff9100"
        else:
            return "#666666"

    def _generateTable(self):
        table = Table(
            title="[bold #e0e0e0]Test Execution Dashboard[/]",
            border_style="#00e5ff",
            header_style="bold #00e5ff",
            box=box.SQUARE
        )
        table.add_column("Status", width=12, justify="center")
        table.add_column("Test Case", style="bold #e0e0e0")
        table.add_column("Time", justify="right")
        table.add_column("Memory", justify="right", style="#e0e0e0")
        table.add_column("Details")

        for success, testCase, execTime, timeout, message, memory in self.results:
            timeStr = f"{execTime:.3f}s"
            memStr = formatMemory(memory) if self.hasPsutil else "N/A"
            timeStyle = self._timeStyle(execTime, timeout, success)
            if success:
                statusStr = "[bold #0a0a0a on #00ff41] PASS [/]"
                msgStyle = "#00ff41"
            else:
                statusStr = "[bold #e0e0e0 on #ff1744] FAIL [/]"
                msgStyle = "#ff1744"

            table.add_row(
                statusStr,
                testCase,
                f"[{timeStyle}]{timeStr}[/]",
                memStr,
                f"[{msgStyle}]{message}[/]"
            )

        if self.currentTest:
            timeStr = f"{self.currentTime:.3f}s"
            memStr = formatMemory(self.currentMemory) if self.hasPsutil else "N/A"
            statusStr = "[bold #0a0a0a on #ff9100] RUNNING [/]"
            table.add_row(
                statusStr,
                self.currentTest,
                f"[#ff9100]{timeStr}[/]",
                memStr,
                "[#ff9100]Executing...[/]"
            )

        return table

    def _buildWrongAnswerPanel(self, expected, actual):
        expectedLines = expected.split('\n')
        actualLines = actual.split('\n')

        table = Table(
            title="[bold #e0e0e0]Side-by-Side Diff[/]",
            border_style="#00e5ff",
            box=box.SQUARE,
            expand=True
        )
        table.add_column("Expected Output", style="#84967e")
        table.add_column("Your Output", style="#ffb4ab")

        maxLines = max(len(expectedLines), len(actualLines))

        for i in range(maxLines):
            expLine = expectedLines[i] if i < len(expectedLines) else ""
            actLine = actualLines[i] if i < len(actualLines) else ""

            expText = Text()
            actText = Text()

            if expLine == actLine:
                expText.append(expLine, style="#84967e")
                actText.append(actLine, style="#ffb4ab")
            else:
                sm = difflib.SequenceMatcher(None, expLine, actLine)
                for tag, i1, i2, j1, j2 in sm.get_opcodes():
                    if tag == 'equal':
                        expText.append(expLine[i1:i2], style="#84967e")
                        actText.append(actLine[j1:j2], style="#ffb4ab")
                    elif tag == 'delete':
                        expText.append(expLine[i1:i2], style="bold #0a0a0a on #00ff41")
                    elif tag == 'insert':
                        actText.append(actLine[j1:j2], style="bold #e0e0e0 on #ff1744")
                    elif tag == 'replace':
                        expText.append(expLine[i1:i2], style="bold #0a0a0a on #00ff41")
                        actText.append(actLine[j1:j2], style="bold #e0e0e0 on #ff1744")

            table.add_row(expText, actText)

        return table

    def _printTimingSummary(self):
        """Print fastest / slowest / average timing across all tests."""
        if not self.results:
            return
        times = [execTime for _, _, execTime, _, _, _ in self.results]
        names = [testCase for _, testCase, _, _, _, _ in self.results]
        fastest = min(times)
        slowest = max(times)
        avg = sum(times) / len(times)
        fastestName = names[times.index(fastest)]
        slowestName = names[times.index(slowest)]
        self.console.print(
            f"[#666666]Fastest: [#00ff41]{fastest:.3f}s[/] ({fastestName})  "
            f"Slowest: [#ff9100]{slowest:.3f}s[/] ({slowestName})  "
            f"Avg: [#e0e0e0]{avg:.3f}s[/][/]"
        )

    def addResult(self, testCase, success, execTime, timeout, message, memory=0, details=None):
        self.currentTest = None
        self.results.append((success, testCase, execTime, timeout, message, memory))

        if success:
            self.passed += 1
        else:
            self.failed += 1

        errorPanel = None
        if not success:
            if details and "expected" in details and "actual" in details:
                errorPanel = self._buildWrongAnswerPanel(details["expected"], details["actual"])
            elif details and "error" in details:
                errorPanel = Panel(
                    str(details["error"]),
                    title="[bold #ff1744]Error[/]",
                    border_style="#ff1744",
                    expand=False,
                    box=box.SQUARE
                )

        # Show stderr for both PASS and FAIL — useful for sanitizer/debug output
        stderrPanel = None
        if details and "stderr" in details and details["stderr"].strip():
            stderrPanel = Panel(
                Text.from_ansi(details["stderr"].strip()),
                title="[bold #ff9100]Stderr[/]",
                border_style="#ff9100",
                expand=False,
                box=box.SQUARE
            )

        if errorPanel:
            self.panelsToPrint.append((testCase, errorPanel))
        if stderrPanel:
            self.panelsToPrint.append((testCase, stderrPanel))

        if self.live:
            self.live.update(self._generateTable())

    def stopTests(self):
        if self.live:
            self.live.stop()
            self.live = None

        self.console.print(f"[#666666]" + "—" * 40 + "[/]")

        for testCase, panel in self.panelsToPrint:
            self.console.print(f"[bold #00e5ff]Details for {testCase}:[/]")
            self.console.print(panel)
            self.console.print()

        self._printTimingSummary()

        if self.passed == self.total and self.total > 0:
            self.console.print(f"[bold #0a0a0a on #00ff41] ✔ All {self.total} tests passed! [/]")
        else:
            self.console.print(
                f"[bold #e0e0e0 on #ff1744] ✖ {self.failed} failed [/] "
                f"[bold #0a0a0a on #00ff41] ✔ {self.passed} passed [/] "
                f"[bold #0a0a0a on #e0e0e0] {self.total} total [/]"
            )
        self.console.print()
