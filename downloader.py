#!/usr/bin/env python3
import os
import sys
import subprocess
import json
from datetime import datetime
import argparse

DEFAULT_PATH = os.path.expanduser("~/Downloads/FeliciaDL")
CONFIG_PATH = "/opt/feliciadl/config.json"

# Load config or create default
def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {"download_dir": DEFAULT_PATH}

def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f)

def ensure_dirs(base):
    folders = [
        base,
        os.path.join(base, "downloaded/youtube-dl-video"),
        os.path.join(base, "downloaded/youtube-dl-audio"),
        os.path.join(base, "downloaded/spotdl"),
        os.path.join(base, "log")
    ]
    for path in folders:
        os.makedirs(path, exist_ok=True)

def log_action(base, tool, url):
    log_path = os.path.join(base, "log", "download.log")
    with open(log_path, "a") as f:
        f.write(f"[{datetime.now()}] {tool}: {url}\n")

def main():
    parser = argparse.ArgumentParser(
        prog="feliciadl",
        description="FeliciaDL CLI - Media downloader",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Examples:
  feliciadl --yt-dlp-video https://youtube.com/watch?v=abc123
  feliciadl --spotdl https://open.spotify.com/track/xyz
"""
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--yt-dlp-video", help="Download video using yt-dlp")
    group.add_argument("--yt-dlp-audio", help="Download audio using yt-dlp")
    group.add_argument("--gallery-dl", help="Download using gallery-dl")
    group.add_argument("--spotdl", help="Download using spotdl")
    group.add_argument("--videoother", help="Download with yt-dlp to current folder (generic use)")

    parser.add_argument("--downloadpath", help="Override the configured download location")
    parser.add_argument("--resetpath", action="store_true", help="Reset config to default ~/Downloads/FeliciaDL")

    args = parser.parse_args()

    config = load_config()

    if args.resetpath:
        config["download_dir"] = DEFAULT_PATH
        save_config(config)
        print("✔️  Download path reset to:", DEFAULT_PATH)

    if args.downloadpath:
        custom_path = os.path.abspath(args.downloadpath)
        config["download_dir"] = os.path.join(custom_path, "FeliciaDL")
        save_config(config)
        print("✔️  Download path set to:", config["download_dir"])

    base = config["download_dir"]
    ensure_dirs(base)

    if args.yt_dlp_video:
        tool = "Youtube-DL-Video"
        cmd = ["yt-dlp", "-P", os.path.join(base, "downloaded/youtube-dl-video"), args.yt_dlp_video]
        url = args.yt_dlp_video
    elif args.yt_dlp_audio:
        tool = "Youtube-DL-Audio"
        cmd = ["yt-dlp", "-x", "--audio-format", "mp3", "-P", os.path.join(base, "downloaded/youtube-dl-audio"), args.yt_dlp_audio]
        url = args.yt_dlp_audio
    elif args.gallery_dl:
        tool = "Gallery-DL"
        cmd = ["gallery-dl", "-d", os.path.join(base, "downloaded"), args.gallery_dl]
        url = args.gallery_dl
    elif args.spotdl:
        tool = "Spot-DL"
        cmd = ["spotdl", "download", args.spotdl, "--output", os.path.join(base, "downloaded/spotdl/{track_name}.{output_ext}")]
        url = args.spotdl
    elif args.videoother:
        tool = "Other-Videos"
        cmd = ["yt-dlp", args.videoother]
        url = args.videoother
    else:
        print("❌ No valid tool specified.")
        return

    print(f"🚀 Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        log_action(base, tool, url)
        print("✅ Download completed!")
    except subprocess.CalledProcessError:
        print("❌ Download failed.")

if __name__ == "__main__":
    main()
