"""
Textual-based editor popup for creating custom test cases.
Spawned by the addtest command in interactive.py.
"""

from textual.app import App, ComposeResult
from textual.widgets import TextArea, Label
from textual.binding import Binding


class TestEditorApp(App):
    """
    Full-screen editor for writing a single block of text (test input or expected output).
    After app.run(), check app.result:
      - str  -> user saved content
      - None -> user cancelled
    """

    CSS = """
    Screen {
        background: #0a0a0a;
        align: center middle;
    }

    #title-bar {
        background: #111111;
        border: solid #00e5ff;
        color: #00e5ff;
        text-style: bold;
        padding: 0 2;
        height: 3;
        content-align: center middle;
        width: 80%;
    }

    #editor {
        height: auto;
        max-height: 50%;
        min-height: 5;
        border: solid #333333;
        background: #111111;
        width: 80%;
    }

    #editor:focus {
        border: solid #00e5ff;
    }

    #footer-bar {
        dock: bottom;
        height: 1;
        background: #111111;
        color: #00e5ff;
        padding: 0 2;
    }
    """

    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        Binding("ctrl+s", "save", "Save & Continue", show=True, priority=True),
        Binding("ctrl+c", "cancel", "Cancel", show=False, priority=True),
        Binding("escape", "cancel", "Cancel", show=True),
    ]

    def __init__(self, title: str, **kwargs):
        super().__init__(**kwargs)
        self.editorTitle = title
        self.result: str | None = None

    def compose(self) -> ComposeResult:
        yield Label(f"  \u270e  {self.editorTitle}", id="title-bar")
        yield TextArea("", id="editor")
        yield Label("  Ctrl+S → Save & Continue   •   Esc → Cancel", id="footer-bar")

    def on_mount(self) -> None:
        self.query_one("#editor", TextArea).focus()

    def action_save(self) -> None:
        self.result = self.query_one("#editor", TextArea).text
        self.exit()

    def action_cancel(self) -> None:
        self.result = None
        self.exit()
