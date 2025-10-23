import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Optional

# ADD THESE LINES FOR TASKBAR ICON FIX
import ctypes
try:
    # Tell Windows this is a unique app (not Python)
    myappid = 'saikatmajumder.internetspeedtest.1.0'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except:
    pass
# END OF ICON FIX

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QFrame, QMessageBox, QScrollArea
)

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QPainter, QLinearGradient, QColor, QIcon, QImage
import speedtest

# Constants
DEFAULT_HISTORY_FILE = "speed_test_history.json"
DEFAULT_LOGO_PATH = "logo.png"
THEMES = {
    "Dark": {"fg": "#FFFFFF", "accent": "#00BFFF", "bg1": "#141E30", "bg2": "#243B55"},
    "Light": {"fg": "#000000", "accent": "#0078D7", "bg1": "#89f7fe", "bg2": "#66a6ff"}
}

def format_speed(speed_bps: float) -> str:
    """Format speed in appropriate unit (bps, Kbps, Mbps, Gbps)."""
    if speed_bps >= 1_000_000_000:  # >= 1 Gbps
        return f"{speed_bps / 1_000_000_000:.2f} Gbps"
    elif speed_bps >= 1_000_000:  # >= 1 Mbps
        return f"{speed_bps / 1_000_000:.2f} Mbps"
    elif speed_bps >= 1_000:  # >= 1 Kbps
        return f"{speed_bps / 1_000:.2f} Kbps"
    else:
        return f"{speed_bps:.2f} bps"

def get_speed_value_for_history(speed_bps: float) -> float:
    """Return speed in Mbps for history storage."""
    return speed_bps / 1_000_000

