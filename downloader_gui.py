#!/usr/bin/env python3
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import tkinter as tk
from tkinter import filedialog, messagebox

import ttkbootstrap as tb
from ttkbootstrap.constants import *
import tkinter.ttk as ttk

import json
import os
import platform
import re
import shutil
import urllib.request
from pathlib import Path
from tkinter import messagebox

import subprocess
import sys

IS_WINDOWS = sys.platform.startswith("win")

def _no_window_kwargs():
    if not IS_WINDOWS:
        return {}

    kwargs = {}
    kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    kwargs["startupinfo"] = startupinfo

    return kwargs

GITHUB_RELEASES = {
    "yt-dlp": "yt-dlp/yt-dlp",
    "gallery-dl": "mikf/gallery-dl",
    "spotdl": "spotDL/spotify-downloader",
}

UPDATE_TOOL_LABELS = {
    "yt-dlp": "YT-DLP",
    "gallery-dl": "Gallery-DL",
    "spotdl": "SpotDL",
}

def _normalize_version(v: str) -> str:
    v = (v or "").strip()
    v = v.lstrip("vV")
    return v

def _version_tuple(v: str):
    v = _normalize_version(v)
    nums = re.findall(r"\d+", v)
    return tuple(int(n) for n in nums) if nums else ()

def _is_newer(remote: str, local: str) -> bool:
    if not local:
        return True
    r = _version_tuple(remote)
    l = _version_tuple(local)
    if r and l:
        return r > l
    return _normalize_version(remote) != _normalize_version(local)

def _github_latest_release(repo: str) -> dict | None:
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "FeliciaDL-Updater",
        },
    )

    import ssl

    # Try normal SSL first
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        pass

    # Fallback (Windows SSL issues)
    try:
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(req, timeout=30, context=context) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

def _get_local_version(tool_name: str, exe_path: str | None) -> str | None:
    if not exe_path or not Path(exe_path).exists():
        return None

    try:
        proc = subprocess.run(
            [exe_path, "--version"],
            capture_output=True,
            text=True,
            timeout=20,
            shell=False,
            **_no_window_kwargs(),
        )
        text = (proc.stdout or proc.stderr or "").strip().splitlines()[0].strip()
        return _normalize_version(text)
    except Exception:
        return None
    
def _select_asset_for_tool(tool: str, release: dict) -> dict | None:
    assets = release.get("assets", []) or []
    machine = platform.machine().lower()

    def by_name(patterns):
        for pat in patterns:
            rx = re.compile(pat, re.IGNORECASE)
            for a in assets:
                name = a.get("name", "")
                if rx.fullmatch(name):
                    return a
        return None

    if tool == "yt-dlp":
        if machine in ("arm64", "aarch64"):
            asset = by_name([r"yt-dlp_arm64\.exe", r"yt-dlp.*arm64.*\.exe"])
        else:
            asset = by_name([r"yt-dlp\.exe", r"yt-dlp.*\.exe"])
        if asset:
            return asset

    elif tool == "gallery-dl":
        asset = by_name([r"gallery-dl\.exe", r"gallery-dl.*\.exe"])
        if asset:
            return asset

    elif tool == "spotdl":
        asset = by_name([
            r"spotdl-.*-win32\.exe",
            r"spotdl-.*-win64\.exe",
            r"spotdl.*\.exe",
        ])
        if asset:
            return asset

    return None

def _download_file(url: str, dest: Path, timeout: int = 120, retries: int = 3) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    import ssl

    last_error = None

    for attempt in range(1, retries + 1):
        try:
            if tmp.exists():
                try:
                    tmp.unlink()
                except Exception:
                    pass

            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "FeliciaDL-Updater",
                    "Accept": "*/*",
                },
            )

            try:
                response = urllib.request.urlopen(req, timeout=timeout)
            except Exception:
                response = urllib.request.urlopen(
                    req,
                    timeout=timeout,
                    context=ssl._create_unverified_context(),
                )

            with response, tmp.open("wb") as f:
                shutil.copyfileobj(response, f, length=1024 * 1024)

            if tmp.stat().st_size == 0:
                raise RuntimeError("Downloaded file is empty")

            tmp.replace(dest)
            return

        except Exception as e:
            last_error = e
            try:
                if tmp.exists():
                    tmp.unlink()
            except Exception:
                pass

            if attempt < retries:
                time.sleep(2 * attempt)
            else:
                raise last_error

