#!/bin/bash

set -e

echo "🔍 Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install it first."
    exit 1
fi

PYTHON=python3
PIP="$PYTHON -m pip"

echo "✅ Python found: $($PYTHON --version)"

echo "📦 Checking/Installing dependencies (konsave, PyQt6)..."

install_dep() {
    local package=$1
    if ! $PYTHON -c "import $package" &> /dev/null; then
        echo "🔧 Installing $package..."
        if ! $PIP install "$package"; then
            echo "⚠️  Standard pip install failed. Trying --break-system-packages (PEP 668 workaround)..."
            $PIP install --break-system-packages "$package"
        fi
    else
        echo "✅ $package already installed."
    fi
}

install_dep konsave
install_dep PyQt6

BIN_DIR=$(dirname "$(which konsave)")
GUI_PATH="$BIN_DIR/konsave-gui"

echo "📄 Creating executable konsave-gui in $BIN_DIR..."

cat << 'EOF' > "$GUI_PATH"
#!/usr/bin/env python3
[source]
EOF

echo "✅ Script written to $GUI_PATH"

read -p "🔐 Do you want to make 'konsave-gui' executable with chmod +x? (y/n): " chmod_ans
if [[ "$chmod_ans" =~ ^[Yy]$ ]]; then
    chmod +x "$GUI_PATH"
    echo "✅ Made executable."
else
    echo "ℹ️ Skipped chmod. You can run: chmod +x \"$GUI_PATH\""
fi

read -p "🛠️  Do you want to add $BIN_DIR to your PATH in your shell config? (y/n): " path_ans
if [[ "$path_ans" =~ ^[Yy]$ ]]; then
    SHELL_NAME=$(basename "$SHELL")

    if [[ "$SHELL_NAME" == "bash" ]]; then
        RC=~/.bashrc
        LINE="export PATH=\"$BIN_DIR:\$PATH\""
    elif [[ "$SHELL_NAME" == "zsh" ]]; then
        RC=~/.zshrc
        LINE="export PATH=\"$BIN_DIR:\$PATH\""
    elif [[ "$SHELL_NAME" == "fish" ]]; then
        RC=~/.config/fish/config.fish
        LINE="set -gx PATH \"$BIN_DIR\" \$PATH"
    else
        RC=~/.profile
        LINE="export PATH=\"$BIN_DIR:\$PATH\""
    fi

    if grep -q "$BIN_DIR" "$RC" 2>/dev/null; then
        echo "ℹ️ PATH already includes $BIN_DIR in $RC"
    else
        echo -e "\n# Added by konsave-gui installer\n$LINE" >> "$RC"
        echo "✅ Added to $RC"
    fi

    echo "⚠️ You may need to restart your terminal or log out/in for changes to take effect."
else
    echo "ℹ️ Skipped modifying PATH. You can manually add \"$BIN_DIR\" to your shell config."
fi

echo "🎉 Done! Run with: konsave-gui"
