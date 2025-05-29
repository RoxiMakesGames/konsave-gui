#!/bin/bash
set -e

echo "📥 Downloading konsave-gui from GitHub..."
curl -fsSL https://raw.githubusercontent.com/RoxiMakesGames/konsave-gui/refs/heads/master/konsave-gui -o konsave-gui

echo "🔐 Making it executable..."
chmod +x konsave-gui

echo "📦 Installing konsave and PyQt6 (if not already present)..."
python3 -m pip install konsave PyQt6 || python3 -m pip install --break-system-packages konsave PyQt6

read -p "🛠️ Do you want to move it to ~/.local/bin (recommended)? (y/n): " move_ans
if [[ "$move_ans" =~ ^[Yy]$ ]]; then
    mkdir -p ~/.local/bin
    mv konsave-gui ~/.local/bin/konsave-gui
    echo "✅ Installed to ~/.local/bin/konsave-gui"

    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo "📎 ~/.local/bin is not in PATH."

        SHELL_NAME=$(basename "$SHELL")
        if [[ "$SHELL_NAME" == "bash" ]]; then
            RC=~/.bashrc
        elif [[ "$SHELL_NAME" == "zsh" ]]; then
            RC=~/.zshrc
        else
            RC=~/.profile
        fi

        echo -e "\n# Added by konsave-gui installer\nexport PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$RC"
        echo "✅ Added ~/.local/bin to PATH in $RC"
        echo "🔁 Restart your terminal or source $RC to apply changes."
    fi
else
    echo "ℹ️ You can run ./konsave-gui manually or move it to a directory in your PATH."
fi

echo "🎉 Done! Run it with: konsave-gui"