def _current_tool_state():
    return {
        "yt-dlp": {
            "exe": find_executable("yt-dlp"),
            "current": _get_local_version("yt-dlp", find_executable("yt-dlp")),
        },
        "gallery-dl": {
            "exe": find_executable("gallery-dl"),
            "current": _get_local_version("gallery-dl", find_executable("gallery-dl")),
        },
        "spotdl": {
            "exe": find_executable("spotdl"),
            "current": _get_local_version("spotdl", find_executable("spotdl")),
        },
    }

def _status_widgets_for_tool(tool: str):
    return {
        "yt-dlp": (yt_status_label, yt_version_label, "YT-DLP"),
        "gallery-dl": (gallery_status_label, gallery_version_label, "Gallery-DL"),
        "spotdl": (spot_status_label, spot_version_label, "SpotDL"),
    }.get(tool, (None, None, tool.upper()))


def _mark_outdated(main_lbl, ver_lbl, title, current, latest):
    if main_lbl is None or ver_lbl is None:
        return
    main_lbl.config(text=f"{title} Outdated", foreground="red")
    ver_lbl.config(text=f"current: {current} -> new: {latest}")

def start_update_downloads(updates, close_after=True, on_complete=None, silent=False):
    """
    Download helper exes into bin.

    If close_after is True, the app asks the user to restart after updates.
    If close_after is False, the app stays open and refreshes tool status.
    """
    def worker():
        try:
            BIN_DIR.mkdir(parents=True, exist_ok=True)
            completed_messages = []

            for u in updates:
                dest = BIN_DIR / u["dest_name"]

                timeout = 600 if u["tool"] == "spotdl" else 120
                _download_file(u["asset_url"], dest, timeout=timeout, retries=3)

                completed_messages.append(f"{u['label']} is updated to version {u['latest']}")

                if u["tool"] == "spotdl":
                    for old in BIN_DIR.glob("spotdl-*.exe"):
                        try:
                            if old.name != "spotdl.exe":
                                old.unlink()
                        except Exception:
                            pass

            def done():
                for msg in completed_messages:
                    append_console(msg)

                if on_complete is not None:
                    on_complete()

                if close_after:
                    messagebox.showinfo(
                        "Update complete",
                        "The selected tools were updated.\n\nRestart FeliciaDL so the new files are picked up.",
                    )
                    root.destroy()
                else:
                    if not silent and not completed_messages:
                        append_console("Tools are up to date.")

            root.after(0, done)

        except Exception as e:
            root.after(0, lambda: messagebox.showerror("Update failed", str(e)))

    threading.Thread(target=worker, daemon=True).start()

def check_updates_on_startup():
    """
    Run once after the GUI is visible.

    Missing helper tools are installed automatically on startup.
    Existing helper tools that are outdated are also updated automatically.
    """
    def worker():
        try:
            local = _current_tool_state()
            updates = []

            for tool, repo in GITHUB_RELEASES.items():
                latest = _github_latest_release(repo)
                if not latest:
                    continue

                latest_tag = _normalize_version(latest.get("tag_name", ""))
                current = local[tool]["current"]
                exe_missing = not local[tool]["exe"]

                asset = _select_asset_for_tool(tool, latest)
                if asset is None:
                    continue

                dest_name = {
                    "yt-dlp": "yt-dlp.exe",
                    "gallery-dl": "gallery-dl.exe",
                    "spotdl": "spotdl.exe",
                }.get(tool, asset.get("name"))

                if exe_missing or not current or _is_newer(latest_tag, current):
                    updates.append({
                        "tool": tool,
                        "label": UPDATE_TOOL_LABELS[tool],
                        "current": current or "not installed",
                        "latest": latest_tag or latest.get("name", "unknown"),
                        "asset_name": asset.get("name"),
                        "asset_url": asset.get("browser_download_url"),
                        "dest_name": dest_name,
                    })

            if updates:
                def after_done():
                    refresh_tool_statuses_once()                
                root.after(
                    0,
                    lambda: start_update_downloads(
                        updates,
                        close_after=False,
                        on_complete=after_done,
                        silent=True,
                    ),
                )
            else:
                root.after(0, lambda: append_console("Tools are up to date."))

        except Exception:
            root.after(0, lambda: append_console("Tools are up to date."))

    threading.Thread(target=worker, daemon=True).start()

