# FeliciaDL

FeliciaDL is a simple graphical and command-line downloader built for Linux. It wraps powerful tools like `yt-dlp`, `gallery-dl`, and `spotdl` into a unified, user-friendly interface — both GUI and CLI.

## Features

- Download YouTube videos or extract audio using `yt-dlp`
- Download music tracks from Spotify using `spotdl`
- Download image galleries from supported sites using `gallery-dl`
- Clean GUI with theme selector and folder controls
- CLI interface with clearly named flags
- Persistent settings stored in `~/.config/feliciadl/`
- Output log with auto-scroll and command history
- Smart output organization (no brace-named folders)

---

## Installation

Tested on Arch Linux. Installation is handled via a single script:

```bash
git clone https://github.com/feliciacos/feliciadl
cd feliciadl
chmod +x install.sh
./install.sh
```

This script:

- Installs dependencies (`yt-dlp`, `gallery-dl`, `spotdl`, `ffmpeg`, `tk`, `zenity`, `ttkbootstrap`)
- Copies your app files to `/opt/feliciadl/`
- Installs a launcher to `/usr/bin/feliciadl`
- Registers a `.desktop` entry for the Start Menu
- Creates an initial config if none exists

---

## Usage

### CLI

```bash
feliciadl --yt-dlp-video <url>
feliciadl --yt-dlp-audio <url>
feliciadl --spotdl <url>
feliciadl --gallery-dl <url>
feliciadl --videoother <url>
```

#### Optional arguments:

- `--downloadpath <path>` — override the default folder
- `--resetpath` — reset to `~/Downloads/FeliciaDL`

#### Example:

```bash
feliciadl --yt-dlp-audio https://youtube.com/watch?v=abc123 --downloadpath /mnt/media
```

### GUI

Launch from the terminal:
```bash
feliciadl
```

Or find **FeliciaDL** in your Start Menu under **Multimedia** or **Utilities**.

---

## Configuration

Stored in:

```
~/.config/feliciadl/config.json
```

- `download_dir` — user-selected output folder
- `theme` — persistent GUI theme (e.g. `darkly`, `cyborg`, etc.)

Logs are written to:

```
<download_path>/FeliciaDL/log/download.log
```

---

## Folder Layout

```
~/Downloads/FeliciaDL/
├── downloaded/
│   ├── youtube-dl-video/
│   ├── youtube-dl-audio/
│   ├── spotdl/
│   └── other-videos/
└── log/
    └── download.log
```

---

## Dependencies

- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [spotDL](https://github.com/spotDL/spotify-downloader)
- [gallery-dl](https://github.com/mikf/gallery-dl)
- [ffmpeg](https://ffmpeg.org/)
- `tkinter`, `zenity`, and [`ttkbootstrap`](https://github.com/israel-dryer/ttkbootstrap)

---

## License

MIT License. See the [LICENSE](LICENSE) file.

---

## Author

Created by [@feliciacos](https://github.com/feliciacos)