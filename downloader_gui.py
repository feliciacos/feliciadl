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

CONFIG_DIR = os.path.expanduser("~/.config/feliciadl")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
YTDLP_CONFIG_PATH = os.path.join(CONFIG_DIR, "yt-dlp.conf")
DEFAULT_PATH = os.path.expanduser("~/Downloads/FeliciaDL")
AUTOMATIC_MAP_PATH = os.path.join(CONFIG_DIR, "automatic.json")
APP_ICON_PATH = "/opt/feliciadl/assets/icon.png"
APP_LOGO_PATH = "/opt/feliciadl/assets/logo.png"
DEFAULT_THEME = "flatly"

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
        os.path.join(base, "downloaded/other-videos"),
        os.path.join(base, "log")
    ]:
        os.makedirs(folder, exist_ok=True)
    ensure_ytdlp_config()

def build_command(tool, url, base):
    base_video = os.path.join(base, "downloaded/youtube-dl-video")
    base_audio = os.path.join(base, "downloaded/youtube-dl-audio")
    base_spot = os.path.join(base, "downloaded/spotdl")
    base_other = os.path.join(base, "downloaded/other-videos")
    yt_base = ["yt-dlp", "--config-location", YTDLP_CONFIG_PATH]

    resolved_tool = tool

    if tool == "Automatic":
        domain = url.split("/")[2].lower()
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
        "Gallery-DL": ["gallery-dl", "-d", os.path.join(base, "downloaded"), url],
        "Spot-DL": ["spotdl", "download", url, "--output", base_spot],
        "Other-Videos": ["yt-dlp", "--config-location", YTDLP_CONFIG_PATH, "-o", "%(title)s.%(ext)s", "-P", base_other, url],
    }[resolved_tool]

    return cmd, resolved_tool

    
def log_to_console(text):
    output_box.config(state=tk.NORMAL)
    output_box.insert(tk.END, text + "\n")
    output_box.see(tk.END)
    output_box.config(state=tk.DISABLED)

active_threads = []

def run_download():
    input_url = url_entry.get().strip()
    tool = tool_selector.get()
    base = download_dir.get()

    if not input_url:
        messagebox.showerror("Missing URL", "Please enter a URL.")
        return

    url_entry.delete(0, tk.END)
    root.geometry(f"{min(root.winfo_width() + 100, 1300)}x{min(root.winfo_height() + 50, 1000)}")

    row = ttk.Frame(right_frame)
    row.pack(fill=tk.X, pady=2)
    status_label = ttk.Label(row, text=f"⏳ {tool}: {input_url}", anchor="w")
    status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

    bar = ttk.Progressbar(row, mode="indeterminate")
    bar.pack(side=tk.RIGHT, padx=5)
    bar.start()

    stop_button = ttk.Button(row, text="Stop")
    stop_button.pack(side=tk.RIGHT, padx=5)

    def thread_target(url=input_url):
        cmd, resolved_tool = build_command(tool, url, base)
        if cmd is None:
            root.after(0, lambda: [
                bar.stop(),
                stop_button.destroy(),
                row.pack_forget()
            ])
        return
        
        # Update status label to show backend if automatic
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
                    root.after(0, stop_button.destroy)

            stop_button.config(command=stop_process)

            for line in process.stdout:
                if line.strip():
                    root.after(0, lambda l=line.strip(): log_to_console(l))
            for line in process.stderr:
                if line.strip():
                    root.after(0, lambda l=line.strip(): log_to_console(l))

            process.wait()
            root.after(0, bar.stop)
            root.after(0, stop_button.destroy)

            if process.returncode == 0:
                root.after(0, lambda: [
                    status_label.config(text=f"✅ Finished: {tool}"),
                    messagebox.showinfo("Download Complete", f"✅ {tool} finished:\n{url}"),
                    root.after(10000, lambda: row.pack_forget())
                ])
            else:
                root.after(0, lambda: [
                    status_label.config(text=f"❌ Failed: {tool}"),
                    messagebox.showerror("Download Failed", f"❌ {tool} failed:\n{url}"),
                    root.after(10000, lambda: row.pack_forget())
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
                root.after(10000, lambda: row.pack_forget())
            ])

        if threading.current_thread() in active_threads:
            active_threads.remove(threading.current_thread())

    t = threading.Thread(target=thread_target, daemon=True)
    active_threads.append(t)
    t.start()

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

