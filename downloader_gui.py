import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
from ttkbootstrap import ttk
import subprocess
import os
import json
import webbrowser
import threading
import sys
import time
from tkinter import font
import re

CONFIG_DIR = os.path.expanduser("~/.config/feliciadl")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
YTDLP_CONFIG_PATH = os.path.join(CONFIG_DIR, "yt-dlp.conf")
AUTOMATIC_MAP_PATH = os.path.join(CONFIG_DIR, "automatic.json")
DEFAULT_PATH = os.path.expanduser("~/Downloads/FeliciaDL")
APP_ICON_PATH = "/opt/feliciadl/assets/icon.png"
APP_LOGO_PATH = "/opt/feliciadl/assets/logo.png"
DEFAULT_THEME = "flatly"

# define custom fonts for the status lines
status_font_main = ("TkDefaultFont", 10, "bold")
status_font_version = ("TkDefaultFont", 9, "italic")
status_color_version = "#888888"  # grey tone


def _run(cmd, timeout=20):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return ((p.stdout or "") + (p.stderr or "")).strip()
    except Exception as e:
        return f"__ERR__ {e}"

def _set_label(main_lbl, ver_lbl, title, version, up_to_date=True, note=None):
    color = "green" if up_to_date else "red"
    main_lbl.config(text=f"{title} {'Up-to-date' if up_to_date else 'Out-of-date'}", foreground=color)
    ver_text = f"version {version}" + (f" ({note})" if note else "")
    ver_lbl.config(text=ver_text)

def _norm_ver(s: str) -> str:
    """Normalize a version token like 'stable@2025.10.22.' -> '2025.10.22'"""
    s = s.strip().strip(".").strip(",")
    if "@" in s:
        s = s.split("@", 1)[-1]
    return s

def check_ytdlp():
    """Check YT-DLP version and update status."""
    ver_out = _run(["yt-dlp", "--version"])
    version = (ver_out.splitlines()[0] if ver_out else "unknown").strip()

    upd_out = _run(["yt-dlp", "--update"])
    low = upd_out.lower()

    # common "up to date" phrasings (with/without hyphen)
    if ("up to date" in low) or ("up-to-date" in low) or ("is up to date" in low) or ("is up-to-date" in low):
        root.after(0, lambda: _set_label(yt_status_label, yt_version_label, "YT-DLP", version, True))
        return

    # parse: "Latest version: stable@2025.10.22 ..."
    import re
    m = re.search(r"latest version:\s*([^\s]+)", low)
    if m:
        latest = _norm_ver(m.group(1))
        if latest == version or version.endswith(latest) or latest.endswith(version):
            root.after(0, lambda: _set_label(yt_status_label, yt_version_label, "YT-DLP", version, True))
        else:
            root.after(0, lambda: _set_label(yt_status_label, yt_version_label, "YT-DLP", version, False, note=f"latest {latest}"))
        return

    # fallback: show version without "(status unknown)"
    root.after(0, lambda: _set_label(yt_status_label, yt_version_label, "YT-DLP", version, True))

def check_gallerydl():
    """Check Gallery-DL version and update status."""
    ver_out = _run(["gallery-dl", "--version"])
    version = (ver_out.splitlines()[0] if ver_out else "unknown").strip()

    upd_out = _run(["gallery-dl", "--update"])
    low = upd_out.lower()

    # typical: "[update][info] gallery-dl is up to date (1.30.10)"
    if ("up to date" in low) or ("up-to-date" in low):
        root.after(0, lambda: _set_label(gallery_status_label, gallery_version_label, "Gallery-DL", version, True))
        return

    # sometimes: "new version available: x.y.z" / "update available: x.y.z"
    import re
    m = re.search(r"(new version available|update available)[:\s]+([v]?\d[0-9a-zA-Z\.\-\+]*)", low)
    if m:
        latest = _norm_ver(m.group(2))
        root.after(0, lambda: _set_label(gallery_status_label, gallery_version_label, "Gallery-DL", version, False, note=f"latest {latest}"))
        return

    # fallback: show version without "(status unknown)"
    root.after(0, lambda: _set_label(gallery_status_label, gallery_version_label, "Gallery-DL", version, True))