APP_NAME = "FeliciaDL"
BASE_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
BIN_DIR = BASE_DIR / "bin"

APPDATA_DIR = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
CONFIG_DIR = APPDATA_DIR / APP_NAME
CONFIG_PATH = CONFIG_DIR / "config.json"
YTDLP_CONFIG_PATH = CONFIG_DIR / "yt-dlp.conf"
AUTOMATIC_MAP_PATH = BASE_DIR / "automatic.json"
AUTOMATIC_MAP_FALLBACK = CONFIG_DIR / "automatic.json"

DEFAULT_PATH = Path.home() / "Downloads" / APP_NAME
APP_ICON_PATH = BASE_DIR / "assets" / "icon.png"
APP_LOGO_PATH = BASE_DIR / "assets" / "logo.png"
DEFAULT_THEME = "flatly"

status_font_main = ("TkDefaultFont", 10, "bold")
status_font_version = ("TkDefaultFont", 9, "italic")
status_color_version = "#888888"

active_jobs = 0
active_jobs_lock = threading.Lock()
resize_callbacks = []
resize_after_id = None

config = {}
automatic_map = {}
download_dir = None
bulk_mode = None
theme_selector = None
tool_selector = None
url_entry = None
url_box = None
download_entry = None
change_button = None
reset_button = None
output_box = None
status_canvas = None
status_list = None
status_parent = None
root = None

yt_status_label = None
yt_version_label = None
gallery_status_label = None
gallery_version_label = None
spot_status_label = None
spot_version_label = None

download_button = None
open_logs_button = None
open_folder_button = None
open_config_button = None


def load_config():
    try:
        if CONFIG_PATH.exists():
            with CONFIG_PATH.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
    except Exception:
        pass
    return {"download_dir": str(DEFAULT_PATH), "theme": DEFAULT_THEME}


def save_config(payload):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

def load_automatic_mapping():
    for path in (AUTOMATIC_MAP_PATH, AUTOMATIC_MAP_FALLBACK):
        try:
            if path.exists():
                with path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
        except Exception:
            pass
    return {}


def ensure_ytdlp_config():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not YTDLP_CONFIG_PATH.exists():
        YTDLP_CONFIG_PATH.write_text(
            "# yt-dlp config\n# Example: --cookies cookies.txt\n",
            encoding="utf-8",
        )


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
    for folder in folders:
        folder.mkdir(parents=True, exist_ok=True)
    ensure_ytdlp_config()

def build_runtime_env():
    env = os.environ.copy()
    bin_dir = str(BIN_DIR)
    current_path = env.get("PATH", "")
    env["PATH"] = bin_dir + os.pathsep + current_path
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
    candidate = BIN_DIR / exe_map.get(name, f"{name}.exe")
    if candidate.exists():
        return str(candidate)

    candidate_plain = BIN_DIR / name
    if candidate_plain.exists():
        return str(candidate_plain)

    return None


def find_ffmpeg_location():
    ffmpeg_local = BIN_DIR / "ffmpeg.exe"
    if ffmpeg_local.exists():
        return str(BIN_DIR)

    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return str(Path(ffmpeg_path).resolve().parent)

    return None


def run_capture(cmd, timeout=20):
    try:
        p = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
            **_no_window_kwargs(),
        )
        return (p.stdout or "") + (p.stderr or "")
    except FileNotFoundError:
        return "__MISSING__"
    except Exception as e:
        return f"__ERR__ {e}"


def _norm_ver(s):
    s = s.strip().strip(".").strip(",")
    if "@" in s:
        s = s.split("@", 1)[-1]
    return s


def _set_label(main_lbl, ver_lbl, title, version, state="ready", note=None):
    color_map = {
        "ready": "green",
        "missing": "red",
        "outdated": "red",
        "installing": "orange",
    }
    label_map = {
        "ready": "Ready",
        "missing": "Missing",
        "outdated": "Out-of-date",
        "installing": "Installing",
    }

    color = color_map.get(state, "green")
    label_text = label_map.get(state, "Ready")

    main_lbl.config(
        text=f"{title} {label_text}",
        foreground=color,
    )

    ver_text = f"version {version}"
    if note:
        ver_text += f" ({note})"
    ver_lbl.config(text=ver_text)

