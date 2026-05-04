import sys
import os
import subprocess
import json

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLineEdit, QLabel, QFileDialog,
    QFrame, QDialog, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

# Project root directory
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ─── Worker: runs run_qa.py in a separate process ──────────────────────────────
class QAWorker(QThread):
    result_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, question):
        super().__init__()
        self.question = question

    def run(self):
        try:
            result = subprocess.run(
                [sys.executable, os.path.join(ROOT, "run_qa.py"), self.question],
                capture_output=True,
                text=True,
                cwd=ROOT
            )
            # Find the JSON line — it's the last non-empty line
            lines = [l.strip() for l in result.stdout.strip().splitlines() if l.strip()]
            json_line = None
            for line in reversed(lines):
                if line.startswith("{"):
                    json_line = line
                    break

            if json_line:
                data = json.loads(json_line)
                self.result_ready.emit(data)
            else:
                err = result.stderr.strip() or result.stdout.strip() or "No response from QA engine."
                self.error_occurred.emit(err)
        except Exception as e:
            self.error_occurred.emit(str(e))


# ─── Worker: runs file loading in a separate process ──────────────────────────
class LoadWorker(QThread):
    done = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, mode, files):
        super().__init__()
        self.mode = mode  # "evtx" or "registry"
        self.files = files

    def run(self):
        try:
            script = os.path.join(ROOT, "run_load.py")
            result = subprocess.run(
                [sys.executable, script, self.mode] + self.files,
                capture_output=True,
                text=True,
                cwd=ROOT
            )
            if result.returncode == 0:
                lines = [l.strip() for l in result.stdout.strip().splitlines() if l.strip()]
                self.done.emit(lines[-1] if lines else "Done.")
            else:
                self.error.emit(result.stderr.strip() or "Unknown error during loading.")
        except Exception as e:
            self.error.emit(str(e))