def check_spotdl():
    ver_out = _run(["spotdl", "--version"])
    first = (ver_out.splitlines()[0] if ver_out else "").strip()
    version = (first.split()[-1].strip(",") if "version" in first.lower() else first) or "unknown"

    upd_out = _run(["spotdl", "--check-for-updates"], timeout=30)
    avail = None
    for ln in upd_out.splitlines():
        if ln.lower().startswith("new version available"):
            # e.g. "New version available: v4.4.3."
            avail = ln.split(":", 1)[-1].strip().strip(".")
            break

    if avail:
        root.after(0, lambda: _set_label(
            spot_status_label, spot_version_label,
            "SpotDL", version, False, note=f"latest {avail}"
        ))
    else:
        root.after(0, lambda: _set_label(
            spot_status_label, spot_version_label,
            "SpotDL", version, True
        ))


def refresh_tool_statuses_once():
    # run in background so UI loads instantly
    threading.Thread(target=lambda: [check_ytdlp(), check_gallerydl(), check_spotdl()], daemon=True).start()

def load_config():
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except:
        return {"download_dir": DEFAULT_PATH, "theme": DEFAULT_THEME}


def save_config(config):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f)


def load_automatic_mapping():
    try:
        with open(AUTOMATIC_MAP_PATH, "r") as f:
            return json.load(f)
    except:
        return {}


def ensure_ytdlp_config():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if not os.path.exists(YTDLP_CONFIG_PATH):
        with open(YTDLP_CONFIG_PATH, "w") as f:
            f.write("# yt-dlp config\n# Example: --cookies cookies.txt\n")


def ensure_dirs(base):
    for folder in [
        base,
        os.path.join(base, "downloaded/youtube-dl-video"),
        os.path.join(base, "downloaded/youtube-dl-audio"),
        os.path.join(base, "downloaded/spotdl"),
        os.path.join(base, "downloaded/gallery-dl"),
        os.path.join(base, "downloaded/other-videos"),
        os.path.join(base, "log")
    ]:
        os.makedirs(folder, exist_ok=True)
    ensure_ytdlp_config()


def build_command(tool, url, base):
    base_video = os.path.join(base, "downloaded/youtube-dl-video")
    base_audio = os.path.join(base, "downloaded/youtube-dl-audio")
    base_spot = os.path.join(base, "downloaded/spotdl")
    base_gallery = os.path.join(base, "downloaded/gallery-dl")
    base_other = os.path.join(base, "downloaded/other-videos")
    yt_base = ["yt-dlp", "--config-location", YTDLP_CONFIG_PATH]

    resolved_tool = tool
    if tool == "Automatic":
        try:
            domain = url.split("/")[2].lower()
        except IndexError:
            return None, None
        matched = False
        for backend, domains in automatic_map.items():
            if any(d in domain for d in domains):
                resolved_tool = {
                    "yt-dlp": "Youtube-DL-Video",
                    "gallery-dl": "Gallery-DL",
                    "spotdl": "Spot-DL"
                }.get(backend, "Other-Videos")
                matched = True
                break
        if not matched:
            messagebox.showerror("Automatic Mode Error",
                "Automatic mode not available for this URL.\nPlease use one of the supported templates.")
            return None, None

    cmd = {
        "Youtube-DL-Video": yt_base + [
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
            "-o", "%(title)s.%(ext)s",
            "-P", base_video,
            url
        ],
        "Youtube-DL-Audio": yt_base + [
            "-x", "--audio-format", "mp3",
            "-o", "%(title)s.%(ext)s",
            "-P", base_audio,
            url
        ],
        "Gallery-DL": ["gallery-dl", "-d", base_gallery, url],
        "Spot-DL": ["spotdl", "download", url, "--output", base_spot],
        "Other-Videos": ["yt-dlp", "--config-location", YTDLP_CONFIG_PATH, "-o", "%(title)s.%(ext)s", "-P", base_other, url],
    }[resolved_tool]

    return cmd, resolved_tool


def log_to_console(text):
    output_box.config(state=tk.NORMAL)
    output_box.insert(tk.END, text + "\n")
    output_box.see(tk.END)
    output_box.config(state=tk.DISABLED)


def scroll_status_to_bottom():
    status_canvas.update_idletasks()
    status_canvas.yview_moveto(1.0)

def update_label_width(label_widget, parent_widget, reserved_right_px=180):
    """Dynamically resize label width based on remaining space."""
    parent_widget.update_idletasks()
    parent_width = parent_widget.winfo_width()
    if parent_width <= 1:
        return
    char_width = 8  # More realistic for ttk.Label
    usable_width = max(100, parent_width - reserved_right_px)
    width_chars = usable_width // char_width
    label_widget.config(width=width_chars)


