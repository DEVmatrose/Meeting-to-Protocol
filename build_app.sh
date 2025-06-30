#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
APP_NAME="MeetingProtocolGenerator"
SCRIPT_ENTRY_POINT="gui.py"
OUTPUT_DIR="dist"

# --- Functions ---
echo_info() {
    echo "[INFO] $1"
}

echo_success() {
    echo "[SUCCESS] $1"
}

# --- Robustly find Python command ---
if command -v python3 &> /dev/null
then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null
then
    PYTHON_CMD="python"
else
    echo "[ERROR] Python not found. Please install Python."
    exit 1
fi
echo_info "Using '$PYTHON_CMD' as Python command."

# --- Build Process ---

# 1. Create a virtual environment
if [ ! -d "venv" ]; then
    echo_info "Creating Python virtual environment..."
    $PYTHON_CMD -m venv venv
fi
source venv/bin/activate

# 2. Install/Upgrade dependencies
echo_info "Installing/upgrading dependencies from requirements.txt..."
pip install -U pip
pip install -r requirements.txt
pip install pyinstaller # Ensure pyinstaller is installed

# 3. Clean up previous builds
if [ -d "$OUTPUT_DIR" ]; then
    echo_info "Cleaning up old build directory..."
    rm -rf "$OUTPUT_DIR"
fi
if [ -d "build" ]; then
    rm -rf "build"
fi
if [ -f "*.spec" ]; then
    rm -f "*.spec"
fi

# 4. Run PyInstaller
echo_info "Running PyInstaller to build the application..."
pyinstaller --name "$APP_NAME" \
            --onefile \
            --windowed \
            --add-data "templates:templates" \
            "$SCRIPT_ENTRY_POINT"

# The --windowed flag prevents a console window from appearing on Windows.
# --add-data ensures the 'templates' folder is included in the executable.

# 5. Clean up temporary files
echo_info "Cleaning up temporary build files..."
rm -rf build
rm -f "$APP_NAME.spec"

echo_success "Build complete!"
echo_info "The executable can be found in the '$OUTPUT_DIR' directory."
echo_info "You can now download this file and run it on your local machine."
