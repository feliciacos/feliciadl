#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

APP_NAME = "FeliciaDL"
BASE_DIR = Path(__file__).resolve().parent
BIN_DIR = BASE_DIR / "bin"

APPDATA_DIR = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
CONFIG_DIR = APPDATA_DIR / APP_NAME
CONFIG_PATH = CONFIG_DIR / "config.json"
YTDLP_CONFIG_PATH = CONFIG_DIR / "yt-dlp.conf"
DEFAULT_PATH = Path.home() / "Downloads" / APP_NAME


def load_config():
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
    return {"download_dir": str(DEFAULT_PATH)}


def save_config(config):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def ensure_dirs(base):
    base = Path(base)

    folders = [
        base,
        base / "downloaded" / "youtube-dl-video",
        base / "downloaded" / "youtube-dl-audio",
        base / "downloaded" / "spotdl",
        base / "downloaded" / "gallery-dl",
        base / "downloaded" / "other-videos",
        base / "log",
        CONFIG_DIR,
    ]

    for path in folders:
        path.mkdir(parents=True, exist_ok=True)

    if not YTDLP_CONFIG_PATH.exists():
        YTDLP_CONFIG_PATH.write_text("# yt-dlp config\n", encoding="utf-8")


def log_action(base, tool, url):
    log_path = Path(base) / "log" / "download.log"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {tool}: {url}\n")


def build_runtime_env():
    env = os.environ.copy()
    env["PATH"] = str(BIN_DIR) + os.pathsep + env.get("PATH", "")
    return env


def find_executable(name):
    found = shutil.which(name)
    if found:
        return found

    exe_map = {
        "yt-dlp": "yt-dlp.exe",
        "gallery-dl": "gallery-dl.exe",
        "spotdl": "spotdl.exe",
        "ffmpeg": "ffmpeg.exe",
        "ffprobe": "ffprobe.exe",
    }

    exe_name = exe_map.get(name, f"{name}.exe")

    local_path = BIN_DIR / exe_name
    if local_path.exists():
        return str(local_path)

    local_plain = BIN_DIR / name
    if local_plain.exists():
        return str(local_plain)

    return None


def find_ffmpeg_location():
    local_ffmpeg = BIN_DIR / "ffmpeg.exe"
    if local_ffmpeg.exists():
        return str(BIN_DIR)

    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return str(Path(system_ffmpeg).resolve().parent)

    return None


def main():
    parser = argparse.ArgumentParser(description="FeliciaDL CLI")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--yt-dlp-video")
    group.add_argument("--yt-dlp-audio")
    group.add_argument("--gallery-dl")
    group.add_argument("--spotdl")
    group.add_argument("--videoother")

    parser.add_argument("--downloadpath")
    parser.add_argument("--resetpath", action="store_true")

    args = parser.parse_args()
    config = load_config()

    if args.resetpath:
        config["download_dir"] = str(DEFAULT_PATH)
        save_config(config)
        print("✔️ Reset path")

    if args.downloadpath:
        base = Path(args.downloadpath).expanduser() / APP_NAME
        config["download_dir"] = str(base)
        save_config(config)
    else:
        base = Path(config["download_dir"]).expanduser()

    ensure_dirs(base)

    yt_dlp = find_executable("yt-dlp")
    gallery_dl = find_executable("gallery-dl")
    spotdl = find_executable("spotdl")
    ffmpeg_location = find_ffmpeg_location()
    ffmpeg_exe = find_executable("ffmpeg")

    if args.yt_dlp_video or args.yt_dlp_audio or args.videoother:
        if not yt_dlp:
            raise SystemExit("yt-dlp was not found in PATH or win\\bin")

    if args.gallery_dl and not gallery_dl:
        raise SystemExit("gallery-dl was not found in PATH or win\\bin")

    if args.spotdl and not spotdl:
        raise SystemExit("spotdl was not found in PATH or win\\bin")

    yt_dlp_base = [yt_dlp, "--config-location", str(YTDLP_CONFIG_PATH)]
    if ffmpeg_location:
        yt_dlp_base += ["--ffmpeg-location", ffmpeg_location]

    cmd = []
    tool = ""
    url = ""

    if args.yt_dlp_video:
        tool = "YouTube Video"
        url = args.yt_dlp_video

        fmt = "bestvideo+bestaudio/best" if ffmpeg_location else "best"
        if not ffmpeg_location:
            print("⚠️ No ffmpeg found. Falling back to single-file download.")

        cmd = yt_dlp_base + [
            "-f", fmt,
            "-o", "%(title)s.%(ext)s",
            "-P", str(base / "downloaded" / "youtube-dl-video"),
            url,
        ]

    elif args.yt_dlp_audio:
        tool = "YouTube Audio"
        url = args.yt_dlp_audio

        cmd = yt_dlp_base + [
            "-x", "--audio-format", "mp3",
            "-o", "%(title)s.%(ext)s",
            "-P", str(base / "downloaded" / "youtube-dl-audio"),
            url,
        ]

    elif args.gallery_dl:
        tool = "Gallery-DL"
        url = args.gallery_dl

        cmd = [
            gallery_dl,
            "-d", str(base / "downloaded" / "gallery-dl"),
            url,
        ]

    elif args.spotdl:
        tool = "SpotDL"
        url = args.spotdl

        cmd = [
            spotdl,
            "download",
            url,
            "--output",
            str(base / "downloaded" / "spotdl"),
        ]

        if ffmpeg_exe:
            cmd += ["--ffmpeg", ffmpeg_exe]

    elif args.videoother:
        tool = "Other Video"
        url = args.videoother

        fmt = "bestvideo+bestaudio/best" if ffmpeg_location else "best"
        if not ffmpeg_location:
            print("⚠️ No ffmpeg found. Falling back to single-file download.")

        cmd = yt_dlp_base + [
            "-f", fmt,
            "-o", "%(title)s.%(ext)s",
            "-P", str(base / "downloaded" / "other-videos"),
            url,
        ]

    print("🚀 Running:", " ".join(cmd))

    try:
        subprocess.run(cmd, check=True, env=build_runtime_env())
        log_action(base, tool, url)
        print("✅ Done")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: command failed with exit code {e.returncode}")
    except FileNotFoundError as e:
        print(f"❌ Error: missing executable: {e}")
    except Exception as e:
        print("❌ Error:", e)


if __name__ == "__main__":
    main()