active_threads = []


def run_single_download(input_url, tool, sync=False, on_finish=None):
    base = download_dir.get()
    outer_row = ttk.Frame(status_list)
    outer_row.pack(fill=tk.X, pady=2)
    root.after(100, scroll_status_to_bottom)

    # Grid layout with fixed width label and fixed right-aligned bar+button
    outer_row.grid_columnconfigure(0, weight=1)
    outer_row.grid_columnconfigure(1, weight=0)
    outer_row.grid_columnconfigure(2, weight=0)

    status_label = ttk.Label(
        outer_row,
        text=f"⏳ {tool}: {input_url}",
        anchor="w",
        justify="left",
        width=67
    )
    resize_callbacks.append(lambda: update_label_width(status_label, outer_row))
    stop_button = ttk.Button(outer_row, text="Stop")
    bar = ttk.Progressbar(outer_row, mode="indeterminate", maximum=100)

    status_label.grid(row=0, column=0, sticky="w", padx=(0, 10))
    stop_button.grid(row=0, column=1, sticky="e", padx=(5, 2))
    bar.grid(row=0, column=2, sticky="e", padx=(2, 5))

    bar.start()

    def thread_target(url=input_url):
        cmd, resolved_tool = build_command(tool, url, base)
        if cmd is None:
            root.after(0, lambda: [
                bar.stop(),
                stop_button.destroy(),
                outer_row.pack_forget(),
                root.after(100, scroll_status_to_bottom)
            ])
            if on_finish:
                root.after(0, on_finish)
            return

        label_text = f"⏳ {tool} ({resolved_tool}): {url}" if tool == "Automatic" else f"⏳ {tool}: {url}"
        root.after(0, lambda: status_label.config(text=label_text))
        ensure_dirs(base)
        log_path = os.path.join(base, "log", "download.log")

        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)

            def stop_process():
                if process.poll() is None and messagebox.askyesno("Stop Download", f"Force stop this job?\n\n{tool}\n{url}"):
                    process.kill()
                    log_to_console(f"⛔ Stopped: {tool} → {url}")
                    root.after(0, lambda: status_label.config(text=f"⛔ Stopped: {tool}"))
                    bar.stop()
                    def preserve_button_space():
                        placeholder = ttk.Label(outer_row, text="", width=6)
                        placeholder.grid(row=0, column=1, sticky="e", padx=(5, 2))
                    root.after(0, lambda: [stop_button.destroy(), preserve_button_space()])

            stop_button.config(command=stop_process)

            for line in process.stdout:
                if line.strip():
                    root.after(0, lambda l=line.strip(): log_to_console(l))
            for line in process.stderr:
                if line.strip():
                    root.after(0, lambda l=line.strip(): log_to_console(l))

            process.wait()
            root.after(0, bar.stop)

            def preserve_button_space():
                placeholder = ttk.Label(outer_row, text="", width=6)
                placeholder.grid(row=0, column=1, sticky="e", padx=(5, 2))

            root.after(0, lambda: [stop_button.destroy(), preserve_button_space()])

            final_status = "✅ Finished" if process.returncode == 0 else "❌ Failed"
            log_func = messagebox.showinfo if process.returncode == 0 else messagebox.showerror
            bar_mode = "determinate"
            bar_value = 100 if process.returncode == 0 else 0

            root.after(0, lambda: [
                bar.stop(),
                bar.config(mode=bar_mode, value=bar_value),
                status_label.config(text=f"{final_status}: {tool} ({resolved_tool}): {url}"),
                log_func("Download", f"{final_status}: {tool}\n{url}"),
                scroll_status_to_bottom()
            ])

            with open(log_path, "a") as f:
                f.write(f"{tool} ({resolved_tool}): {url}\n")

        except Exception as e:
            root.after(0, bar.stop)
            root.after(0, stop_button.destroy)
            err = f"❌ Exception: {e}\n{url}"
            root.after(0, lambda: [
                status_label.config(text="❌ Exception"),
                messagebox.showerror("Download Error", err),
                log_to_console(err),
            ])

        if threading.current_thread() in active_threads:
            active_threads.remove(threading.current_thread())
        if on_finish:
            on_finish()
        if not any(t.is_alive() for t in active_threads):
            root.after(0, unlock_controls)
        
    if sync:
        thread_target()
    else:
        t = threading.Thread(target=thread_target, daemon=True)
        active_threads.append(t)
        t.start()

