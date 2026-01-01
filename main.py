import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import sys
from pydub import AudioSegment
from pydub.utils import which
import threading
import subprocess
import shutil
import re

class AudioConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Converter")
        self.root.geometry("550x400")
        self.root.resizable(False, False)

        # Style
        style = ttk.Style()
        style.theme_use('clam')

        # Variables
        self.input_file_path = tk.StringVar()
        self.output_format = tk.StringVar(value="mp3")
        self.status_var = tk.StringVar(value="Ready")
        self.progress_var = tk.DoubleVar(value=0)

        # UI Components
        self.create_widgets()
        
    def create_widgets(self):
        # Main Frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="Audio Converter Pro", font=("Helvetica", 16, "bold"))
        title_label.pack(pady=(0, 20))

        # Input File Section
        input_frame = ttk.LabelFrame(main_frame, text="Input File", padding="10")
        input_frame.pack(fill=tk.X, pady=(0, 10))

        self.file_entry = ttk.Entry(input_frame, textvariable=self.input_file_path, state="readonly")
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        browse_btn = ttk.Button(input_frame, text="Browse", command=self.browse_file)
        browse_btn.pack(side=tk.RIGHT)

        # Options Section
        options_frame = ttk.LabelFrame(main_frame, text="Conversion Options", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 20))

        format_label = ttk.Label(options_frame, text="Output Format:")
        format_label.pack(side=tk.LEFT, padx=(0, 10))

        formats = ["mp3", "wav", "ogg", "flac", "m4a", "aac", "wma"]
        format_menu = ttk.OptionMenu(options_frame, self.output_format, formats[0], *formats)
        format_menu.pack(side=tk.LEFT)

        # Progress Section
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))

        # Convert Button
        self.convert_btn = ttk.Button(main_frame, text="Convert Now", command=self.start_conversion)
        self.convert_btn.pack(fill=tk.X, value=tk.BOTTOM,  pady=(0, 5))

        # Status Bar
        status_label = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_label.pack(fill=tk.X, side=tk.BOTTOM)

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Audio Files", "*.mp3 *.wav *.ogg *.flac *.m4a *.aac *.wma"), ("All Files", "*.*")]
        )
        if file_path:
            self.input_file_path.set(file_path)
            self.status_var.set("File selected: " + os.path.basename(file_path))
            self.progress_var.set(0)

    def start_conversion(self):
        input_path = self.input_file_path.get()
        if not input_path:
            messagebox.showerror("Error", "Please select an input file first.")
            return
        
        # Verify ffmpeg exists nearby or in path
        ffmpeg_exe = "ffmpeg.exe" if os.path.exists("ffmpeg.exe") else "ffmpeg"
        if shutil.which(ffmpeg_exe) is None and not os.path.exists(ffmpeg_exe):
             messagebox.showerror("Error", "ffmpeg.exe not found! Please place it in the app folder.")
             return

        target_format = self.output_format.get()
        
        # Ask for save location
        initial_file_name = os.path.splitext(os.path.basename(input_path))[0] + "." + target_format
        save_path = filedialog.asksaveasfilename(
            defaultextension=f".{target_format}",
            filetypes=[(f"{target_format.upper()} Audio", f"*.{target_format}")],
            initialfile=initial_file_name
        )

        if not save_path:
            return

        self.convert_btn.config(state="disabled")
        self.status_var.set("Preparing conversion...")
        self.progress_var.set(0)
        
        # Run in thread
        threading.Thread(target=self.convert_process, args=(input_path, save_path), daemon=True).start()

    def get_duration(self, input_path):
        # Use ffprobe to get duration in seconds
        ffprobe_cmd = [
            "ffprobe.exe" if os.path.exists("ffprobe.exe") else "ffprobe", 
            "-v", "error", 
            "-show_entries", "format=duration", 
            "-of", "default=noprint_wrappers=1:nokey=1", 
            input_path
        ]
        
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            result = subprocess.run(
                ffprobe_cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                startupinfo=startupinfo
            )
            return float(result.stdout.strip())
        except Exception as e:
            print(f"Error getting duration: {e}")
            return None

    def convert_process(self, input_path, save_path):
        try:
            duration = self.get_duration(input_path)
            if not duration:
                # Fallback if duration fails: just convert without progress
                self.progress_var.set(0)
                duration = 1 # avoid zero div
            
            ffmpeg_cmd = [
                "ffmpeg.exe" if os.path.exists("ffmpeg.exe") else "ffmpeg",
                "-i", input_path,
                "-y", # overwrite
                save_path
            ]

            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                startupinfo=startupinfo,
                bufsize=1,            # Line buffered
                universal_newlines=True
            )
            
            # Read stderr for progress (ffmpeg writes stats to stderr)
            pattern = re.compile(r"time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})")
            
            while True:
                line = process.stderr.readline()
                if not line and process.poll() is not None:
                    break
                
                if line:
                    match = pattern.search(line)
                    if match:
                        h, m, s, ms = map(int, match.groups())
                        current_seconds = h * 3600 + m * 60 + s + (ms / 100.0)
                        progress = (current_seconds / duration) * 100
                        self.root.after(0, lambda p=progress: self.update_progress(p))

            if process.returncode == 0:
                self.root.after(0, lambda: self.conversion_complete(True, save_path))
            else:
                self.root.after(0, lambda: self.conversion_complete(False, "FFmpeg exited with error."))

        except Exception as e:
            self.root.after(0, lambda: self.conversion_complete(False, str(e)))

    def update_progress(self, val):
        self.progress_var.set(val)
        self.status_var.set(f"Converting... {val:.1f}%")

    def conversion_complete(self, success, message):
        self.convert_btn.config(state="normal")
        if success:
            self.progress_var.set(100)
            self.status_var.set("Conversion Successful!")
            messagebox.showinfo("Success", f"File saved to:\n{message}")
        else:
            self.status_var.set("Error during conversion.")
            # messagebox.showerror("Conversion Failed", f"An error occurred:\n{message}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioConverterApp(root)
    root.mainloop()