def check_tool_status(tool_name, exe_name, main_lbl, ver_lbl):
    exe = find_executable(exe_name)
    if not exe:
        root.after(0, lambda: _set_label(main_lbl, ver_lbl, tool_name, "not found", state="missing"))
        return

    out = run_capture([exe, "--version"], timeout=20).strip()
    first = out.splitlines()[0].strip() if out else "unknown"
    root.after(0, lambda: _set_label(main_lbl, ver_lbl, tool_name, first, state="ready"))

def refresh_tool_statuses_once():
    def worker():
        check_tool_status("YT-DLP", "yt-dlp", yt_status_label, yt_version_label)
        check_tool_status("Gallery-DL", "gallery-dl", gallery_status_label, gallery_version_label)
        check_tool_status("SpotDL", "spotdl", spot_status_label, spot_version_label)

    threading.Thread(target=worker, daemon=True).start()


def scroll_status_to_bottom():
    if status_canvas is not None:
        status_canvas.update_idletasks()
        status_canvas.yview_moveto(1.0)


def append_console(text):
    def _append():
        output_box.config(state=tk.NORMAL)
        output_box.insert(tk.END, text + "\n")
        output_box.see(tk.END)
        output_box.config(state=tk.DISABLED)

    root.after(0, _append)


def open_folder(path):
    try:
        os.startfile(str(path))
    except Exception as e:
        messagebox.showerror("Open Folder", str(e))


def open_config_folder():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    open_folder(CONFIG_DIR)


def open_link(url):
    webbrowser.open_new_tab(url)