def run_download():
    lock_controls()
    tool = tool_selector.get()
    text = url_box.get("1.0", tk.END).strip() if bulk_mode.get() else url_entry.get().strip()
    urls = [u.strip() for u in text.splitlines() if u.strip()]
    if not urls:
        messagebox.showerror("Missing URL", "Please enter at least one URL.")
        return

    if bulk_mode.get():
        url_box.delete("1.0", tk.END)
    else:
        url_entry.delete(0, tk.END)

    base = download_dir.get()
    ensure_dirs(base)
    log_path = os.path.join(base, "log", "download.log")

    if bulk_mode.get():
        row = ttk.Frame(status_list)
        row.pack(fill=tk.X, pady=2)
        root.after(100, scroll_status_to_bottom)

        # Create widgets using grid
        label = ttk.Label(
            row,
            text="",
            anchor="w",
            justify="left",
            width=67  # Same clipping effect for long lines in bulk
        )
        
        resize_callbacks.append(lambda: update_label_width(label, row))
        stop_button = ttk.Button(row, text="Stop")
        bar = ttk.Progressbar(row, mode="indeterminate", maximum=100)

        label.grid(row=0, column=0, sticky="w", padx=(0, 10))
        stop_button.grid(row=0, column=1, sticky="e", padx=(5, 2))
        bar.grid(row=0, column=2, sticky="e", padx=(2, 5))

        row.grid_columnconfigure(0, weight=1)


        bar.start()
        current_process = None
        cancelled = False

        def stop_bulk():
            nonlocal cancelled
            cancelled = True
            if current_process and current_process.poll() is None:
                current_process.kill()
            root.after(0, lambda: label.config(text="⛔ Stopped (Bulk Job)"))

        stop_button.config(command=stop_bulk)

        def bulk_worker():
            nonlocal current_process, cancelled
            total = len(urls)
            completed = tk.IntVar(value=0)

            def update_progress():
                percent = int((completed.get() / total) * 100)
                bar.config(mode="determinate", value=percent)

            for i, url in enumerate(urls, start=1):
                if cancelled:
                    break

                cmd, resolved_tool = build_command(tool, url, base)
                if cmd is None:
                    continue


                label_text = f"⏳ [{i}/{total}] {tool} ({resolved_tool}): {url}" if tool == "Automatic" else f"⏳ [{i}/{total}] {tool}: {url}"
                root.after(0, lambda text=label_text: label.config(text=text))

                try:
                    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
                    current_process = process

                    for line in process.stdout:
                        if line.strip():
                            root.after(0, lambda l=line.strip(): log_to_console(l))
                    for line in process.stderr:
                        if line.strip():
                            root.after(0, lambda l=line.strip(): log_to_console(l))

                    process.wait()

                    with open(log_path, "a") as f:
                        f.write(f"{tool} ({resolved_tool}): {url}\n")

                    if process.returncode != 0:
                        root.after(0, lambda: messagebox.showerror("Download Failed", f"❌ {tool} failed:\n{url}"))

                except Exception as e:
                    err = f"❌ Exception: {e}\n{url}"
                    root.after(0, lambda: [
                        label.config(text="❌ Exception"),
                        messagebox.showerror("Download Error", err),
                        log_to_console(err)
                    ])

                completed.set(completed.get() + 1)
                root.after(0, update_progress)
                time.sleep(5)

            def on_complete():
                bar.stop()
                bar.config(mode="determinate", value=100)
                stop_button.grid_forget()
                if cancelled:
                    label.config(text=f"⛔ Bulk job cancelled at {completed.get()}/{total}.")
                else:
                    label.config(text=f"✅ All {total} downloads completed.")
                scroll_status_to_bottom()
                if threading.current_thread() in active_threads:
                    active_threads.remove(threading.current_thread())
                if not any(t.is_alive() for t in active_threads):
                    unlock_controls()
                # if if if if if if if else else else else else  deze zijn speciaal voor Thomas <3

            root.after(0, on_complete)

        bulk_thread = threading.Thread(target=bulk_worker, daemon=True)
        active_threads.append(bulk_thread)
        bulk_thread.start()
        
    else:
        def check_unlock():
            if not any(t.is_alive() for t in active_threads):
                unlock_controls()

        run_single_download(urls[0], tool, on_finish=check_unlock)


