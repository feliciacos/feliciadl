#!/bin/bash
set -e

APP_DIR="/opt/feliciadl"
LAUNCHER="/usr/bin/feliciadl"
DESKTOP_FILE="$HOME/.local/share/applications/feliciadl.desktop"
CONFIG_DIR="$HOME/.config/feliciadl"
CONFIG_FILE="$CONFIG_DIR/config.json"
AUTOMATIC_FILE_SRC="automatic.json"
AUTOMATIC_FILE_DEST="$CONFIG_DIR/automatic.json"
DEFAULT_DOWNLOAD_DIR="$HOME/Downloads/FeliciaDL"
ICON_PATH="$APP_DIR/assets/icon.png"
PIPX_BIN="$HOME/.local/bin"
SYSTEM_BIN="/usr/local/bin"

print_header() {
  echo -e "\n======================================"
  echo "  Installing FeliciaDL Downloader"
  echo "======================================"
}

check_python() {
  if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python 3 before proceeding."
    exit 1
  fi
}

install_dependencies() {
  echo -e "\n📦 Installing system dependencies..."
  if command -v yay &> /dev/null; then
    yay -S --needed yt-dlp ffmpeg tk zenity python-pipx python-ttkbootstrap --noconfirm
  elif command -v apt &> /dev/null; then
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv pipx ffmpeg yt-dlp python3-tk zenity python3-pil.imagetk
    export PATH="$HOME/.local/bin:$PATH"
  else
    echo "❌ Unsupported package manager. Please install the required packages manually."
    exit 1
  fi
}

install_python_tools() {
  echo -e "\n📦 Installing Python apps with pipx..."
  pipx ensurepath

  echo "➡️ Upgrading or installing gallery-dl..."
  pipx upgrade gallery-dl || pipx install --force gallery-dl

  echo "➡️ Upgrading or installing spotdl..."
  pipx upgrade spotdl || pipx install --force spotdl

  echo -e "\n📦 Installing ttkbootstrap into user site..."
  sudo python3 -m pip install ttkbootstrap --break-system-packages
}

symlink_binaries() {
  echo -e "\n🔗 Symlinking pipx binaries..."
  for bin in gallery-dl spotdl; do
    if [ -f "$PIPX_BIN/$bin" ]; then
      sudo ln -sf "$PIPX_BIN/$bin" "$SYSTEM_BIN/$bin"
      echo "✔ Linked $bin → $SYSTEM_BIN/$bin"
    else
      echo "⚠️  $bin not found in $PIPX_BIN"
    fi
  done
}

install_app_files() {
  echo -e "\n📁 Copying application files to $APP_DIR..."
  sudo mkdir -p "$APP_DIR"
  sudo cp downloader.py downloader_gui.py "$APP_DIR/"

  echo "📁 Copying assets..."
  if [ -d "assets" ]; then
    sudo mkdir -p "$APP_DIR/assets"
    sudo cp -r assets/* "$APP_DIR/assets/"
  fi
}

install_launcher() {
  echo -e "\n🔗 Installing launcher to $LAUNCHER..."
  sudo cp feliciadl "$LAUNCHER"
  sudo chmod +x "$LAUNCHER"
}

install_desktop_entry() {
  echo -e "\n🖥️ Registering desktop shortcut..."
  mkdir -p "$(dirname "$DESKTOP_FILE")"
  ICON_LINE="Icon=utilities-terminal"
  [ -f "$ICON_PATH" ] && ICON_LINE="Icon=$ICON_PATH"

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

create_config_files_if_missing() {
  echo -e "\n⚙️  Ensuring config files exist..."
  mkdir -p "$CONFIG_DIR"

  if [ ! -f "$CONFIG_FILE" ]; then
    echo "Creating default config.json"
    echo "{\"download_dir\": \"$DEFAULT_DOWNLOAD_DIR\", \"theme\": \"darkly\"}" > "$CONFIG_FILE"
  else
    echo "✔ config.json already exists."
  fi

  if [ -f "$AUTOMATIC_FILE_SRC" ]; then
    echo "Copying automatic.json to config directory (overwrite)…"
    cp -f "$AUTOMATIC_FILE_SRC" "$AUTOMATIC_FILE_DEST"
    # If you run the installer via sudo and want the file owned by the real user:
    [ -n "$SUDO_USER" ] && chown "$SUDO_USER:$SUDO_USER" "$AUTOMATIC_FILE_DEST" || true
  else
    echo "⚠️  automatic.json not found in source directory, skipping copy."
  fi

}

print_footer() {
  echo -e "\n✅ FeliciaDL installed successfully!"
  echo "📦 Run in terminal: feliciadl"
  echo "📂 Or launch from Start Menu: FeliciaDL"
}

# Run installation steps
print_header
check_python
install_dependencies
install_python_tools
symlink_binaries
install_app_files
install_launcher
install_desktop_entry
create_config_files_if_missing
print_footer