def update_label_width(label_widget, parent_widget, reserved_right_px=200):
    parent_widget.update_idletasks()
    parent_width = parent_widget.winfo_width()
    if parent_width <= 1:
        return
    char_width = 8
    usable_width = max(180, parent_width - reserved_right_px)
    label_widget.config(width=max(20, usable_width // char_width))


def debounced_resize_handler(event=None):
    global resize_after_id
    if resize_after_id:
        root.after_cancel(resize_after_id)

    def _apply():
        for cb in resize_callbacks:
            try:
                cb()
            except Exception:
                pass

    resize_after_id = root.after(150, _apply)


def job_started():
    global active_jobs
    with active_jobs_lock:
        was_zero = active_jobs == 0
        active_jobs += 1
    if was_zero:
        root.after(0, lock_controls)


def job_finished():
    global active_jobs
    with active_jobs_lock:
        active_jobs = max(0, active_jobs - 1)
        now_zero = active_jobs == 0
    if now_zero:
        root.after(0, unlock_controls)


def lock_controls():
    for widget in [
        theme_selector,
        tool_selector,
        url_entry,
        url_box,
        download_entry,
        change_button,
        reset_button,
        download_button,
        open_folder_button,
        open_logs_button,
        open_config_button,
    ]:
        try:
            widget.config(state="disabled")
        except Exception:
            pass


def unlock_controls():
    for widget, state in [
        (theme_selector, "readonly"),
        (tool_selector, "readonly"),
        (url_entry, "normal"),
        (url_box, "normal"),
        (download_entry, "normal"),
        (change_button, "normal"),
        (reset_button, "normal"),
        (download_button, "normal"),
        (open_folder_button, "normal"),
        (open_logs_button, "normal"),
        (open_config_button, "normal"),
    ]:
        try:
            widget.config(state=state)
        except Exception:
            pass


def normalize_download_dir(raw_path):
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def ensure_download_root():
    base = normalize_download_dir(download_dir.get())
    ensure_dirs(base)
    return base


def resolve_automatic_backend(url):
    parsed = urlparse(url)
    host = (parsed.netloc or "").lower().split(":")[0]
    host = host.removeprefix("www.")

    if not host:
        return None

    backend_map = {
        "yt-dlp": "Youtube-DL-Video",
        "gallery-dl": "Gallery-DL",
        "spotdl": "Spot-DL",
    }

    for backend, domains in automatic_map.items():
        if not isinstance(domains, (list, tuple, set)):
            domains = [domains]

        for d in domains:
            d = str(d).lower().strip().removeprefix("www.")
            if not d:
                continue

            if d in host or host in d:
                return backend_map.get(backend, "Other-Videos")
    return None


def build_command(tool, url, base):
    base_video = base / "downloaded" / "youtube-dl-video"
    base_audio = base / "downloaded" / "youtube-dl-audio"
    base_spot = base / "downloaded" / "spotdl"
    base_gallery = base / "downloaded" / "gallery-dl"
    base_other = base / "downloaded" / "other-videos"

    yt_dlp = find_executable("yt-dlp")
    gallery_dl = find_executable("gallery-dl")
    spotdl = find_executable("spotdl")
    ffmpeg_location = find_ffmpeg_location()

    if tool == "Automatic":
        resolved_tool = resolve_automatic_backend(url)
        if not resolved_tool:
            return None, None, "Automatic mode is not available for this URL."
    else:
        resolved_tool = tool

    if resolved_tool in ("Youtube-DL-Video", "Other-Videos", "Youtube-DL-Audio") and not yt_dlp:
        return None, None, "yt-dlp is not installed and was not found in win\\bin."

    if resolved_tool == "Gallery-DL" and not gallery_dl:
        return None, None, "gallery-dl is not installed and was not found in win\\bin."
    if resolved_tool == "Spot-DL":
        ffmpeg_exe = find_executable("ffmpeg")
        cmd = [
            spotdl,
            "download",
            url,
            "--output", str(base_spot),
        ]
        if ffmpeg_exe:
            cmd += ["--ffmpeg", ffmpeg_exe]
        return cmd, resolved_tool, None

    yt_base = [yt_dlp, "--config-location", str(YTDLP_CONFIG_PATH)]
    if ffmpeg_location:
        yt_base += ["--ffmpeg-location", ffmpeg_location]

    if resolved_tool == "Youtube-DL-Video":
        fmt = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]"
        if not ffmpeg_location:
            fmt = "best[ext=mp4]/best"
        cmd = yt_base + [
            "-f", fmt,
            "-o", "%(title)s.%(ext)s",
            "-P", str(base_video),
            url,
        ]
        return cmd, resolved_tool, None

    if resolved_tool == "Youtube-DL-Audio":
        cmd = yt_base + [
            "-x", "--audio-format", "mp3",
            "-o", "%(title)s.%(ext)s",
            "-P", str(base_audio),
            url,
        ]
        return cmd, resolved_tool, None

    if resolved_tool == "Gallery-DL":
        cmd = [
            gallery_dl,
            "-d", str(base_gallery),
            url,
        ]
        return cmd, resolved_tool, None

    if resolved_tool == "Spot-DL":
        cmd = [
            spotdl,
            "download",
            url,
            "--output", str(base_spot),
        ]
        return cmd, resolved_tool, None

    if resolved_tool == "Other-Videos":
        fmt = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]"
        if not ffmpeg_location:
            fmt = "best[ext=mp4]/best"
        cmd = yt_base + [
            "-f", fmt,
            "-o", "%(title)s.%(ext)s",
            "-P", str(base_other),
            url,
        ]
        return cmd, resolved_tool, None

    return None, None, f"Unknown tool: {resolved_tool}"


def make_status_row(prefix):
    ready = threading.Event()
    holder = {}

    def _create():
        row = ttk.Frame(status_list)
        row.pack(fill=tk.X, pady=2)

        row.grid_columnconfigure(0, weight=1)

        label = ttk.Label(
            row,
            text=prefix,
            anchor="w",
            justify="left",
            wraplength=600,
        )
        stop_button = ttk.Button(row, text="Stop")
        bar = ttk.Progressbar(row, mode="indeterminate", maximum=100)

        label.grid(row=0, column=0, sticky="w", padx=(0, 10))
        stop_button.grid(row=0, column=1, sticky="e", padx=(5, 2))
        bar.grid(row=0, column=2, sticky="e", padx=(2, 5))

        bar.start()

        holder["row"] = row
        holder["label"] = label
        holder["stop_button"] = stop_button
        holder["bar"] = bar
        ready.set()
        scroll_status_to_bottom()

    root.after(0, _create)
    ready.wait()
    return holder