def toggle_bulk_mode():
    for widget in url_input_frame.winfo_children():
        widget.pack_forget()

    if bulk_mode.get():
        url_box.pack(fill=tk.X)
        current_width = root.winfo_width()
        current_height = root.winfo_height()
        root.geometry(f"{current_width}x{current_height + 50}")
    else:
        url_entry.pack(fill=tk.X)
        current_width = root.winfo_width()
        current_height = root.winfo_height()
        root.geometry(f"{current_width}x{max(current_height - 50, 400)}")


def on_exit():
    if any(t.is_alive() for t in active_threads):
        if not messagebox.askyesno("Quit", "⚠️ Downloads are still running. Are you sure you want to exit?"):
            return
    root.destroy()

def browse_folder():
    try:
        result = subprocess.run(["zenity", "--file-selection", "--directory", "--title=Select Download Folder"],
                                capture_output=True, text=True)
        selected = result.stdout.strip()
        if selected:
            full_path = os.path.join(selected, "FeliciaDL")
            os.makedirs(full_path, exist_ok=True)
            download_dir.set(full_path)
            config["download_dir"] = full_path
            save_config(config)
    except FileNotFoundError:
        selected = filedialog.askdirectory(parent=root, title="Select Download Folder")
        if selected:
            full_path = os.path.join(selected, "FeliciaDL")
            os.makedirs(full_path, exist_ok=True)
            download_dir.set(full_path)
            config["download_dir"] = full_path
            save_config(config)

def open_config_folder():
    subprocess.run(["xdg-open", CONFIG_DIR])

def reset_folder():
    download_dir.set(DEFAULT_PATH)
    config["download_dir"] = DEFAULT_PATH
    save_config(config)

def open_folder(path):
    subprocess.run(["xdg-open", path])

def open_link(url):
    webbrowser.open_new_tab(url)

def on_theme_change(event):
    config["theme"] = theme_selector.get()
    save_config(config)
    root.destroy()
    os.execl(sys.executable, sys.executable, *sys.argv)

def lock_controls():
    theme_selector.config(state="disabled")
    download_entry.config(state="disabled")
    change_button.config(state="disabled")
    reset_button.config(state="disabled")

def unlock_controls():
    theme_selector.config(state="readonly")
    download_entry.config(state="normal")
    change_button.config(state="normal")
    reset_button.config(state="normal")

# --- INIT ---
config = load_config()
theme = config.get("theme", DEFAULT_THEME)
automatic_map = load_automatic_mapping()
ensure_ytdlp_config()

# GUI
root = tb.Window(themename=theme)
root.title("FeliciaDL")
root.geometry("1000x600")
root.protocol("WM_DELETE_WINDOW", on_exit)
resize_callbacks = []
resize_after_id = None

def debounced_resize_handler(event):
    global resize_after_id
    if resize_after_id:
        root.after_cancel(resize_after_id)
    resize_after_id = root.after(150, lambda: [cb() for cb in resize_callbacks])

root.bind("<Configure>", debounced_resize_handler)

try:
    root.iconphoto(False, tk.PhotoImage(file=APP_ICON_PATH))
except: pass

download_dir = tk.StringVar(value=config["download_dir"])
bulk_mode = tk.BooleanVar(value=False)

main_frame = tb.Frame(root, padding=10)
main_frame.pack(fill=tk.BOTH, expand=True)

theme_frame = ttk.Frame(main_frame)
theme_frame.pack(anchor="w", pady=(0, 10))
ttk.Label(theme_frame, text="Theme:").pack(side=tk.LEFT)
theme_selector = ttk.Combobox(theme_frame, values=tb.Style().theme_names(), state="readonly", width=20)
theme_selector.set(theme)
theme_selector.pack(side=tk.LEFT, padx=5)
theme_selector.bind("<<ComboboxSelected>>", on_theme_change)

ttk.Button(theme_frame, text="Open Config Folder", command=open_config_folder).pack(side=tk.LEFT, padx=10)
ttk.Button(theme_frame, text="Open Logs", command=lambda: open_folder(os.path.join(download_dir.get(), "log"))).pack(side=tk.LEFT)

content_frame = ttk.Frame(main_frame)
content_frame.pack(fill=tk.BOTH, expand=True)

