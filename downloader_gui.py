import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
from ttkbootstrap import ttk
import subprocess
import os
import json
import webbrowser
import sys

CONFIG_PATH = os.path.expanduser("~/.config/feliciadl/config.json")
DEFAULT_PATH = os.path.expanduser("~/Downloads/FeliciaDL")
APP_ICON_PATH = "/opt/feliciadl/assets/icon.png"
APP_LOGO_PATH = "/opt/feliciadl/assets/logo.png"
DEFAULT_THEME = "darkly"

# Load or create config
def load_config():
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except:
        return {
            "download_dir": DEFAULT_PATH,
            "theme": DEFAULT_THEME
        }

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
        os.path.join(base, "downloaded/other-videos"),
        os.path.join(base, "log")
    ]
    for path in folders:
        os.makedirs(path, exist_ok=True)

def build_command(tool, url, base):
    return {
        "Youtube-DL-Video": ["yt-dlp", "-P", os.path.join(base, "downloaded/youtube-dl-video"), url],
        "Youtube-DL-Audio": ["yt-dlp", "-x", "--audio-format", "mp3", "-P", os.path.join(base, "downloaded/youtube-dl-audio"), url],
        "Gallery-DL":       ["gallery-dl", "-d", os.path.join(base, "downloaded"), url],
        "Spot-DL": [
    "spotdl", "download", url,
    "--output", os.path.join(base, "downloaded/spotdl")
],

        "Other-Videos":     ["yt-dlp", url]
    }[tool]

def run_download():
    url = url_entry.get().strip()
    tool = tool_selector.get()
    base = download_dir.get()

    if not url:
        messagebox.showerror("Missing URL", "Please enter a URL.")
        return

    cmd = build_command(tool, url, base)
    output_box.config(state=tk.NORMAL)
    output_box.insert(tk.END, f"\n🚀 Running: {' '.join(cmd)}\n")
    output_box.see(tk.END)
    output_box.config(state=tk.DISABLED)

    ensure_dirs(base)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        output_box.config(state=tk.NORMAL)
        output_box.insert(tk.END, result.stdout)
        output_box.see(tk.END)
        output_box.insert(tk.END, result.stderr)
        output_box.see(tk.END)
        output_box.config(state=tk.DISABLED)
        with open(os.path.join(base, "log", "download.log"), "a") as f:
            f.write(f"{tool}: {url}\n")
    except Exception as e:
        output_box.config(state=tk.NORMAL)
        output_box.insert(tk.END, f"❌ Error: {e}\n")
        output_box.see(tk.END)
        output_box.config(state=tk.DISABLED)

    url_entry.delete(0, tk.END)

def browse_folder():
    try:
        result = subprocess.run(
            ["zenity", "--file-selection", "--directory", "--title=Select Download Folder"],
            capture_output=True, text=True
        )
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

def reset_folder():
    download_dir.set(DEFAULT_PATH)
    config["download_dir"] = DEFAULT_PATH
    save_config(config)

def open_folder(path):
    subprocess.run(["xdg-open", path])

def open_link(url):
    webbrowser.open_new_tab(url)

def on_theme_change(event=None):
    selected = theme_selector.get()
    config["theme"] = selected
    save_config(config)
    root.destroy()
    os.execl(sys.executable, sys.executable, *sys.argv)

# Load config early to get theme
config = load_config()
theme = config.get("theme", DEFAULT_THEME)

# GUI SETUP
root = tb.Window(themename=theme)
root.title("FeliciaDL")
root.geometry("800x600")

try:
    root.iconphoto(False, tk.PhotoImage(file=APP_ICON_PATH))
except:
    pass

download_dir = tk.StringVar(value=config["download_dir"])

main_frame = tb.Frame(root, padding=10)
main_frame.pack(fill=tk.BOTH, expand=True)

# Theme selector
top_bar = tb.Frame(main_frame)
top_bar.pack(fill=tk.X, pady=(0, 10))
tb.Label(top_bar, text="Theme:").pack(side=tk.LEFT, padx=(0, 5))
theme_selector = tb.Combobox(top_bar, values=tb.Style().theme_names(), state="readonly", width=20)
theme_selector.set(theme)
theme_selector.pack(side=tk.LEFT)
theme_selector.bind("<<ComboboxSelected>>", on_theme_change)

# Layout split: logo (left), controls (right)
content_frame = tb.Frame(main_frame)
content_frame.pack(fill=tk.BOTH, expand=True)

left_frame = tb.Frame(content_frame)
left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

right_frame = tb.Frame(content_frame)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

# Logo image
try:
    logo_img = tk.PhotoImage(file=APP_LOGO_PATH)
    scaled_logo = logo_img.subsample(4, 4)
    logo_label = tk.Label(left_frame, image=scaled_logo)
    logo_label.pack(anchor="n")
except:
    pass

# Tool selector
ttk.Label(right_frame, text="Select Tool:").pack(anchor="w")
tool_selector = ttk.Combobox(right_frame, values=[
    "Youtube-DL-Video",
    "Youtube-DL-Audio",
    "Gallery-DL",
    "Spot-DL",
    "Other-Videos"
], state="readonly")
tool_selector.set("Youtube-DL-Video")
tool_selector.pack(fill=tk.X)

# URL input
ttk.Label(right_frame, text="Enter URL:").pack(anchor="w", pady=(10, 0))
url_entry = ttk.Entry(right_frame)
url_entry.pack(fill=tk.X)

# Download folder
folder_frame = ttk.Frame(right_frame)
folder_frame.pack(fill=tk.X, pady=(10, 0))
ttk.Entry(folder_frame, textvariable=download_dir).pack(side=tk.LEFT, fill=tk.X, expand=True)
ttk.Button(folder_frame, text="Change", command=browse_folder).pack(side=tk.LEFT, padx=5)
ttk.Button(folder_frame, text="Reset", command=reset_folder).pack(side=tk.LEFT)

# Action buttons
button_frame = ttk.Frame(right_frame)
button_frame.pack(pady=10)
ttk.Button(button_frame, text="Download", command=run_download).pack(side=tk.LEFT, padx=5)
ttk.Button(button_frame, text="Open Download Folder", command=lambda: open_folder(download_dir.get())).pack(side=tk.LEFT, padx=5)
ttk.Button(button_frame, text="Open Logs", command=lambda: open_folder(os.path.join(download_dir.get(), "log"))).pack(side=tk.LEFT, padx=5)

# Output box
output_box = tk.Text(right_frame, height=12, state=tk.DISABLED)
output_box.pack(fill=tk.BOTH, expand=True)

# Info links
link_frame = ttk.Frame(right_frame)
link_frame.pack(pady=5)
yt_link = ttk.Label(link_frame, text="Supported sites (yt-dlp)", foreground="blue", cursor="hand2")
yt_link.pack(side=tk.LEFT, padx=10)
yt_link.bind("<Button-1>", lambda e: open_link("https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md"))

gallery_link = ttk.Label(link_frame, text="Supported sites (gallery-dl)", foreground="blue", cursor="hand2")
gallery_link.pack(side=tk.LEFT)
gallery_link.bind("<Button-1>", lambda e: open_link("https://github.com/mikf/gallery-dl/blob/master/docs/supportedsites.md"))

root.mainloop()