# Load config
config = load_config()
theme = config.get("theme", DEFAULT_THEME)
ensure_ytdlp_config()
automatic_map = load_automatic_mapping()

# GUI SETUP
root = tb.Window(themename=theme)
root.title("FeliciaDL")
root.geometry("1000x600")
root.protocol("WM_DELETE_WINDOW", on_exit)

try:
    root.iconphoto(False, tk.PhotoImage(file=APP_ICON_PATH))
except:
    pass

download_dir = tk.StringVar(value=config["download_dir"])

main_frame = tb.Frame(root, padding=10)
main_frame.pack(fill=tk.BOTH, expand=True)

# Theme selector + Config buttons
theme_frame = ttk.Frame(main_frame)
theme_frame.pack(anchor="w", pady=(0, 10))
ttk.Label(theme_frame, text="Theme:").pack(side=tk.LEFT)
theme_selector = ttk.Combobox(theme_frame, values=tb.Style().theme_names(), state="readonly", width=20)
theme_selector.set(theme)
theme_selector.pack(side=tk.LEFT, padx=5)
theme_selector.bind("<<ComboboxSelected>>", on_theme_change)
ttk.Button(theme_frame, text="Open Config Folder", command=open_config_folder).pack(side=tk.LEFT, padx=10)
ttk.Button(theme_frame, text="Open Logs", command=lambda: open_folder(os.path.join(download_dir.get(), "log"))).pack(side=tk.LEFT)

# Layout
content_frame = ttk.Frame(main_frame)
content_frame.pack(fill=tk.BOTH, expand=True)

left_frame = ttk.Frame(content_frame)
left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

right_frame = ttk.Frame(content_frame)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

# Logo + Links under logo
try:
    logo_img = tk.PhotoImage(file=APP_LOGO_PATH)
    scaled_logo = logo_img.subsample(4, 4)
    tk.Label(left_frame, image=scaled_logo).pack(anchor="n")
except:
    pass

link_frame = ttk.Frame(left_frame)
link_frame.pack(pady=5)
yt_link = ttk.Label(link_frame, text="Supported sites (yt-dlp)", foreground="blue", cursor="hand2")
yt_link.pack(pady=2)
yt_link.bind("<Button-1>", lambda e: open_link("https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md"))
gallery_link = ttk.Label(link_frame, text="Supported sites (gallery-dl)", foreground="blue", cursor="hand2")
gallery_link.pack()
gallery_link.bind("<Button-1>", lambda e: open_link("https://github.com/mikf/gallery-dl/blob/master/docs/supportedsites.md"))

# Controls
ttk.Label(right_frame, text="Select Tool:").pack(anchor="w")
tool_selector = ttk.Combobox(right_frame, values=[
    "Automatic", "Youtube-DL-Video", "Youtube-DL-Audio", "Gallery-DL", "Spot-DL", "Other-Videos"
], state="readonly")
tool_selector.set("Automatic")
tool_selector.pack(fill=tk.X)

ttk.Label(right_frame, text="Enter URL:").pack(anchor="w", pady=(10, 0))
url_entry = ttk.Entry(right_frame)
url_entry.pack(fill=tk.X)

url_btn_frame = ttk.Frame(right_frame)
url_btn_frame.pack(anchor="w", pady=8)
ttk.Button(url_btn_frame, text="Download", command=run_download).pack(side=tk.LEFT, padx=0)
ttk.Button(url_btn_frame, text="Open Download Folder", command=lambda: open_folder(download_dir.get())).pack(side=tk.LEFT, padx=5)

folder_frame = ttk.Frame(right_frame)
folder_frame.pack(fill=tk.X, pady=(5, 10))
ttk.Entry(folder_frame, textvariable=download_dir).pack(side=tk.LEFT, fill=tk.X, expand=True)
ttk.Button(folder_frame, text="Change", command=browse_folder).pack(side=tk.LEFT, padx=5)
ttk.Button(folder_frame, text="Reset", command=reset_folder).pack(side=tk.LEFT)

output_box = tk.Text(right_frame, height=12, state=tk.DISABLED)
output_box.pack(fill=tk.BOTH, expand=True)

root.mainloop()
