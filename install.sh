#!/bin/bash

echo "🔧 Installing FeliciaDL..."

# Install dependencies
yay -S --needed yt-dlp ffmpeg tk python-pipx --noconfirm || exit 1
pipx install gallery-dl
pipx install spotdl

# Create app dir
sudo mkdir -p /opt/feliciadl
sudo cp downloader.py downloader_gui.py /opt/feliciadl

# Preserve config
if [ ! -f /opt/feliciadl/config.json ]; then
    echo "{\"download_dir\": \"$(echo $HOME)/Downloads\"}" | sudo tee /opt/feliciadl/config.json > /dev/null
    echo "🧩 Created config.json with default path."
else
    echo "⚠️  config.json already exists, preserving user settings."
fi

# Install launcher
sudo cp feliciadl /usr/bin/feliciadl
sudo chmod +x /usr/bin/feliciadl

# Install .desktop entry
mkdir -p ~/.local/share/applications
cp feliciadl.desktop ~/.local/share/applications/
update-desktop-database ~/.local/share/applications/

echo "✅ FeliciaDL installed successfully!"
