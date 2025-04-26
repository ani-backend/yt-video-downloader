import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog # <-- Import filedialog
import os
import threading
import json # <-- Import json for saving/loading config
from commons import (
    get_available_streams,
    download_selected_stream,
)

# --- Configuration Handling ---
CONFIG_FILE = "config.json"
DEFAULT_DOWNLOAD_FOLDER = "youtube_downloads"

def load_config():
    """Loads configuration from file."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Error reading {CONFIG_FILE}. Using defaults.")
            return {} # Return empty dict on error
    return {}

def save_config(config_data):
    """Saves configuration to file."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config_data, f, indent=4)

# --- Existing Functions (Ensure they use the dynamic download path) ---


class DownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Video Downloader")
        self.root.geometry("800x600") # Example size

        self.streams_data = None
        self.video_title = ""
        self.selected_stream = None
        # self.download_path = None # We'll use self.current_download_folder now

        # --- Load Configuration ---
        self.config = load_config()
        loaded_folder = self.config.get("download_folder", DEFAULT_DOWNLOAD_FOLDER)

        # --- Check if loaded path is empty ---
        if not loaded_folder: # If the loaded path is empty or None
            messagebox.showwarning("Configuration", "No download folder configured. Please select one.")
            # Initialize to empty, select_download_folder will handle setting it
            self.current_download_folder = ""
            # We need the UI elements (like the button) to exist before calling select_download_folder
            # So, we'll schedule the call after the main window is initialized
            self.root.after(100, self.select_download_folder)
        else:
            self.current_download_folder = loaded_folder
            # Ensure folder exists only if the path is not empty
            if not os.path.exists(self.current_download_folder):
                try:
                    os.makedirs(self.current_download_folder)
                except OSError as e:
                    messagebox.showerror("Error", f"Could not create download folder '{self.current_download_folder}': {e}\nPlease select a different folder.")
                    # Force selection if creation fails
                    self.current_download_folder = ""
                    self.root.after(100, self.select_download_folder)


        # --- UI Elements ---
        # URL Input
        ttk.Label(root, text="Enter YouTube URL:").pack(pady=5)
        self.url_entry = ttk.Entry(root, width=60)
        self.url_entry.pack(pady=5)

        # Show Formats Button
        self.show_formats_button = ttk.Button(root, text="Show Available Formats", command=self.fetch_formats_thread)
        self.show_formats_button.pack(pady=10)
        self.format_frame = ttk.Frame(root)

        # --- Download Folder Selection ---
        folder_frame = ttk.Frame(root)
        folder_frame.pack(fill=tk.X, padx=10, pady=5)

        self.select_folder_button = ttk.Button(folder_frame, text="Select Download Folder", command=self.select_download_folder)
        self.select_folder_button.pack(side=tk.LEFT)

        # Use a StringVar for the label to update it easily
        self.download_folder_var = tk.StringVar()
        # Set initial text based on potentially empty path
        self.download_folder_var.set(f"Current Folder: {self.current_download_folder if self.current_download_folder else 'Not Set'}")
        self.folder_label = ttk.Label(folder_frame, textvariable=self.download_folder_var, wraplength=400) # Wraplength for long paths
        self.folder_label.pack(side=tk.LEFT, padx=10)
        # --- End Download Folder Selection ---

        # Status Label
        self.status_label = ttk.Label(root, text="")
        self.status_label.pack(pady=10)

    def select_download_folder(self):
        """Opens a dialog to select the download folder."""
        # Determine a sensible starting directory
        initial_dir = self.current_download_folder if self.current_download_folder and os.path.exists(self.current_download_folder) else os.path.expanduser("~")

        selected_path = filedialog.askdirectory(
            initialdir=initial_dir,
            title="Select Download Folder"
        )
        if selected_path: # Only update if a path was actually selected
            self.current_download_folder = selected_path
            self.download_folder_var.set(f"Current Folder: {self.current_download_folder}")
            # Save the selected path to config
            self.config["download_folder"] = self.current_download_folder
            save_config(self.config)
            self.update_status(f"Download folder set to: {self.current_download_folder}")
        elif not self.current_download_folder: # If selection was cancelled AND no folder was previously set
             self.update_status("Folder selection cancelled. Please select a folder to enable downloads.", True)
             self.download_folder_var.set("Current Folder: Not Set")
        else:
             # Keep the existing folder if selection is cancelled but one was already set
             self.update_status("Folder selection cancelled.")


    def update_status(self, text, is_error=False):
        self.status_label.config(text=text, foreground="red" if is_error else "black")

    def fetch_formats_thread(self):
        url = self.url_entry.get()
        if not url:
            messagebox.showwarning("Input Error", "Please enter a YouTube URL first")
            return

        self.update_status("Fetching formats...")
        self.show_formats_button.config(state=tk.DISABLED) # Disable button during fetch

        # Run network task in a separate thread
        thread = threading.Thread(target=self.fetch_formats_task, args=(url,))
        thread.start()

    def fetch_formats_task(self, url):
        try:
            streams, title = get_available_streams(url)
            self.streams_data = streams
            self.video_title = title
            # Schedule UI update back on the main thread
            self.root.after(0, self.display_formats)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to fetch formats: {str(e)}"))
            self.root.after(0, lambda: self.update_status(f"Error fetching: {str(e)}", True))
        finally:
            # Re-enable button on the main thread
             self.root.after(0, lambda: self.show_formats_button.config(state=tk.NORMAL))


    def display_formats(self):
        self.update_status("Formats loaded. Select type and quality.")
        # Clear previous format widgets if any
        for widget in self.format_frame.winfo_children():
            widget.destroy()

        # Radio buttons for format type
        self.format_type_var = tk.StringVar(value='progressive') # Default selection
        ttk.Radiobutton(self.format_frame, text="Progressive (Video+Audio)", variable=self.format_type_var, value='progressive', command=self.update_quality_options).pack(anchor=tk.W)
        ttk.Radiobutton(self.format_frame, text="Video Only", variable=self.format_type_var, value='video', command=self.update_quality_options).pack(anchor=tk.W)
        ttk.Radiobutton(self.format_frame, text="Audio Only", variable=self.format_type_var, value='audio', command=self.update_quality_options).pack(anchor=tk.W)

        # Combobox for quality selection
        ttk.Label(self.format_frame, text="Select quality:").pack(anchor=tk.W, pady=(10,0))
        self.quality_combobox = ttk.Combobox(self.format_frame, width=50, state="readonly")
        self.quality_combobox.pack(anchor=tk.W)
        self.quality_combobox.bind("<<ComboboxSelected>>", self.on_quality_selected)

        # Download Button
        self.download_button = ttk.Button(self.format_frame, text="Download Selected Format", command=self.download_selected_thread, state=tk.DISABLED)
        self.download_button.pack(pady=10)

        self.format_frame.pack(pady=10) # Show the frame
        self.update_quality_options() # Populate combobox initially


    def update_quality_options(self):
        format_type = self.format_type_var.get()
        stream_list = self.streams_data.get(format_type, [])

        if not stream_list:
            self.quality_combobox['values'] = []
            self.quality_combobox.set('')
            self.selected_stream = None
            self.download_button.config(state=tk.DISABLED)
            return

        try:
             sorted_streams = sorted(stream_list,
                                   key=lambda s: (
                                       int(s.resolution[:-1])
                                       if s.resolution and s.resolution.endswith('p')
                                       else int(s.abr[:-4]) if s.abr and s.abr.endswith('kbps')
                                       else 0
                                   ),
                                   reverse=True)
        except Exception as e:
             print(f"Error sorting streams: {e}") # Handle potential sorting errors
             sorted_streams = stream_list # Fallback to unsorted

        self.stream_map = {f"{s.resolution or s.abr} ({s.mime_type})": s for s in sorted_streams}
        options = list(self.stream_map.keys())

        self.quality_combobox['values'] = options
        if options:
            self.quality_combobox.current(0) # Select first item
            self.on_quality_selected() # Update selected_stream
        else:
             self.quality_combobox.set('')
             self.selected_stream = None
             self.download_button.config(state=tk.DISABLED)


    def on_quality_selected(self, event=None):
         selected_option = self.quality_combobox.get()
         if selected_option in self.stream_map:
             self.selected_stream = self.stream_map[selected_option]
             self.download_button.config(state=tk.NORMAL)
         else:
             self.selected_stream = None
             self.download_button.config(state=tk.DISABLED)

    def download_selected_thread(self):
        if not self.selected_stream:
            messagebox.showwarning("Selection Error", "No stream selected.")
            return
        # --- Check if download folder is set ---
        if not self.current_download_folder or not os.path.isdir(self.current_download_folder):
             messagebox.showerror("Configuration Error", "Invalid download folder selected. Please select a valid folder.")
             self.select_download_folder() # Prompt user to select again
             return
        # --- End Check ---


        self.update_status("Downloading...")
        self.download_button.config(state=tk.DISABLED)
        self.show_formats_button.config(state=tk.DISABLED)

        # Run download in a separate thread, passing the current folder
        thread = threading.Thread(target=self.download_task, args=(self.selected_stream, self.video_title, self.current_download_folder))
        thread.start()

    def download_task(self, stream, title, download_folder): # <-- Add download_folder parameter
        try:
            # Pass the download_folder to the download function
            file_path, file_name = download_selected_stream(stream, title, download_folder)
            # self.download_path = file_path # Store path if needed later (optional)
            self.root.after(0, lambda: messagebox.showinfo("Success", f"Downloaded '{file_name}' to '{download_folder}'")) # Use the actual folder path
            self.root.after(0, lambda: self.update_status(f"Download complete: {file_name}"))
            # You might add a button here to open the download_folder
            # Example: self.root.after(0, lambda: os.startfile(download_folder)) # Windows only
            # Example: self.root.after(0, lambda: subprocess.run(['open', download_folder])) # macOS
            # Example: self.root.after(0, lambda: subprocess.run(['xdg-open', download_folder])) # Linux
            # (Requires importing subprocess)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Download Error", f"Failed to download: {str(e)}"))
            self.root.after(0, lambda: self.update_status(f"Download failed: {str(e)}", True))
        finally:
            # Re-enable buttons on the main thread
            self.root.after(0, lambda: self.download_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.show_formats_button.config(state=tk.NORMAL))


# --- Main Execution ---
if __name__ == "__main__":
    root = tk.Tk()
    app = DownloaderApp(root)
    root.mainloop()