#!/usr/bin/env bash
# UMOS installer for macOS and Linux.
# Usage: curl -fsSL https://raw.githubusercontent.com/yxtan5022-maker/unimind-os/main/install.sh | bash
# Or:  ./install.sh [--user]
set -euo pipefail

INSTALL_DIR="${UMOS_DIR:-"$HOME/.umos"}"
BIN_DIR="${UMOS_BIN_DIR:-"$HOME/.local/bin"}"
DESKTOP_DIR="${XDG_DATA_HOME:-"$HOME/.local/share"}/applications"
USE_SUDO=true

# --- Parse args ---
for arg in "$@"; do
    case "$arg" in
        --user) USE_SUDO=false; BIN_DIR="$HOME/.local/bin";;
        --help) echo "Usage: install.sh [--user]"; exit 0;;
    esac
done

# --- Detect OS ---
OS="$(uname -s)"
ARCH="$(uname -m)"
case "$OS" in
    Darwin) OS_NAME="macOS";;
    Linux)  OS_NAME="Linux";;
    *)      echo "[UMOS] Unsupported OS: $OS"; exit 1;;
esac
echo "[UMOS] Detected: $OS_NAME ($ARCH)"

# --- Prefer uv if available, fall back to pip ---
INSTALL_CMD=""
if command -v uv &>/dev/null; then
    INSTALL_CMD="uv pip"
elif command -v pip3 &>/dev/null; then
    INSTALL_CMD="pip3"
elif command -v pip &>/dev/null; then
    INSTALL_CMD="pip"
else
    echo "[UMOS] Python not found. Attempting to install..."
    case "$OS" in
        Darwin) brew install python3 ;;
        Linux)
            if command -v apt-get &>/dev/null; then
                sudo apt-get update -qq && sudo apt-get install -y -qq python3 python3-pip python3-venv
            elif command -v dnf &>/dev/null; then
                sudo dnf install -y python3 python3-pip
            elif command -v pacman &>/dev/null; then
                sudo pacman -S --noconfirm python python-pip
            else
                echo "[UMOS] Please install Python 3.10+ manually." >&2
                exit 1
            fi
    esac
    INSTALL_CMD="pip3"
fi

# --- Clone or update ---
if [ -d "$INSTALL_DIR" ]; then
    echo "[UMOS] Updating existing installation at $INSTALL_DIR..."
    cd "$INSTALL_DIR"
    git pull --ff-only
else
    echo "[UMOS] Cloning UMOS to $INSTALL_DIR..."
    git clone https://github.com/yxtan5022-maker/unimind-os.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# --- Install Python package ---
echo "[UMOS] Installing Python package..."
$INSTALL_CMD install -e .

# --- Install optional extras ---
echo "[UMOS] Installing optional dependencies..."
$INSTALL_CMD install -e ".[hw]" 2>/dev/null || true  # psutil (safe everywhere)
if [ "$OS" = "Linux" ]; then
    $INSTALL_CMD install -e ".[quantum]" 2>/dev/null || true  # qiskit (Linux ok)
fi

# --- Install launcher ---
mkdir -p "$BIN_DIR"
cp "$INSTALL_DIR/umos" "$BIN_DIR/umos"
chmod +x "$BIN_DIR/umos"
echo "[UMOS] Launcher installed: $BIN_DIR/umos"

# --- Install .desktop file (Linux) ---
if [ "$OS" = "Linux" ]; then
    mkdir -p "$DESKTOP_DIR"
    cat > "$DESKTOP_DIR/umos.desktop" << 'DESKTOP_EOF'
[Desktop Entry]
Name=UMOS Desktop
Comment=UniMind OS - AI Native Operating System
Exec=umos --desktop
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=Utility;Science;Development;
StartupNotify=true
DESKTOP_EOF
    chmod +x "$DESKTOP_DIR/umos.desktop"
    echo "[UMOS] Desktop entry installed: $DESKTOP_DIR/umos.desktop"

    # Also install to /usr/local/share/applications if sudo available
    if $USE_SUDO && command -v sudo &>/dev/null; then
        sudo mkdir -p /usr/local/share/applications
        sudo cp "$DESKTOP_DIR/umos.desktop" /usr/local/share/applications/umos.desktop
    fi
fi

# --- macOS .app bundle (manual instruction) ---
if [ "$OS" = "Darwin" ]; then
    echo "[UMOS] macOS detected. To create a .app bundle, run:"
    echo "  python3 $INSTALL_DIR/build_exe.py"
    echo "  open $INSTALL_DIR/dist/UMOS-Desktop.app"
fi

# --- Add to PATH if not already ---
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    SHELL_CONFIG="$HOME/.bashrc"
    if [ -n "${ZSH_VERSION:-}" ] || [ -f "$HOME/.zshrc" ]; then
        SHELL_CONFIG="$HOME/.zshrc"
    fi
    echo "" >> "$SHELL_CONFIG"
    echo "# UMOS" >> "$SHELL_CONFIG"
    echo "export PATH=\"\$PATH:$BIN_DIR\"" >> "$SHELL_CONFIG"
    echo "[UMOS] Added $BIN_DIR to PATH in $SHELL_CONFIG"
    echo "[UMOS] Run 'source $SHELL_CONFIG' to update your current shell."
fi

echo ""
echo "[UMOS] Installation complete!"
echo "[UMOS] Run 'umos' to launch the Desktop GUI."
echo "[UMOS] Run 'umos --help' to see all commands."
