import sys
import os
import subprocess
import shutil
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
#
# Create the application and set the icon theme
app = QApplication(sys.argv)
app.setWindowIcon(QIcon.fromTheme("applications-interfacedesign"))

def ensure_konsave_in_path():
    if shutil.which("konsave") is not None:
        return

    try:
        result = subprocess.run(
            ["pip", "show", "konsave"],
            capture_output=True,
            text=True,
            check=True
        )
        for line in result.stdout.splitlines():
            if line.startswith("Location:"):
                location = line.split(":", 1)[1].strip()
                bin_path = os.path.join(location, "bin")
                break
        else:
            return

        if not os.path.isdir(bin_path):
            return

        # Detect shell
        shell_path = os.environ.get("SHELL", "")
        shell_name = os.path.basename(shell_path)

        if "bash" in shell_name:
            rc_file = os.path.expanduser("~/.bashrc")
            export_line = f'export PATH="{bin_path}:$PATH"'
        elif "zsh" in shell_name:
            rc_file = os.path.expanduser("~/.zshrc")
            export_line = f'export PATH="{bin_path}:$PATH"'
        elif "fish" in shell_name:
            rc_file = os.path.expanduser("~/.config/fish/config.fish")
            export_line = f'set -gx PATH "{bin_path}" $PATH'
        else:
            rc_file = os.path.expanduser("~/.profile")
            export_line = f'export PATH="{bin_path}:$PATH"'

        # Check for duplicates
        if os.path.exists(rc_file):
            with open(rc_file, "r") as f:
                if bin_path in f.read():
                    return

        # Ask user whether to apply automatically or manually
        choice = QMessageBox.question(
            None,
            "Add Konsave to PATH",
            f"Konsave was installed, but it's not in your system PATH.\n\n"
            f"Shell: {shell_name or 'unknown'}\n"
            f"Config file: {rc_file}\n\n"
            f"Do you want to automatically add the following line?\n\n{export_line}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if choice == QMessageBox.StandardButton.Yes:
            with open(rc_file, "a") as f:
                f.write(f"\n# Added by Konsave GUI\n{export_line}\n")
            QMessageBox.information(
                None,
                "Konsave Path Added",
                f"The line was added to {rc_file}.\nYou may need to restart your terminal or log out and back in."
            )
        else:
            QMessageBox.information(
                None,
                "Manual PATH Setup",
                f"Please add the following line to {rc_file} manually:\n\n{export_line}"
            )

    except Exception as e:
        QMessageBox.warning(
            None,
            "Path Setup Failed",
            f"Could not detect konsave installation location or modify PATH.\n\nError:\n{e}"
        )

def install_konsave_if_missing():
    try:
        import konsave
        return
    except ImportError:
        choice = QMessageBox.question(
            None,
            "Konsave Not Installed",
            "Konsave is not installed. Do you want to install it now using pip?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if choice != QMessageBox.StandardButton.Yes:
            sys.exit("Konsave is required. Exiting.")

        try:
            subprocess.run(
                ["pip", "install", "konsave"],
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            if "externally-managed-environment" in e.stderr:
                override = QMessageBox.question(
                    None,
                    "PEP 668 Restriction",
                    "Your system restricts pip installs (PEP 668).\n"
                    "Do you want to force install with:\n\npip install --break-system-packages konsave?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if override == QMessageBox.StandardButton.Yes:
                    try:
                        subprocess.run(
                            ["pip", "install", "--break-system-packages", "konsave"],
                            capture_output=True,
                            text=True,
                            check=True
                        )
                    except subprocess.CalledProcessError as e2:
                        QMessageBox.critical(
                            None,
                            "Forced Installation Failed",
                            f"Even forced installation failed.\n\nError:\n{e2.stderr.strip()}"
                        )
                        sys.exit(1)
                else:
                    sys.exit("Installation cancelled due to system restrictions.")
            else:
                QMessageBox.critical(
                    None,
                    "Installation Failed",
                    f"Failed to install konsave.\n\nError:\n{e.stderr.strip()}"
                )
                sys.exit(1)

        try:
            import konsave
            ensure_konsave_in_path()
        except ImportError:
            QMessageBox.critical(
                None,
                "Import Error",
                "Installed konsave but still cannot import it."
            )
            sys.exit(1)

if __name__ == "__main__":
    print("Checking Konsave...")
    install_konsave_if_missing()
    ensure_konsave_in_path()
    print("Launching main.py...")

    subprocess.run(
        [sys.executable, os.path.join(SCRIPT_DIR, "main.py")],
        cwd=os.path.expanduser("~")
    )