def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and PyInstaller."""
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class SpeedTestThread(QThread):
    """Thread for running speed tests without blocking UI."""
    status_update = pyqtSignal(str)
    server_update = pyqtSignal(str)
    download_update = pyqtSignal(float)
    upload_update = pyqtSignal(float)
    ping_update = pyqtSignal(float)
    progress_update = pyqtSignal(int)
    test_complete = pyqtSignal(dict)
    test_error = pyqtSignal(str)

    def run(self):
        try:
            self.status_update.emit("Initializing speed test...")
            self.progress_update.emit(0)

            st = speedtest.Speedtest()

            self.status_update.emit("Finding best server...")
            self.progress_update.emit(10)
            st.get_best_server()

            server_info = f"Server: {st.best['sponsor']} ({st.best['country']})"
            self.server_update.emit(server_info)
            self.progress_update.emit(20)

            # Download test
            self.status_update.emit("Testing download speed...")
            self.progress_update.emit(30)
            download_speed = st.download()
            self.download_update.emit(download_speed)
            self.progress_update.emit(60)

            # Upload test
            self.status_update.emit("Testing upload speed...")
            self.progress_update.emit(70)
            upload_speed = st.upload()
            self.upload_update.emit(upload_speed)
            self.progress_update.emit(90)

            # Ping
            ping = st.results.ping
            self.ping_update.emit(ping)
            self.progress_update.emit(100)

            # Complete
            test_data = {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "time": datetime.now().strftime("%H:%M:%S"),
                "download": download_speed,
                "upload": upload_speed,
                "ping": ping
            }
            self.test_complete.emit(test_data)
            self.status_update.emit("✅ Test Completed Successfully")

        except speedtest.ConfigRetrievalError:
            self.test_error.emit("Failed to retrieve speedtest configuration. Please check your internet connection.")
            self.status_update.emit("❌ Configuration Error")
        except speedtest.NoMatchedServers:
            self.test_error.emit("No speedtest servers found. Please check your internet connection.")
            self.status_update.emit("❌ No Servers Found")
        except Exception as e:
            self.test_error.emit(f"Test failed: {str(e)}\n\nPlease check:\n- Internet connection\n- Firewall settings\n- VPN configuration")
            self.status_update.emit("❌ Test Failed")
        finally:
            self.progress_update.emit(0)

class SpeedTestApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Internet Speed Test")
        self.setMinimumSize(500, 650)
        self.resize(500, 650)

        # State
        self.current_theme = "Dark"
        self.test_history: List[Dict] = []
        self.history_file = DEFAULT_HISTORY_FILE
        self.speed_test_thread: Optional[SpeedTestThread] = None
        self.original_pixmap: Optional[QPixmap] = None

        # Setup
        self.load_history()
        self.load_icon()
        self.setup_ui()
        self.apply_theme()

        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)

    def invert_logo_colors(self, pixmap: QPixmap) -> QPixmap:
        """Invert the colors of the logo pixmap."""
        image = pixmap.toImage()
        image.invertPixels()
        return QPixmap.fromImage(image)

    def update_logo_pixmap(self):
        """Update the logo pixmap based on the current theme."""
        if hasattr(self, 'original_pixmap') and self.original_pixmap:
            if self.current_theme == "Dark":
                pixmap = self.original_pixmap
            else:
                pixmap = self.invert_logo_colors(self.original_pixmap)

            scaled_pixmap = pixmap.scaled(
                100, 100,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.logo_label.setPixmap(scaled_pixmap)
            self.logo_label.setStyleSheet("")

    def load_logo_image(self):
        """Load logo image from file."""
        logo_path = get_resource_path(DEFAULT_LOGO_PATH)
        if os.path.exists(logo_path):
            try:
                pixmap = QPixmap(logo_path)
                if not pixmap.isNull():
                    self.original_pixmap = pixmap
                    self.update_logo_pixmap()
            except Exception as e:
                print(f"Error loading logo image: {e}")

    def load_icon(self):
        """Load application icon."""
        logo_path = get_resource_path(DEFAULT_LOGO_PATH)
        if os.path.exists(logo_path):
            try:
                icon = QIcon(logo_path)
                self.setWindowIcon(icon)
                QApplication.setWindowIcon(icon)
            except Exception as e:
                print(f"Error loading icon: {e}")

    def setup_ui(self):
        """Setup the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)

        # Logo
        self.logo_label = QLabel("🌐")
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setStyleSheet("font-size: 60px;")
        main_layout.addWidget(self.logo_label)

        # Title
        self.title_label = QLabel("Internet Speed Test")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        main_layout.addWidget(self.title_label)

        # Clock
        self.clock_label = QLabel()
        self.clock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.clock_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        main_layout.addWidget(self.clock_label)

        # Server info
        self.server_label = QLabel("")
        self.server_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.server_label.setStyleSheet("font-size: 10px;")
        main_layout.addWidget(self.server_label)

        # Info frame
        info_frame = QFrame()
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(10)

        # Download
        download_layout = QHBoxLayout()
        self.download_label = QLabel("Download Speed:")
        self.download_value = QLabel("-- Mbps")
        self.download_value.setStyleSheet("font-weight: bold;")
        download_layout.addWidget(self.download_label)
        download_layout.addStretch()
        download_layout.addWidget(self.download_value)
        info_layout.addLayout(download_layout)

        # Upload
        upload_layout = QHBoxLayout()
        self.upload_label = QLabel("Upload Speed:")
        self.upload_value = QLabel("-- Mbps")
        self.upload_value.setStyleSheet("font-weight: bold;")
        upload_layout.addWidget(self.upload_label)
        upload_layout.addStretch()
        upload_layout.addWidget(self.upload_value)
        info_layout.addLayout(upload_layout)

        # Ping
        ping_layout = QHBoxLayout()
        self.ping_label = QLabel("Ping:")
        self.ping_value = QLabel("-- ms")
        self.ping_value.setStyleSheet("font-weight: bold;")
        ping_layout.addWidget(self.ping_label)
        ping_layout.addStretch()
        ping_layout.addWidget(self.ping_value)
        info_layout.addLayout(ping_layout)

        main_layout.addWidget(info_frame)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        main_layout.addWidget(self.progress_bar)

        # Buttons
        button_layout = QHBoxLayout()

        self.test_button = QPushButton("Start Test")
        self.test_button.clicked.connect(self.start_test)
        self.test_button.setToolTip("Start a new speed test")
        button_layout.addWidget(self.test_button)

        self.cancel_button = QPushButton("Cancel Test")
        self.cancel_button.clicked.connect(self.cancel_test)
        self.cancel_button.setEnabled(False)
        self.cancel_button.setToolTip("Cancel the ongoing test")
        button_layout.addWidget(self.cancel_button)

        self.theme_button = QPushButton("Switch to Light Theme")
        self.theme_button.clicked.connect(self.toggle_theme)
        self.theme_button.setToolTip("Toggle between dark and light themes")
        button_layout.addWidget(self.theme_button)

        self.clear_button = QPushButton("Clear History")
        self.clear_button.clicked.connect(self.clear_history)
        self.clear_button.setToolTip("Clear all test history")
        button_layout.addWidget(self.clear_button)

        main_layout.addLayout(button_layout)

        # Status
        self.status_label = QLabel("Ready to test")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 11px;")
        main_layout.addWidget(self.status_label)

        # History (scrollable)
        history_scroll = QScrollArea()
        history_scroll.setWidgetResizable(True)
        history_scroll.setFixedHeight(100)
        history_scroll.setStyleSheet("background: transparent; border: none;")
        history_widget = QWidget()
        history_layout = QVBoxLayout(history_widget)

        self.history_title = QLabel("Previous Tests:")
        self.history_title.setStyleSheet("font-weight: bold; font-size: 10px;")
        history_layout.addWidget(self.history_title)

        self.history_text = QLabel("No tests yet")
        self.history_text.setStyleSheet("font-size: 9px;")
        self.history_text.setWordWrap(True)
        history_layout.addWidget(self.history_text)

        history_widget.setLayout(history_layout)
        history_scroll.setWidget(history_widget)
        main_layout.addWidget(history_scroll)

        # Footer
        self.footer_label = QLabel("Developed by Saikat Majumder")
        self.footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.footer_label.setStyleSheet("font-size: 9px;")
        main_layout.addWidget(self.footer_label)

        main_layout.addStretch()
        self.load_logo_image()
        self.display_history()

    def paintEvent(self, event):
        """Paint gradient background."""
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, 0, self.height())
        theme = THEMES[self.current_theme]
        gradient.setColorAt(0, QColor(theme["bg1"]))
        gradient.setColorAt(1, QColor(theme["bg2"]))
        painter.fillRect(self.rect(), gradient)
        painter.end()

    def apply_theme(self):
        """Apply current theme to widgets."""
        theme = THEMES[self.current_theme]
        fg = theme["fg"]
        accent = theme["accent"]

        label_style = f"color: {fg}; background: transparent;"

        self.title_label.setStyleSheet(f"{label_style} font-size: 20px; font-weight: bold;")
        self.clock_label.setStyleSheet(f"{label_style} font-size: 14px; font-weight: bold;")
        self.server_label.setStyleSheet(f"{label_style} font-size: 10px;")
        self.download_label.setStyleSheet(f"{label_style} font-size: 11px;")
        self.upload_label.setStyleSheet(f"{label_style} font-size: 11px;")
        self.ping_label.setStyleSheet(f"{label_style} font-size: 11px;")
        self.download_value.setStyleSheet(f"{label_style} font-size: 11px; font-weight: bold;")
        self.upload_value.setStyleSheet(f"{label_style} font-size: 11px; font-weight: bold;")
        self.ping_value.setStyleSheet(f"{label_style} font-size: 11px; font-weight: bold;")
        self.status_label.setStyleSheet(f"{label_style} font-size: 11px;")
        self.history_title.setStyleSheet(f"{label_style} font-weight: bold; font-size: 10px;")
        self.history_text.setStyleSheet(f"{label_style} font-size: 9px;")
        self.footer_label.setStyleSheet(f"{label_style} font-size: 9px;")

        if not hasattr(self, 'original_pixmap') or not self.original_pixmap:
            self.logo_label.setStyleSheet(f"{label_style} font-size: 60px;")
        else:
            self.logo_label.setStyleSheet(label_style)

        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid {fg};
                border-radius: 5px;
                text-align: center;
                background-color: transparent;
                color: {fg};
            }}
            QProgressBar::chunk {{
                background-color: {accent};
            }}
        """)

        self.theme_button.setText(f"Switch to {'Dark' if self.current_theme == 'Light' else 'Light'} Theme")
        self.update()

    def toggle_theme(self):
        """Toggle between dark and light themes."""
        self.current_theme = "Light" if self.current_theme == "Dark" else "Dark"
        self.apply_theme()
        self.update_logo_pixmap()

    def update_clock(self):
        """Update clock display."""
        now = datetime.now().strftime("%H:%M:%S")
        self.clock_label.setText(now)

    def start_test(self):
        """Start speed test in background thread."""
        if self.speed_test_thread and self.speed_test_thread.isRunning():
            return

        self.test_button.setEnabled(False)
        self.cancel_button.setEnabled(True)

        self.speed_test_thread = SpeedTestThread()
        self.speed_test_thread.status_update.connect(self.status_label.setText)
        self.speed_test_thread.server_update.connect(self.server_label.setText)
        self.speed_test_thread.download_update.connect(
            lambda v: self.download_value.setText(format_speed(v))
        )
        self.speed_test_thread.upload_update.connect(
            lambda v: self.upload_value.setText(format_speed(v))
        )
        self.speed_test_thread.ping_update.connect(
            lambda v: self.ping_value.setText(f"{v:.2f} ms")
        )
        self.speed_test_thread.progress_update.connect(self.progress_bar.setValue)
        self.speed_test_thread.test_complete.connect(self.on_test_complete)
        self.speed_test_thread.test_error.connect(self.on_test_error)
        self.speed_test_thread.finished.connect(self.on_test_finished)

        self.speed_test_thread.start()

    def cancel_test(self):
        """Cancel the ongoing speed test."""
        if self.speed_test_thread and self.speed_test_thread.isRunning():
            self.speed_test_thread.terminate()
            self.status_label.setText("Test cancelled")
            self.progress_bar.setValue(0)
            self.cancel_button.setEnabled(False)
            self.test_button.setEnabled(True)

    def on_test_finished(self):
        """Handle thread completion."""
        self.cancel_button.setEnabled(False)
        self.test_button.setEnabled(True)

    def on_test_complete(self, data: Dict):
        """Handle test completion."""
        self.add_to_history(data)

    def on_test_error(self, error_msg: str):
        """Handle test error."""
        QMessageBox.critical(self, "Error", error_msg)

    def add_to_history(self, data: Dict):
        """Add test result to history."""
        self.test_history.append(data)
        if len(self.test_history) > 5:
            self.test_history.pop(0)
        self.save_history()
        self.display_history()

    def display_history(self):
        """Display test history."""
        if not self.test_history:
            self.history_text.setText("No tests yet")
            return

        history_text = ""
        for i, test in enumerate(reversed(self.test_history), 1):
            date_str = test.get('date', test.get('time', ''))
            download_mbps = test['download']
            upload_mbps = test['upload']

            download_str = format_speed(download_mbps)
            upload_str = format_speed(upload_mbps)

            history_text += f"{i}. {date_str} - ↓{download_str} ↑{upload_str}, Ping: {test['ping']:.0f}ms\n"

        self.history_text.setText(history_text.strip())

    def clear_history(self):
        """Clear test history."""
        self.test_history = []
        self.save_history()
        self.display_history()

    def load_history(self):
        """Load test history from file."""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    self.test_history = json.load(f)
                if len(self.test_history) > 5:
                    self.test_history = self.test_history[-5:]
        except Exception as e:
            print(f"Error loading history: {e}")
            self.test_history = []

    def save_history(self):
        """Save test history to file."""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.test_history, f, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")

def main():
    app = QApplication(sys.argv)
    window = SpeedTestApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