# ─── Evidence popup ────────────────────────────────────────────────────────────
class EvidenceDialog(QDialog):
    def __init__(self, ref_id, meta, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Evidence — {ref_id}")
        self.setMinimumSize(600, 350)
        layout = QVBoxLayout()
        self.setLayout(layout)

        text = QTextEdit()
        text.setReadOnly(True)
        text.setFont(QFont("Consolas", 10))

        if meta.get("type") == "event":
            content = (
                f"Type      : Windows Event Log\n"
                f"EventID   : {meta.get('event_id', 'N/A')}\n"
                f"Timestamp : {meta.get('timestamp', 'N/A')}\n"
                f"Source    : {meta.get('source', 'N/A')}\n"
                f"Computer  : {meta.get('computer', 'N/A')}\n"
                f"Level     : {meta.get('level', 'N/A')}\n"
                f"Log File  : {meta.get('file_source', 'N/A')}\n"
                f"DB ID     : {meta.get('db_id', 'N/A')}\n"
            )
        else:
            content = (
                f"Type      : Windows Registry\n"
                f"Hive      : {meta.get('hive', 'N/A')}\n"
                f"Key Path  : {meta.get('key_path', 'N/A')}\n"
                f"Value     : {meta.get('value_name', 'N/A')}\n"
                f"Data      : {meta.get('value_data', 'N/A')}\n"
                f"Hive File : {meta.get('file_source', 'N/A')}\n"
                f"DB ID     : {meta.get('db_id', 'N/A')}\n"
            )
        text.setPlainText(content)
        layout.addWidget(text)

        btn = QPushButton("Close")
        btn.clicked.connect(self.close)
        layout.addWidget(btn)


# ─── Main Window ───────────────────────────────────────────────────────────────
class ForensicsChatbot(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Windows Forensics AI Chatbot")
        self.setMinimumSize(900, 700)
        self.session_log = []
        self.worker = None
        self.load_worker = None
        self._build_ui()
        self._apply_styles()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        # Title
        title = QLabel("🔍  Windows Forensics AI Chatbot")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Buttons row
        btn_frame = QFrame()
        btn_frame.setFrameShape(QFrame.StyledPanel)
        btn_layout = QHBoxLayout(btn_frame)

        self.evtx_btn = QPushButton("📂  Load Event Logs (.evtx)")
        self.evtx_btn.setFixedHeight(36)
        self.evtx_btn.clicked.connect(self.load_evtx)

        self.reg_btn = QPushButton("📂  Load Registry Hives")
        self.reg_btn.setFixedHeight(36)
        self.reg_btn.clicked.connect(self.load_registry)

        self.export_btn = QPushButton("📄  Export PDF Report")
        self.export_btn.setFixedHeight(36)
        self.export_btn.clicked.connect(self.export_report)

        btn_layout.addWidget(self.evtx_btn)
        btn_layout.addWidget(self.reg_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.export_btn)
        layout.addWidget(btn_frame)

        # Status
        self.status_label = QLabel("Status: Ready. Ask a question or load new files.")
        self.status_label.setFont(QFont("Segoe UI", 9))
        self.status_label.setStyleSheet("color: #888; padding: 2px 4px;")
        layout.addWidget(self.status_label)

        # Chat area
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setFont(QFont("Segoe UI", 10))
        self.chat_area.setMinimumHeight(400)
        self.chat_area.setPlaceholderText("Chat history will appear here...")
        layout.addWidget(self.chat_area)

        # Input row
        input_frame = QFrame()
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(0, 0, 0, 0)

        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Ask an investigation question...")
        self.input_box.setFixedHeight(38)
        self.input_box.setFont(QFont("Segoe UI", 10))
        self.input_box.returnPressed.connect(self.send_question)

        self.send_btn = QPushButton("Send ➤")
        self.send_btn.setFixedSize(90, 38)
        self.send_btn.clicked.connect(self.send_question)

        input_layout.addWidget(self.input_box)
        input_layout.addWidget(self.send_btn)
        layout.addWidget(input_frame)

        self.statusBar().showMessage("Ready")

    def _apply_styles(self):
        self.setStyleSheet("""
            QMainWindow, QWidget { background-color: #1e1e2e; color: #cdd6f4; }
            QFrame { background-color: #181825; border-radius: 6px; padding: 4px; }
            QPushButton {
                background-color: #313244; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 5px;
                padding: 4px 12px; font-size: 10pt;
            }
            QPushButton:hover { background-color: #45475a; }
            QPushButton:disabled { background-color: #282838; color: #555; }
            QTextEdit {
                background-color: #181825; border: 1px solid #313244;
                border-radius: 6px; padding: 8px; color: #cdd6f4;
            }
            QLineEdit {
                background-color: #181825; border: 1px solid #313244;
                border-radius: 5px; padding: 4px 10px; color: #cdd6f4;
            }
            QLineEdit:focus { border: 1px solid #89b4fa; }
            QStatusBar { color: #888; font-size: 9pt; }
        """)
        self.send_btn.setStyleSheet("""
            QPushButton { background-color: #89b4fa; color: #1e1e2e; font-weight: bold; border-radius: 5px; }
            QPushButton:hover { background-color: #b4befe; }
            QPushButton:disabled { background-color: #444; color: #888; }
        """)
        self.export_btn.setStyleSheet("""
            QPushButton { background-color: #a6e3a1; color: #1e1e2e; font-weight: bold; border-radius: 5px; }
            QPushButton:hover { background-color: #94e2d5; }
        """)

    # ── File loading (via subprocess to avoid DLL conflict) ────────────────────
    def load_evtx(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Event Log Files", "", "Event Log Files (*.evtx);;All Files (*)"
        )
        if not files:
            return
        self._set_loading(True, f"Parsing {len(files)} event log file(s)...")
        self.load_worker = LoadWorker("evtx", files)
        self.load_worker.done.connect(lambda msg: self._on_load_done(msg))
        self.load_worker.error.connect(lambda err: self._on_load_error(err))
        self.load_worker.start()

    def load_registry(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Registry Hive Files", "", "All Files (*)"
        )
        if not files:
            return
        self._set_loading(True, f"Parsing {len(files)} registry hive(s)...")
        self.load_worker = LoadWorker("registry", files)
        self.load_worker.done.connect(lambda msg: self._on_load_done(msg))
        self.load_worker.error.connect(lambda err: self._on_load_error(err))
        self.load_worker.start()

    def _on_load_done(self, msg):
        self._set_loading(False, f"✅ {msg}")
        self._append_system(f"✅ {msg}")

    def _on_load_error(self, err):
        self._set_loading(False, f"❌ {err}")
        self._append_system(f"❌ Error loading files: {err}")

    def _set_loading(self, loading, status_msg):
        self.evtx_btn.setEnabled(not loading)
        self.reg_btn.setEnabled(not loading)
        self.status_label.setText(f"Status: {status_msg}")
        self.statusBar().showMessage(status_msg)

    # ── Q&A ────────────────────────────────────────────────────────────────────
    def send_question(self):
        question = self.input_box.text().strip()
        if not question:
            return
        self.input_box.clear()
        self.send_btn.setEnabled(False)
        self.input_box.setEnabled(False)
        self.statusBar().showMessage("Thinking...")
        self._append_question(question)

        self.worker = QAWorker(question)
        self.worker.result_ready.connect(self.on_answer_ready)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.start()

    def on_answer_ready(self, result):
        self._append_answer(result.get("answer", ""), result.get("references", []))
        self.session_log.append(result)
        self.send_btn.setEnabled(True)
        self.input_box.setEnabled(True)
        self.input_box.setFocus()
        self.statusBar().showMessage(f"Ready — {len(self.session_log)} question(s) this session")

    def on_error(self, error_msg):
        self._append_system(f"❌ Error: {error_msg}")
        self.send_btn.setEnabled(True)
        self.input_box.setEnabled(True)
        self.statusBar().showMessage("Error occurred")

    # ── Chat rendering ─────────────────────────────────────────────────────────
    def _append_question(self, question):
        self.chat_area.append(
            f'<p style="color:#89b4fa;font-weight:bold;margin-top:12px;">🔎 Investigator: {question}</p>'
        )

    def _append_answer(self, answer, references):
        answer_html = answer.replace("\n", "<br/>")
        self.chat_area.append(
            f'<p style="color:#cdd6f4;margin-left:12px;">🤖 <b>AI Analysis:</b><br/>{answer_html}</p>'
        )
        if references:
            refs_html = '<p style="margin-left:12px;">'
            for ref in references:
                refs_html += (
                    f'<span style="color:#a6e3a1;">'
                    f'📎 {ref["ref_id"]} → {ref["type"].upper()} | DB ID: {ref["db_id"]}'
                    f'</span><br/>'
                )
            refs_html += '</p>'
            self.chat_area.append(refs_html)
        self.chat_area.append('<hr style="border-color:#313244;"/>')

    def _append_system(self, message):
        self.chat_area.append(
            f'<p style="color:#f38ba8;font-style:italic;">{message}</p>'
        )

    # ── PDF Export ─────────────────────────────────────────────────────────────
    def export_report(self):
        if not self.session_log:
            QMessageBox.warning(self, "No Data", "Ask some questions first before exporting.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF Report", "forensic_report.pdf", "PDF Files (*.pdf)"
        )
        if not path:
            return
        try:
            from reporter.pdf_report import generate_report
            generate_report(self.session_log, path)
            QMessageBox.information(self, "Success", f"Report saved to:\n{path}")
            self.statusBar().showMessage(f"Report exported: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Error:\n{e}")


def launch():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = ForensicsChatbot()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    launch()