left_frame = ttk.Frame(content_frame)
left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

right_frame = ttk.Frame(content_frame)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

# Logo + Links
try:
    logo_img = tk.PhotoImage(file=APP_LOGO_PATH)
    scaled_logo = logo_img.subsample(4, 4)
    tk.Label(left_frame, image=scaled_logo).pack(anchor="n")
except:
    pass

# NEW: separator above the two links
links_top_sep = ttk.Separator(left_frame)
links_top_sep.pack(fill=tk.X, pady=(6, 6))

# Links (styled like the grey "version" text, non-italic, left-aligned)
link_font = ("TkDefaultFont", 9)  # non-italic to match your version line
link_color = status_color_version  # "#888888"

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

# Version / update status labels
status_links_sep = ttk.Separator(left_frame)
status_links_sep.pack(fill=tk.X, pady=(8, 6))

def make_status_pair(parent, title):
    frame = ttk.Frame(parent)
    frame.pack(anchor="w", pady=(0, 4), fill=tk.X)
    main_label = ttk.Label(frame, text=f"{title} Checking...", font=status_font_main, anchor="w")
    main_label.pack(anchor="w")
    version_label = ttk.Label(frame, text="version …", font=status_font_version, foreground=status_color_version, anchor="w")
    version_label.pack(anchor="w")
    return main_label, version_label

yt_status_label, yt_version_label = make_status_pair(left_frame, "YT-DLP")
gallery_status_label, gallery_version_label = make_status_pair(left_frame, "Gallery-DL")
spot_status_label, spot_version_label = make_status_pair(left_frame, "SpotDL")


# Controls
ttk.Label(right_frame, text="Select Tool:").pack(anchor="w")
tool_selector = ttk.Combobox(right_frame, values=[
    "Automatic", "Youtube-DL-Video", "Youtube-DL-Audio", "Gallery-DL", "Spot-DL", "Other-Videos"
], state="readonly")
tool_selector.set("Automatic")
tool_selector.pack(fill=tk.X)

ttk.Label(right_frame, text="Enter URL:").pack(anchor="w", pady=(10, 0))
url_input_frame = ttk.Frame(right_frame)
url_input_frame.pack(fill=tk.X)

url_entry = ttk.Entry(url_input_frame)
url_box = tk.Text(url_input_frame, height=4, wrap="word")
url_entry.pack(fill=tk.X)  # start with single-line entry visible

ttk.Checkbutton(right_frame, text="Bulk Mode", variable=bulk_mode, command=toggle_bulk_mode).pack(anchor="w", pady=(5, 5))

url_btn_frame = ttk.Frame(right_frame)
url_btn_frame.pack(anchor="w", pady=8)
ttk.Button(url_btn_frame, text="Download", command=run_download).pack(side=tk.LEFT, padx=0)
ttk.Button(url_btn_frame, text="Open Download Folder", command=lambda: open_folder(download_dir.get())).pack(side=tk.LEFT, padx=5)
folder_frame = ttk.Frame(right_frame)
folder_frame.pack(fill=tk.X, pady=(5, 10))

download_entry = ttk.Entry(folder_frame, textvariable=download_dir)
download_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

change_button = ttk.Button(folder_frame, text="Change", command=browse_folder)
change_button.pack(side=tk.LEFT, padx=5)

reset_button = ttk.Button(folder_frame, text="Reset", command=reset_folder)
reset_button.pack(side=tk.LEFT)


# Console output
output_box = tk.Text(right_frame, height=10, state=tk.DISABLED)
output_box.pack(fill=tk.BOTH, expand=True)

# Scrollable status frame under output_box (50% height of log)
status_frame = ttk.Frame(right_frame)
status_frame.pack(fill=tk.BOTH, expand=False, pady=(5, 0), ipady=5)

status_canvas = tk.Canvas(status_frame, height=150)
status_scrollbar = ttk.Scrollbar(status_frame, orient="vertical", command=status_canvas.yview)
status_list = ttk.Frame(status_canvas)

status_list.bind("<Configure>", lambda e: status_canvas.configure(scrollregion=status_canvas.bbox("all")))
status_canvas.create_window((0, 0), window=status_list, anchor="nw")
status_canvas.configure(yscrollcommand=status_scrollbar.set)

status_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
status_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# initial status fetch (non-blocking)
refresh_tool_statuses_once()

root.mainloop()
