# FeliciaDL

**FeliciaDL** is a simple graphical **and** command-line downloader built for Linux. It wraps powerful tools like `yt-dlp`, `gallery-dl`, and `spotdl` into a unified, user-friendly interface.

Whether you're a CLI nerd or prefer clicking buttons, FeliciaDL has you covered.

---

## Features

- Download YouTube videos or audio using `yt-dlp`
- Download Spotify tracks and albums using `spotdl`
- Download galleries and supported sites via `gallery-dl`
- Easy theme switching (`ttkbootstrap` skins)
- Persistent settings and logs
- Clean folder layout with automatic subdirectory sorting
- Scrollable job status with real-time progress bars
- Automatic downloader detection via `automatic.json`
- Fully native Linux shell integration (Start Menu & launcher)

---

## Installation

Tested on **Arch** and **Ubuntu 24+**. Installation is handled via a single script:

```bash
git clone https://github.com/feliciacos/feliciadl
cd feliciadl
chmod +x install.sh
./install.sh

OR

wget https://github.com/feliciacos/feliciadl/archive/refs/heads/main.zip -O feliciadl.zip
unzip feliciadl.zip
cd feliciadl-main
chmod +x install.sh
./install.sh

What it does:

    Installs system dependencies:

        yt-dlp, spotdl, gallery-dl, ffmpeg, tk, zenity, and ttkbootstrap

    Copies application files to /opt/feliciadl/

    Installs a launcher to /usr/bin/feliciadl

    Adds a Start Menu entry (~/.local/share/applications/feliciadl.desktop)

    Creates a config file at ~/.config/feliciadl/ if missing

    Installs an automatic.json matcher for automatic backend routing

Usage
CLI Mode

feliciadl --yt-dlp-video <url>
feliciadl --yt-dlp-audio <url>
feliciadl --spotdl <url>
feliciadl --gallery-dl <url>
feliciadl --videoother <url>

Optional arguments:

    --downloadpath <path> — override the configured output folder

    --resetpath — reset folder to ~/Downloads/FeliciaDL

Example:

feliciadl --spotdl https://open.spotify.com/track/abc123 --downloadpath /mnt/media

GUI Mode

Launch from terminal:

feliciadl

Or find FeliciaDL in your system menu under Multimedia or Utilities.
GUI Features:

    Tool selection: yt-dlp, spotdl, gallery-dl, or automatic detection

    Bulk Mode: Download many URLs (line-separated)

    Progress tracking per job (✅/❌)

    Console output + scrollable status window

    Theming via dropdown (light/dark skins)

    Configurable download folder

    Logs visible via GUI

⚙️ Configuration

All user preferences and state are stored here:

~/.config/feliciadl/config.json

Default contents:

{
  "download_dir": "~/Downloads/FeliciaDL",
  "theme": "darkly"
}

Automatic backend mapping is handled by:

~/.config/feliciadl/automatic.json

You can add domain mappings like:

{
  "yt-dlp": ["youtube.com", "youtu.be", "rumble.com"],
  "gallery-dl": ["coomer.su", "hentai-cosplay-xxx.com"],
  "spotdl": ["spotify.com"]
}

🗂 Folder Layout

~/Downloads/FeliciaDL/
├── downloaded/
│   ├── youtube-dl-video/
│   ├── youtube-dl-audio/
│   ├── gallery-dl/
│   ├── spotdl/
│   └── other-videos/
└── log/
    └── download.log

🧹 Uninstall (WIP)

A script to fully uninstall FeliciaDL is included:

./uninstall.sh

It will:

    Remove /opt/feliciadl

    Remove /usr/bin/feliciadl

    Remove desktop shortcut

    Optionally prompt to remove your config and logs

    ⚠️ Note: This uninstall script is untested on all platforms. Please use at your own risk.

Dependencies

    yt-dlp

    gallery-dl

    spotDL

    ffmpeg

    ttkbootstrap

    tkinter, zenity, pipx (used for GUI and packaging)

📄 License

MIT License. See the LICENSE file.
👤 Author

Created by @feliciacos


---
