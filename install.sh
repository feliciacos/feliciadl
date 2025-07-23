#!/bin/bash

set -e

APP_DIR="/opt/feliciadl"
LAUNCHER="/usr/bin/feliciadl"
DESKTOP_FILE="$HOME/.local/share/applications/feliciadl.desktop"
CONFIG_FILE="$HOME/.config/feliciadl/config.json"
DEFAULT_DOWNLOAD_DIR="$HOME/Downloads/FeliciaDL"
ICON_PATH="$APP_DIR/assets/icon.png"

print_header() {
  echo -e "\n======================================"
  echo "  Installing FeliciaDL Downloader"
  echo "======================================"
}

install_dependencies() {
  echo -e "\nInstalling system dependencies..."
  if command -v yay &> /dev/null; then
    yay -S --needed yt-dlp ffmpeg tk python-pipx zenity python-ttkbootstrap --noconfirm
  elif command -v apt &> /dev/null; then
    sudo apt update
    sudo apt install -y python3 python3-pip python3-tk ffmpeg zenity
    python3 -m pip install --user pipx
    python3 -m pipx ensurepath
    python3 -m pip install --user ttkbootstrap
  else
    echo "Unsupported package manager. Please install yt-dlp, ffmpeg, tk, pipx, zenity, and ttkbootstrap manually."
    exit 1
  fi

  pipx install gallery-dl || true
  pipx install spotdl || true
}

install_app_files() {
  echo -e "\nCopying application files to $APP_DIR..."
  sudo mkdir -p "$APP_DIR"
  sudo cp downloader.py downloader_gui.py "$APP_DIR/"

  echo "Copying assets..."
  if [ -d "assets" ]; then
    sudo mkdir -p "$APP_DIR/assets"
    sudo cp -r assets/* "$APP_DIR/assets/"
  fi
}

install_launcher() {
  echo -e "\nInstalling launcher to $LAUNCHER..."
  sudo cp feliciadl "$LAUNCHER"
  sudo chmod +x "$LAUNCHER"
}

install_desktop_entry() {
  echo -e "\nRegistering desktop shortcut..."
  mkdir -p "$(dirname "$DESKTOP_FILE")"

  if [ -f "$ICON_PATH" ]; then
    ICON_LINE="Icon=$ICON_PATH"
  else
    ICON_LINE="Icon=utilities-terminal"
  fi

  cat <<EOF > "$DESKTOP_FILE"
[Desktop Entry]
Type=Application
Name=FeliciaDL
Exec=feliciadl
$ICON_LINE
Terminal=false
Categories=AudioVideo;Utility;
Comment=Media downloader using yt-dlp, gallery-dl, spotdl
StartupNotify=true
EOF

  update-desktop-database "$(dirname "$DESKTOP_FILE")"
}

create_config_if_missing() {
  echo -e "\nChecking for config.json..."
  if [ ! -f "$CONFIG_FILE" ]; then
    echo "Creating default config.json"
    mkdir -p "$(dirname "$CONFIG_FILE")"
    echo "{\"download_dir\": \"$DEFAULT_DOWNLOAD_DIR\", \"theme\": \"darkly\"}" > "$CONFIG_FILE"
  else
    echo "Config.json already exists, preserving user settings."
  fi
}

print_footer() {
  echo -e "\nFeliciaDL installed successfully!"
  echo "Run in terminal: feliciadl"
  echo "Or launch from Start Menu: FeliciaDL"
}

# Run all steps
print_header
install_dependencies
install_app_files
install_launcher
install_desktop_entry
create_config_if_missing
print_footer
