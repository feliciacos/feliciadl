#!/bin/bash

APP_DIR="/opt/feliciadl"
LAUNCHER="/usr/bin/feliciadl"
DESKTOP_FILE="$HOME/.local/share/applications/feliciadl.desktop"
CONFIG_DIR="$HOME/.config/feliciadl"

echo "=================================="
echo " Uninstalling FeliciaDL Downloader"
echo "=================================="

# Remove app files
if [ -d "$APP_DIR" ]; then
    echo "Removing application directory: $APP_DIR"
    sudo rm -rf "$APP_DIR"
else
    echo "✔ Application directory not found (already removed)"
fi

# Remove CLI launcher
if [ -f "$LAUNCHER" ]; then
    echo "Removing launcher: $LAUNCHER"
    sudo rm -f "$LAUNCHER"
else
    echo "✔ Launcher not found (already removed)"
fi

# Remove desktop entry
if [ -f "$DESKTOP_FILE" ]; then
    echo "Removing desktop shortcut: $DESKTOP_FILE"
    rm -f "$DESKTOP_FILE"
else
    echo "✔ Desktop shortcut not found"
fi

# Ask if config should be deleted
if [ -d "$CONFIG_DIR" ]; then
    read -p "Do you want to remove your config and logs? ($CONFIG_DIR)? [y/N]: " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        echo "Removing config directory..."
        rm -rf "$CONFIG_DIR"
    else
        echo "✔ Skipping config removal"
    fi
else
    echo "✔ No config directory found"
fi

echo "✅ FeliciaDL has been uninstalled."
