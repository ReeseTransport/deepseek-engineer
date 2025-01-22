import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTextEdit, QLineEdit, QPushButton, QTabWidget, QLabel)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from main import stream_openai_response, read_local_file, create_file, apply_diff_edit
from rich.console import Console

class StreamThread(QThread):
    response_received = pyqtSignal(dict)
    
    def __init__(self, user_input):
        super().__init__()
        self.user_input = user_input
        
    def run(self):
        response = stream_openai_response(self.user_input)
        self.response_received.emit(response.model_dump())

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.console = Console()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("DeepSeek Engineer GUI")
        self.setGeometry(100, 100, 1200, 800)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout()
        main_widget.setLayout(layout)
        
        # Create tab widget
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # Chat Tab
        chat_tab = QWidget()
        self.setup_chat_tab(chat_tab)
        tab_widget.addTab(chat_tab, "Chat")
        
        # Code Tab
        code_tab = QWidget()
        self.setup_code_tab(code_tab)
        tab_widget.addTab(code_tab, "Code")
        
        # Web View Tab
        web_tab = QWidget()
        self.setup_web_tab(web_tab)
        tab_widget.addTab(web_tab, "Web")
        
        # Input Area
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Enter your command or type '/add filename' to include files")
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.handle_input)
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_btn)
        layout.addLayout(input_layout)
        
    def setup_chat_tab(self, tab):
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)
        
    def setup_code_tab(self, tab):
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        self.code_editor = QTextEdit()
        self.code_output = QTextEdit()
        self.code_output.setReadOnly(True)
        layout.addWidget(QLabel("Code Editor:"))
        layout.addWidget(self.code_editor)
        layout.addWidget(QLabel("Output:"))
        layout.addWidget(self.code_output)
        
    def setup_web_tab(self, tab):
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        self.web_view = QWebEngineView()
        self.web_view.load(QUrl("https://deepseek.com"))
        layout.addWidget(self.web_view)
        
    def handle_input(self):
        user_input = self.input_field.text()
        if not user_input:
            return
            
        self.input_field.clear()
        self.chat_display.append(f"You: {user_input}")
        
        # Handle file additions
        if user_input.lower().startswith("/add "):
            self.handle_file_addition(user_input)
            return
            
        # Start streaming thread
        self.stream_thread = StreamThread(user_input)
        self.stream_thread.response_received.connect(self.handle_response)
        self.stream_thread.start()
        
    def handle_file_addition(self, command):
        try:
            file_path = command[5:].strip()
            content = read_local_file(file_path)
            self.chat_display.append(f"System: Added file {file_path} to context")
            create_file(file_path, content)  # From main.py
        except Exception as e:
            self.chat_display.append(f"Error: {str(e)}")
            
    def handle_response(self, response):
        self.chat_display.append(f"Assistant: {response['assistant_reply']}")
        
        # Handle file operations
        if response.get('files_to_create'):
            for file in response['files_to_create']:
                create_file(file['path'], file['content'])
                self.chat_display.append(f"Created file: {file['path']}")
                
        if response.get('files_to_edit'):
            for edit in response['files_to_edit']:
                apply_diff_edit(edit['path'], edit['original_snippet'], edit['new_snippet'])
                self.chat_display.append(f"Updated file: {edit['path']}")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
