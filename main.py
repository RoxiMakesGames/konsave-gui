import sys
import os
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QInputDialog, QFileDialog, QMessageBox,
    QProgressBar, QLabel, QListWidgetItem
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon

# Set working directory to user's home directory for consistency
os.chdir(os.path.expanduser("~"))

class KonsaveMiniGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Konsave Profile Manager")
        self.setWindowIcon(QIcon.fromTheme("applications-interfacedesign"))  # ← Set icon here
        self.setFixedSize(320, 380)

        self.setup_ui()
        self.connect_signals()
        self.refresh_profiles()
        self.show_konsave_version()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        top_layout = QHBoxLayout()

        self.btn_open_folder = QPushButton()
        self.btn_open_folder.setIcon(QIcon.fromTheme("folder"))
        self.btn_open_folder.setFixedSize(32, 32)

        self.btn_refresh = QPushButton()
        self.btn_refresh.setIcon(QIcon.fromTheme("view-refresh"))
        self.btn_refresh.setFixedSize(32, 32)

        self.btn_save = QPushButton("Save")
        self.btn_import = QPushButton("Import")
        self.btn_export = QPushButton("Export")

        top_layout.addWidget(self.btn_open_folder)
        top_layout.addWidget(self.btn_refresh)
        top_layout.addWidget(self.btn_save)
        top_layout.addWidget(self.btn_import)
        top_layout.addWidget(self.btn_export)
        layout.addLayout(top_layout)

        self.profile_list = QListWidget()
        layout.addWidget(self.profile_list)

        bottom_layout = QHBoxLayout()
        self.btn_load = QPushButton("Load")
        self.btn_rename = QPushButton("Rename")
        self.btn_delete = QPushButton("Delete")
        bottom_layout.addWidget(self.btn_load)
        bottom_layout.addWidget(self.btn_rename)
        bottom_layout.addWidget(self.btn_delete)
        layout.addLayout(bottom_layout)

        self.status_label = QLabel("")
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

        self.btn_load.setEnabled(False)
        self.btn_export.setEnabled(False)

    def connect_signals(self):
        self.profile_list.currentItemChanged.connect(self.update_button_states)
        self.btn_save.clicked.connect(self.save_profile)
        self.btn_import.clicked.connect(self.import_profile)
        self.btn_export.clicked.connect(self.export_profile)
        self.btn_load.clicked.connect(self.load_profile)
        self.btn_delete.clicked.connect(self.delete_profile)
        self.btn_rename.clicked.connect(self.rename_profile)
        self.btn_refresh.clicked.connect(self.refresh_profiles)
        self.btn_open_folder.clicked.connect(self.open_profile_folder)

    def get_selected_profile(self):
        item = self.profile_list.currentItem()
        return item.text() if item else None

    def is_valid_profile(self, profile):
        return (
            profile
            and profile.strip()
            and profile != "(New Profile)"
            and profile != "No Profiles Found"
        )

    def update_button_states(self):
        valid = self.is_valid_profile(self.get_selected_profile())
        self.btn_load.setEnabled(valid)
        self.btn_export.setEnabled(valid)

    def update_progress(self, message=None, running=False, auto_clear=False):
        if message:
            self.status_label.setText(message)
        self.progress_bar.setVisible(running)
        self.progress_bar.setRange(0, 0 if running else 1)
        if not running:
            self.progress_bar.setValue(1)
        QApplication.processEvents()
        if auto_clear:
            QTimer.singleShot(2000, self.clear_progress)

    def clear_progress(self):
        self.status_label.setText("")
        self.progress_bar.setVisible(False)

    def run_command(self, command):
        try:
            self.update_progress(f"Running: {command}", running=True)
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            output = result.stdout.strip()
            error = result.stderr.strip()

            if output:
                self.status_label.setText(output.splitlines()[-1])
            if error:
                print(error)

            self.update_progress("Done!", running=False, auto_clear=True)

        except subprocess.CalledProcessError as e:
            self.update_progress("Command failed", running=False, auto_clear=True)
            QMessageBox.critical(self, "Command Failed", str(e))
        except Exception as e:
            self.update_progress("Error!", running=False, auto_clear=True)
            QMessageBox.critical(self, "Error", str(e))

    def refresh_profiles(self):
        self.profile_list.blockSignals(True)
        self.profile_list.clear()

        self.profile_list.addItem("(New Profile)")
        valid_profiles = []

        try:
            result = subprocess.run("konsave -l", shell=True, capture_output=True, text=True)
            for line in result.stdout.strip().splitlines():
                line = line.strip()
                if line and not line.lower().startswith("id") and "konsave" not in line.lower():
                    parts = line.split(maxsplit=1)
                    if len(parts) == 2:
                        profile_name = parts[1]
                        valid_profiles.append(profile_name)
                        self.profile_list.addItem(profile_name)
        except Exception as e:
            print(f"Error loading profiles: {str(e)}")

        if not valid_profiles:
            no_profile_item = QListWidgetItem("No Profiles Found")
            no_profile_item.setFlags(no_profile_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.profile_list.addItem(no_profile_item)

        self.profile_list.blockSignals(False)
        self.profile_list.setCurrentRow(0)
        self.update_button_states()

    def save_profile(self):
        profile = self.get_selected_profile()
        if self.is_valid_profile(profile):
            confirm = QMessageBox.question(self, "Overwrite Profile", f"Overwrite profile '{profile}'?",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if confirm == QMessageBox.StandardButton.Yes:
                self.run_command(f'konsave -s "{profile}"')
        else:
            name, ok = QInputDialog.getText(self, "Save New Profile", "Enter profile name:")
            if ok and name.strip():
                self.run_command(f'konsave -s "{name.strip()}"')
        self.refresh_profiles()

    def import_profile(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import .knsv File", "", "Konsave Files (*.knsv)")
        if file_path:
            self.run_command(f'konsave -i "{file_path}"')
            self.refresh_profiles()

    def export_profile(self):
        profile = self.get_selected_profile()
        if not self.is_valid_profile(profile):
            QMessageBox.warning(self, "No Profile Selected", "Please select a valid profile to export.")
            return

        default_filename = f"{profile}.knsv"
        file_path, _ = QFileDialog.getSaveFileName(self, "Export .knsv File", default_filename, "Konsave Files (*.knsv)")
        if file_path:
            if file_path.lower().endswith(".knsv"):
                file_path = file_path[:-5]
            self.run_command(f'konsave -e "{profile}" -n "{file_path}"')

    def load_profile(self):
        profile = self.get_selected_profile()
        if not self.is_valid_profile(profile):
            QMessageBox.warning(self, "No Profile Selected", "Please select a valid profile to load.")
            return

        self.run_command(f'konsave -a "{profile}"')
        QMessageBox.information(
            self,
            "KDE Reload Required",
            "Profile applied successfully.\nPlease log out and log back in to see the changes completely."
        )

    def delete_profile(self):
        profile = self.get_selected_profile()
        if not self.is_valid_profile(profile):
            QMessageBox.warning(self, "Cannot Delete", "Select a valid profile to delete.")
            return

        if QMessageBox.warning(self, "Delete Profile",
                               f"Are you sure you want to delete '{profile}'?",
                               QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.run_command(f'konsave -r "{profile}"')
            self.refresh_profiles()

    def rename_profile(self):
        old_name = self.get_selected_profile()
        if not self.is_valid_profile(old_name):
            QMessageBox.warning(self, "Invalid Profile", "Select a valid profile to rename.")
            return

        new_name, ok = QInputDialog.getText(self, "Rename Profile", "Enter new profile name:")
        if not (ok and new_name.strip()):
            return

        new_name = new_name.strip()

        if new_name == old_name:
            QMessageBox.information(self, "Same Name", "New profile name must be different.")
            return

        base_dir = os.path.join(os.path.expanduser("~"), ".config", "konsave", "profiles")
        old_path = os.path.join(base_dir, old_name)
        new_path = os.path.join(base_dir, new_name)

        if not os.path.exists(old_path):
            QMessageBox.critical(self, "Rename Failed", f"Profile folder does not exist:\n{old_path}")
            return

        if os.path.exists(new_path):
            QMessageBox.critical(self, "Rename Failed", f"A profile named '{new_name}' already exists.")
            return

        try:
            os.rename(old_path, new_path)
            QMessageBox.information(self, "Renamed", f"Renamed '{old_name}' to '{new_name}' successfully.")
            self.refresh_profiles()
        except Exception as e:
            QMessageBox.critical(self, "Rename Error", f"Could not rename the profile:\n{e}")

    def open_profile_folder(self):
        profile_path = os.path.join(os.path.expanduser("~"), ".config", "konsave", "profiles")
        if os.path.exists(profile_path):
            subprocess.Popen(["xdg-open", profile_path])

    def show_konsave_version(self):
        try:
            result = subprocess.run(["konsave", "--version"], capture_output=True, text=True, check=True)
            version = result.stdout.strip()
        except Exception:
            version = "Konsave: unknown version"

        version_label = QLabel(version)
        version_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        version_label.setStyleSheet("color: gray; font-size: 10px; margin-top: 4px;")
        self.layout().addWidget(version_label)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = KonsaveMiniGUI()
    window.show()
    sys.exit(app.exec())