def finish_row(row_data, success=True, text=None):
    def _finish():
        try:
            row_data["bar"].stop()
            row_data["bar"].config(mode="determinate", value=100 if success else 0)
        except Exception:
            pass

        if text:
            try:
                row_data["label"].config(text=text)
            except Exception:
                pass

        try:
            row_data["stop_button"].destroy()
        except Exception:
            pass

        scroll_status_to_bottom()

    root.after(0, _finish)


def build_runtime_env():
    env = os.environ.copy()
    env["PATH"] = str(BIN_DIR) + os.pathsep + env.get("PATH", "")
    return env

def kill_process_tree(proc):
    if proc is None or proc.poll() is not None:
        return
    try:
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
            capture_output=True,
            text=True,
            check=False,
            **_no_window_kwargs(),
        )
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def run_process_for_url(url, tool, base, prefix=None, total=None, index=None):
    cmd, resolved_tool, error = build_command(tool, url, base)
    if error:
        root.after(0, lambda: messagebox.showerror("Download Error", error))
        return

    job_started()
    row = make_status_row(prefix or f"⏳ {tool}: {url}")
    finished = False
    process_holder = {"process": None}

    def finish_once(success, text):
        nonlocal finished
        if finished:
            return
        finished = True
        finish_row(row, success=success, text=text)
        job_finished()

    try:
        title = f"⏳ [{index}/{total}] {tool}: {url}" if total else f"⏳ {tool}: {url}"
        if tool == "Automatic":
            title = (
                f"⏳ [{index}/{total}] Automatic ({resolved_tool}): {url}"
                if total else f"⏳ Automatic ({resolved_tool}): {url}"
            )
        row["label"].config(text=title)

        log_path = base / "log" / "download.log"

        def stop_process():
            proc = process_holder.get("process")
            if proc and proc.poll() is None:
               if messagebox.askyesno("Stop Download", f"Force stop this job?\n\n{resolved_tool}\n{url}"):
                    kill_process_tree(proc)
                    append_console(f"⛔ Stopped: {resolved_tool} → {url}")
                    finish_once(False, f"⛔ Stopped: {resolved_tool}")

        root.after(0, lambda: row["stop_button"].config(command=stop_process))

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            shell=False,
            env=build_runtime_env(),
            **_no_window_kwargs(),
        )
        process_holder["process"] = process

        for line in process.stdout:
            line = line.rstrip()
            if line:
                append_console(line)

        process.wait()

        with log_path.open("a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat(sep=' ', timespec='seconds')}] {resolved_tool}: {url}\n")

        if process.returncode == 0:
            finish_once(True, f"✅ Finished: {resolved_tool}")
            root.after(0, lambda: messagebox.showinfo("Download", f"✅ Finished:\n{resolved_tool}\n{url}"))
        else:
            finish_once(False, f"❌ Failed: {resolved_tool}")
            root.after(
                0,
                lambda: messagebox.showerror(
                    "Download Failed",
                    f"❌ Download failed (exit code {process.returncode}).\n\n{resolved_tool}\n{url}",
                ),
            )

    except Exception as e:
        finish_once(False, "❌ Exception")
        root.after(0, lambda: messagebox.showerror("Download Error", str(e)))
        append_console(f"❌ Exception: {e}")

def run_download():
    tool = tool_selector.get()
    raw_text = url_box.get("1.0", tk.END).strip() if bulk_mode.get() else url_entry.get().strip()
    urls = [u.strip() for u in raw_text.splitlines() if u.strip()]

    if not urls:
        messagebox.showerror("Missing URL", "Please enter at least one URL.")
        return

    if bulk_mode.get():
        url_box.delete("1.0", tk.END)
    else:
        url_entry.delete(0, tk.END)

    base = ensure_download_root()

    def worker():
        total = len(urls)
        if total == 1:
            run_process_for_url(urls[0], tool, base)
        else:
            for i, url in enumerate(urls, start=1):
                run_process_for_url(url, tool, base, total=total, index=i)

    threading.Thread(target=worker, daemon=True).start()

def toggle_bulk_mode():
    if bulk_mode.get():
        url_entry.pack_forget()
        url_box.pack(fill=tk.X)
    else:
        url_box.pack_forget()
        url_entry.pack(fill=tk.X)


