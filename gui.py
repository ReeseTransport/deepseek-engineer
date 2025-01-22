import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, 
                            QTextEdit, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLineEdit, QLabel, QDialog, QDialogButtonBox, 
                            QFormLayout, QMessageBox)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt, QUrl
from main import stream_openai_response  # Reuse existing functionality

class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration")
        self.setFixedSize(400, 200)
        
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("Enter DeepSeek API key...")
        self.base_url_edit = QLineEdit("https://api.deepseek.com")
        self.model_edit = QLineEdit()
        self.model_edit.setPlaceholderText("deepseek-chat")
        
        form_layout.addRow("API Key:", self.api_key_edit)
        form_layout.addRow("Base URL:", self.base_url_edit)
        form_layout.addRow("Model Name:", self.model_edit)
        
        # Load existing values from .env
        self.load_config()
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.save_config)
        button_box.rejected.connect(self.reject)
        
        layout.addLayout(form_layout)
        layout.addWidget(button_box)
        self.setLayout(layout)
    
    def load_config(self):
        """Load configuration from .env file"""
        env_path = Path(".env")
        if env_path.exists():
            load_dotenv()
            self.api_key_edit.setText(os.getenv("DEEPSEEK_API_KEY", ""))
            self.base_url_edit.setText(os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com"))
            self.model_edit.setText(os.getenv("DEEPSEEK_MODEL", "deepseek-chat"))
    
    def save_config(self):
        """Save configuration to .env file"""
        env_content = f"""DEEPSEEK_API_KEY={self.api_key_edit.text()}
DEEPSEEK_API_BASE={self.base_url_edit.text()}
DEEPSEEK_MODEL={self.model_edit.text()}"""
        
        try:
            with open(".env", "w") as f:
                f.write(env_content)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save config: {str(e)}")

class ChatUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DeepSeek Engineer UI")
        self.setGeometry(100, 100, 1200, 800)
        
        # Main container
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Layouts
        main_layout = QVBoxLayout()
        tab_layout = QVBoxLayout()
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Create tabs
        self.chat_tab = self.create_chat_tab()
        self.code_tab = self.create_code_tab()
        self.web_tab = self.create_web_tab()
        
        # Add tabs
        self.tabs.addTab(self.chat_tab, "Chat")
        self.tabs.addTab(self.code_tab, "Code")
        self.tabs.addTab(self.web_tab, "Web")
        
        main_layout.addWidget(self.tabs)
        main_layout.addLayout(self.create_bottom_bar())
        main_widget.setLayout(main_layout)
        
        # Load styles
        self.load_styles()

    def create_chat_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        
        self.user_input = QLineEdit()
        self.user_input.returnPressed.connect(self.handle_user_input)
        
        layout.addWidget(self.chat_history)
        layout.addWidget(self.user_input)
        tab.setLayout(layout)
        return tab

    def create_code_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        self.code_editor = QTextEdit()
        self.code_editor.setPlaceholderText("Enter code here...")
        
        layout.addWidget(self.code_editor)
        return tab

    def create_web_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        self.web_view = QWebEngineView()
        self.web_view.load(QUrl("about:blank"))
        
        layout.addWidget(self.web_view)
        return tab

    def create_bottom_bar(self):
        bar_layout = QHBoxLayout()
        
        self.status_label = QLabel("Ready")
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_chat)
        config_button = QPushButton("Config")
        config_button.clicked.connect(self.handle_config)
        
        bar_layout.addWidget(self.status_label)
        bar_layout.addWidget(clear_button)
        bar_layout.addWidget(config_button)
        return bar_layout

    def load_styles(self):
        try:
            with open("styles.qss", "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2b2b2b;
                }
                QTextEdit {
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                    font-family: Consolas;
                    font-size: 12pt;
                }
                QTabWidget::pane {
                    border: 1px solid #444;
                }
            """)

    def handle_user_input(self):
        user_text = self.user_input.text()
        if not user_text:
            return
            
        self.status_label.setText("Processing...")
        response = stream_openai_response(user_text)
        self.display_response(response)
        self.user_input.clear()
        self.status_label.setText("Ready")

    def display_response(self, response):
        self.chat_history.append(f"\nUser: {response.assistant_reply}")
        if response.files_to_create:
            self.chat_history.append("\nCreated files:")
            for file in response.files_to_create:
                self.chat_history.append(f" - {file['path']}")

    def clear_chat(self):
        self.chat_history.clear()

    def handle_config(self):
        dialog = ConfigDialog(self)
        if dialog.exec():
            self.status_label.setText("Configuration saved successfully! Restart to apply changes.")

    def closeEvent(self, event):
        # Properly cleanup web engine components
        self.web_view.page().deleteLater()
        self.web_view.deleteLater()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatUI()
    window.show()
    sys.exit(app.exec())
