import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import os
import json

CONFIG_PATH = "/opt/feliciadl/config.json"
DEFAULT_PATH = os.path.expanduser("~/Downloads")

def load_config():
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except:
        return {"download_dir": DEFAULT_PATH}

def save_config(config):
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
        "Spot-DL":          ["spotdl", "download", url, "--output", os.path.join(base, "downloaded/spotdl/{track_name}.{output_ext}")],
        "Other-Videos":     ["yt-dlp", "-P", os.path.join(base, "downloaded/other-videos"), url],
    }[tool]

def run_download():
    url = url_entry.get().strip()
    tool = tool_selector.get()
    base = download_dir.get()

    if not url:
        messagebox.showerror("Missing URL", "Please enter a URL.")
        return

    cmd = build_command(tool, url, base)
    output_box.insert(tk.END, f"🚀 Running: {' '.join(cmd)}\n")

    ensure_dirs(base)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        output_box.insert(tk.END, result.stdout)
        output_box.insert(tk.END, result.stderr)
        with open(os.path.join(base, "log", "download.log"), "a") as f:
            f.write(f"{tool}: {url}\n")
    except Exception as e:
        output_box.insert(tk.END, f"❌ Error: {e}\n")

def browse_folder():
    selected = filedialog.askdirectory(initialdir=download_dir.get())
    if selected:
        download_dir.set(selected)
        config["download_dir"] = selected
        save_config(config)

def reset_folder():
    download_dir.set(DEFAULT_PATH)
    config["download_dir"] = DEFAULT_PATH
    save_config(config)

# GUI SETUP
root = tk.Tk()
root.title("FeliciaDL")
root.geometry("640x480")

frame = ttk.Frame(root, padding=10)
frame.pack(fill=tk.BOTH, expand=True)

ttk.Label(frame, text="Select Tool:").pack(anchor="w")
tool_selector = ttk.Combobox(frame, values=["Youtube-DL-Video", "Youtube-DL-Audio", "Gallery-DL", "Spot-DL", "Other-Videos"], state="readonly")
tool_selector.set("Youtube-DL-Video")
tool_selector.pack(fill=tk.X)

ttk.Label(frame, text="Enter URL:").pack(anchor="w", pady=(10, 0))
url_entry = ttk.Entry(frame)
url_entry.pack(fill=tk.X)

# Folder controls
config = load_config()
download_dir = tk.StringVar(value=config["download_dir"])

ttk.Label(frame, text="Download Folder:").pack(anchor="w", pady=(10, 0))
folder_frame = ttk.Frame(frame)
folder_frame.pack(fill=tk.X)
ttk.Entry(folder_frame, textvariable=download_dir).pack(side=tk.LEFT, fill=tk.X, expand=True)
ttk.Button(folder_frame, text="Change", command=browse_folder).pack(side=tk.LEFT)
ttk.Button(folder_frame, text="Reset", command=reset_folder).pack(side=tk.LEFT)

ttk.Button(frame, text="Download", command=run_download).pack(pady=10)

output_box = tk.Text(frame, height=15)
output_box.pack(fill=tk.BOTH, expand=True)

root.mainloop()
