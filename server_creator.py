import json
import os
import requests
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QLabel, QComboBox, QPushButton, QMessageBox, 
                           QSpinBox, QDialog, QProgressBar, QLineEdit, QCheckBox,
                           QTextEdit)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import subprocess
import shutil
from pathlib import Path

class ConfigLoader(QThread):
    loaded = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def run(self):
        try:
            # GitHub raw content URL
            url = "https://raw.githubusercontent.com/Maybeoff/mcservercreater/main/server-config.json"
            response = requests.get(url)
            response.raise_for_status()
            config = response.json()
            self.loaded.emit(config)
        except Exception as e:
            self.error.emit(f"Failed to load configuration: {str(e)}")

class DownloadThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool)
    
    def __init__(self, version, server_type, config_data):
        super().__init__()
        self.version = version
        self.server_type = server_type
        self.config_data = config_data
        
    def run(self):
        try:
            url = self.config_data[self.server_type]['versions'][self.version]
            response = requests.get(url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024  # 1 Kibibyte
            downloaded = 0
            
            with open('server.jar', 'wb') as f:
                for data in response.iter_content(block_size):
                    downloaded += len(data)
                    f.write(data)
                    if total_size:
                        progress = int((downloaded / total_size) * 100)
                        self.progress.emit(progress)
            
            self.finished.emit(True)
        except Exception as e:
            print(f"Error: {e}")
            self.finished.emit(False)

class ServerSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Server Settings")
        self.setModal(True)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Server name
        name_label = QLabel("Server Name:")
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter server name")
        
        # RAM selection
        ram_label = QLabel("RAM Allocation (GB):")
        self.ram_spin = QSpinBox()
        self.ram_spin.setRange(1, 32)
        self.ram_spin.setValue(4)
        
        # CPU cores selection
        cores_label = QLabel("CPU Cores to Use:")
        self.cores_spin = QSpinBox()
        self.cores_spin.setRange(1, os.cpu_count() or 1)
        self.cores_spin.setValue(os.cpu_count() or 1)
        
        # Max players
        players_label = QLabel("Max Players:")
        self.players_spin = QSpinBox()
        self.players_spin.setRange(1, 100)
        self.players_spin.setValue(20)
        
        # Server port
        port_label = QLabel("Server Port:")
        self.port_edit = QLineEdit()
        self.port_edit.setText("25565")
        
        # Online mode
        self.online_mode = QCheckBox("Online Mode")
        self.online_mode.setChecked(True)
        
        # Create button
        create_button = QPushButton("Create Server")
        create_button.clicked.connect(self.accept)
        
        layout.addWidget(name_label)
        layout.addWidget(self.name_edit)
        layout.addWidget(ram_label)
        layout.addWidget(self.ram_spin)
        layout.addWidget(cores_label)
        layout.addWidget(self.cores_spin)
        layout.addWidget(players_label)
        layout.addWidget(self.players_spin)
        layout.addWidget(port_label)
        layout.addWidget(self.port_edit)
        layout.addWidget(self.online_mode)
        layout.addWidget(create_button)
        
        self.setLayout(layout)

class ServerStartDialog(QDialog):
    def __init__(self, server_dir, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Starting Server")
        self.setModal(True)
        self.server_dir = server_dir
        self.setup_ui()
        self.start_server()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Progress label
        self.progress_label = QLabel("Starting server...")
        layout.addWidget(self.progress_label)
        
        # Console output
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        layout.addWidget(self.console)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        layout.addWidget(self.progress_bar)
        
        # Stop button
        self.stop_button = QPushButton("Stop Server")
        self.stop_button.clicked.connect(self.stop_server)
        layout.addWidget(self.stop_button)
        
        self.setLayout(layout)
        self.resize(600, 400)
    
    def start_server(self):
        self.process = subprocess.Popen(
            ["start.bat"],
            cwd=self.server_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Start reading output
        self.read_output()
    
    def read_output(self):
        if self.process.poll() is None:  # Process is still running
            output = self.process.stdout.readline()
            if output:
                self.console.append(output.strip())
            QApplication.processEvents()
            # Schedule next read
            Qt.QTimer.singleShot(100, self.read_output)
        else:
            self.progress_label.setText("Server stopped")
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)
    
    def stop_server(self):
        if self.process.poll() is None:  # Process is still running
            self.process.terminate()
            self.progress_label.setText("Stopping server...")
            self.stop_button.setEnabled(False)

class ServerCreator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Minecraft Server Creator")
        self.setGeometry(100, 100, 400, 300)
        
        # Start loading configuration
        self.load_config()
        
    def load_config(self):
        self.progress_label = QLabel("Loading configuration...")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.progress_label)
        layout.addWidget(self.progress_bar)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        self.config_loader = ConfigLoader()
        self.config_loader.loaded.connect(self.on_config_loaded)
        self.config_loader.error.connect(self.on_config_error)
        self.config_loader.start()
    
    def on_config_loaded(self, config):
        self.config_data = config
        self.setup_ui()
    
    def on_config_error(self, error_message):
        QMessageBox.critical(self, "Error", error_message)
        self.close()
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        
        # Server type selection
        type_label = QLabel("Select Server Type:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(self.config_data.keys())
        self.type_combo.currentTextChanged.connect(self.update_versions)
        
        # Version selection
        version_label = QLabel("Select Minecraft Version:")
        self.version_combo = QComboBox()
        self.update_versions()
        
        # Create button
        self.create_button = QPushButton("Create Server")
        self.create_button.clicked.connect(self.show_settings)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        
        # Progress label
        self.progress_label = QLabel("")
        
        layout.addWidget(type_label)
        layout.addWidget(self.type_combo)
        layout.addWidget(version_label)
        layout.addWidget(self.version_combo)
        layout.addWidget(self.create_button)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.progress_label)
        
        central_widget.setLayout(layout)
    
    def update_versions(self):
        server_type = self.type_combo.currentText()
        self.version_combo.clear()
        
        versions = list(self.config_data[server_type]['versions'].keys())
        self.version_combo.addItems(versions)
        self.version_combo.setCurrentText(self.config_data[server_type]['latest'])
    
    def show_settings(self):
        dialog = ServerSettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.create_server(
                dialog.name_edit.text(),
                dialog.ram_spin.value(),
                dialog.cores_spin.value(),
                dialog.players_spin.value(),
                dialog.port_edit.text(),
                dialog.online_mode.isChecked()
            )
    
    def create_server(self, server_name, ram_gb, cores, max_players, port, online_mode):
        if not server_name:
            QMessageBox.warning(self, "Error", "Please enter a server name!")
            return
            
        version = self.version_combo.currentText()
        server_type = self.type_combo.currentText()
        
        if not os.path.exists(server_name):
            os.makedirs(server_name)
        os.chdir(server_name)
        
        self.progress_label.setText("Downloading server files...")
        self.progress_bar.setValue(0)
        self.create_button.setEnabled(False)
        
        self.download_thread = DownloadThread(version, server_type, self.config_data)
        self.download_thread.progress.connect(self.update_progress)
        self.download_thread.finished.connect(lambda success: self.on_download_finished(
            success, server_name, ram_gb, cores, max_players, port, online_mode))
        self.download_thread.start()
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def on_download_finished(self, success, server_name, ram_gb, cores, max_players, port, online_mode):
        if success:
            self.create_start_script(ram_gb, cores)
            self.create_eula()
            self.create_server_properties(server_name, max_players, port, online_mode)
            self.progress_label.setText("Server created successfully!")
            QMessageBox.information(self, "Success", "Server created successfully!")
            
            # Ask if user wants to start the server
            reply = QMessageBox.question(self, "Start Server", 
                                       "Do you want to start the server now?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                start_dialog = ServerStartDialog(os.path.abspath(server_name), self)
                start_dialog.exec_()
        else:
            self.progress_label.setText("Failed to download server files")
            QMessageBox.critical(self, "Error", "Failed to download server files")
        
        self.create_button.setEnabled(True)
        self.progress_bar.setValue(0)
        os.chdir("..")  # Return to original directory
    
    def create_start_script(self, ram_gb, cores):
        ram_mb = ram_gb * 1024
        script_content = f"""@echo off
java -Xms{ram_mb}M -Xmx{ram_mb}M -XX:+UseG1GC -XX:ParallelGCThreads={cores} -jar server.jar nogui
pause"""
        with open('start.bat', 'w') as f:
            f.write(script_content)
    
    def create_eula(self):
        with open('eula.txt', 'w') as f:
            f.write('eula=true')
    
    def create_server_properties(self, server_name, max_players, port, online_mode):
        properties = {
            "server-name": server_name,
            "max-players": str(max_players),
            "server-port": port,
            "online-mode": str(online_mode).lower(),
            "enable-command-block": "true",
            "spawn-protection": "16",
            "view-distance": "10",
            "simulation-distance": "10",
            "difficulty": "easy",
            "gamemode": "survival",
            "level-type": "default",
            "enable-jmx-monitoring": "false",
            "enable-status": "true",
            "sync-chunk-writes": "true",
            "enable-query": "false",
            "query.port": port,
            "pvp": "true",
            "generate-structures": "true",
            "max-chained-neighbor-updates": "1000000",
            "rate-limit": "0",
            "hardcore": "false",
            "white-list": "false",
            "broadcast-console-to-ops": "true",
            "prevent-proxy-connections": "false",
            "hide-online-players": "false",
            "max-tick-time": "60000",
            "require-resource-pack": "false",
            "use-native-transport": "true",
            "enable-rcon": "false",
            "rcon.port": "25575",
            "rcon.password": "",
            "enable-command-block": "true",
            "op-permission-level": "4",
            "function-permission-level": "2",
            "level-name": "world",
            "motd": f"{server_name} - Minecraft Server"
        }
        
        with open("server.properties", "w") as f:
            for key, value in properties.items():
                f.write(f"{key}={value}\n")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ServerCreator()
    window.show()
    sys.exit(app.exec_()) 