def on_exit():
    if active_jobs > 0:
        if not messagebox.askyesno("Quit", "⚠️ Downloads are still running. Are you sure you want to exit?"):
            return
    root.destroy()


def browse_folder():
    selected = filedialog.askdirectory(parent=root, title="Select Download Folder")
    if selected:
        full_path = Path(selected) / APP_NAME
        full_path.mkdir(parents=True, exist_ok=True)
        download_dir.set(str(full_path))
        config["download_dir"] = str(full_path)
        save_config(config)


def reset_folder():
    download_dir.set(str(DEFAULT_PATH))
    config["download_dir"] = str(DEFAULT_PATH)
    save_config(config)


def on_theme_change(event=None):
    config["theme"] = theme_selector.get()
    save_config(config)
    root.destroy()
    os.execl(sys.executable, sys.executable, *sys.argv)


def build_gui():
    global root, download_dir, bulk_mode, theme_selector, tool_selector, url_entry, url_box
    global download_entry, change_button, reset_button, output_box, status_canvas, status_list
    global yt_status_label, yt_version_label, gallery_status_label, gallery_version_label
    global spot_status_label, spot_version_label, download_button, open_logs_button
    global open_folder_button, open_config_button, status_parent

    global config, automatic_map
    config = load_config()
    automatic_map = load_automatic_mapping()
    ensure_ytdlp_config()

    theme = config.get("theme", DEFAULT_THEME)

    root = tb.Window(themename=theme)
    root.title("FeliciaDL")
    root.geometry("1000x600")
    root.protocol("WM_DELETE_WINDOW", on_exit)
    root.bind("<Configure>", debounced_resize_handler)

    try:
        icon = tk.PhotoImage(file=str(APP_ICON_PATH))
        root.iconphoto(False, icon)
        root._icon_ref = icon
    except Exception:
        pass

    download_dir = tk.StringVar(value=config.get("download_dir", str(DEFAULT_PATH)))
    bulk_mode = tk.BooleanVar(value=False)

    main_frame = tb.Frame(root, padding=10)
    main_frame.pack(fill=tk.BOTH, expand=True)

    top_frame = ttk.Frame(main_frame)
    top_frame.pack(fill=tk.X, pady=(0, 10))

    ttk.Label(top_frame, text="Theme:").pack(side=tk.LEFT)

    style = tb.Style()
    theme_selector = ttk.Combobox(
        top_frame,
        values=sorted(style.theme_names()),
        state="readonly",
        width=20,
    )
    theme_selector.set(theme)
    theme_selector.pack(side=tk.LEFT, padx=5)
    theme_selector.bind("<<ComboboxSelected>>", on_theme_change)

    open_config_button = ttk.Button(top_frame, text="Open Config Folder", command=open_config_folder)
    open_config_button.pack(side=tk.LEFT, padx=10)

    open_logs_button = ttk.Button(top_frame, text="Open Logs", command=lambda: open_folder(Path(download_dir.get()) / "log"))
    open_logs_button.pack(side=tk.LEFT, padx=5)

    content_frame = ttk.Frame(main_frame)
    content_frame.pack(fill=tk.BOTH, expand=True)

    left_frame = ttk.Frame(content_frame)
    left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

    right_frame = ttk.Frame(content_frame)
    right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

    try:
        logo_img = tk.PhotoImage(file=str(APP_LOGO_PATH))
        scaled_logo = logo_img.subsample(4, 4)
        logo_label = tk.Label(left_frame, image=scaled_logo)
        logo_label.pack(anchor="n")
        left_frame._logo_ref = scaled_logo
    except Exception:
        pass

    ttk.Separator(left_frame).pack(fill=tk.X, pady=(6, 6))

    link_font = ("TkDefaultFont", 9)
    link_color = status_color_version

    link_frame = ttk.Frame(left_frame)
    link_frame.pack(anchor="w", pady=4, fill=tk.X)

    yt_sites = ttk.Label(
        link_frame,
        text="Supported sites (yt-dlp)",
        font=link_font,
        foreground=link_color,
        cursor="hand2",
        anchor="w",
    )
    yt_sites.pack(anchor="w", pady=2)
    yt_sites.bind("<Button-1>", lambda e: open_link("https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md"))

    gd_sites = ttk.Label(
        link_frame,
        text="Supported sites (gallery-dl)",
        font=link_font,
        foreground=link_color,
        cursor="hand2",
        anchor="w",
    )
    gd_sites.pack(anchor="w", pady=2)
    gd_sites.bind("<Button-1>", lambda e: open_link("https://github.com/mikf/gallery-dl/blob/master/docs/supportedsites.md"))

    ttk.Separator(left_frame).pack(fill=tk.X, pady=(8, 6))

    def make_status_pair(parent, title):
        frame = ttk.Frame(parent)
        frame.pack(anchor="w", pady=(0, 4), fill=tk.X)
        main_label = ttk.Label(frame, text=f"{title} Checking...", font=status_font_main, anchor="w")
        main_label.pack(anchor="w")
        version_label = ttk.Label(
            frame,
            text="version …",
            font=status_font_version,
            foreground=status_color_version,
            anchor="w",
        )
        version_label.pack(anchor="w")
        return main_label, version_label

    yt_status_label, yt_version_label = make_status_pair(left_frame, "YT-DLP")
    gallery_status_label, gallery_version_label = make_status_pair(left_frame, "Gallery-DL")
    spot_status_label, spot_version_label = make_status_pair(left_frame, "SpotDL")

    ttk.Label(right_frame, text="Select Tool:").pack(anchor="w")
    tool_selector = ttk.Combobox(
        right_frame,
        values=["Automatic", "Youtube-DL-Video", "Youtube-DL-Audio", "Gallery-DL", "Spot-DL", "Other-Videos"],
        state="readonly",
    )
    tool_selector.set("Automatic")
    tool_selector.pack(fill=tk.X)

    ttk.Label(right_frame, text="Enter URL:").pack(anchor="w", pady=(10, 0))
    url_input_frame = ttk.Frame(right_frame)
    url_input_frame.pack(fill=tk.X)

    url_entry = ttk.Entry(url_input_frame)
    url_entry.pack(fill=tk.X)

    url_box = tk.Text(url_input_frame, height=4, wrap="word")

    ttk.Checkbutton(right_frame, text="Bulk Mode", variable=bulk_mode, command=toggle_bulk_mode).pack(
        anchor="w", pady=(5, 5)
    )

    button_row = ttk.Frame(right_frame)
    button_row.pack(anchor="w", pady=8)

    download_button = ttk.Button(button_row, text="Download", command=run_download)
    download_button.pack(side=tk.LEFT, padx=0)

    open_folder_button = ttk.Button(button_row, text="Open Download Folder", command=lambda: open_folder(download_dir.get()))
    open_folder_button.pack(side=tk.LEFT, padx=5)

    folder_frame = ttk.Frame(right_frame)
    folder_frame.pack(fill=tk.X, pady=(5, 10))

    download_entry = ttk.Entry(folder_frame, textvariable=download_dir)
    download_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

    change_button = ttk.Button(folder_frame, text="Change", command=browse_folder)
    change_button.pack(side=tk.LEFT, padx=5)

    reset_button = ttk.Button(folder_frame, text="Reset", command=reset_folder)
    reset_button.pack(side=tk.LEFT)

    output_box = tk.Text(right_frame, height=10, state=tk.DISABLED)
    output_box.pack(fill=tk.BOTH, expand=True)

    status_parent = ttk.Frame(right_frame)
    status_parent.pack(fill=tk.BOTH, expand=False, pady=(5, 0), ipady=5)

    status_canvas = tk.Canvas(status_parent, height=150)
    status_scrollbar = ttk.Scrollbar(status_parent, orient="vertical", command=status_canvas.yview)
    status_list = ttk.Frame(status_canvas)

    status_list.bind("<Configure>", lambda e: status_canvas.configure(scrollregion=status_canvas.bbox("all")))
    status_canvas.create_window((0, 0), window=status_list, anchor="nw")
    status_canvas.configure(yscrollcommand=status_scrollbar.set)

    status_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    status_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    refresh_tool_statuses_once()
    toggle_bulk_mode()

    return root


if __name__ == "__main__":
    root = build_gui()
    root.after(1200, check_updates_on_startup)
    root.mainloop()