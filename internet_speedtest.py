import tkinter as tk
from tkinter import ttk, messagebox
import threading
import speedtest
from PIL import Image, ImageTk, ImageOps
import os
from datetime import datetime
import queue
import json

class SpeedTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🌐 Internet Speed Test")
        self.root.geometry("500x600")
        self.root.minsize(450, 550)
        
        # Theme settings
        self.themes = {
            "Dark": {"fg": "white", "accent": "#00BFFF", "bg1": "#141E30", "bg2": "#243B55"},
            "Light": {"fg": "black", "accent": "#0078D7", "bg1": "#89f7fe", "bg2": "#66a6ff"}
        }
        self.current_theme = "Dark"
        
        # Queue for thread-safe communication
        self.update_queue = queue.Queue()
        
        # Test history
        self.test_history = []
        self.history_file = "speed_test_history.json"
        
        # Load previous test history
        self.load_history()
        
        # Load logo and set taskbar icon first
        self.load_logo()
        
        # Setup UI
        self.setup_ui()
        self.apply_theme()
        self.update_logo()
        self.display_history()  # Display loaded history
        
        # Start clock and queue processor
        self.update_clock()
        self.process_queue()
        
        # Create gradient after UI is set up
        self.root.after(100, self.create_gradient_image)
        
    def load_history(self):
        """Load test history from file"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    self.test_history = json.load(f)
                # Keep only last 5 tests
                if len(self.test_history) > 5:
                    self.test_history = self.test_history[-5:]
                
        except Exception as e:
            
            self.test_history = []
    
    def save_history(self):
        """Save test history to file"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.test_history, f, indent=2)
            
        except Exception as e:
            print(f"Error saving history: {e}")
    
    def load_logo(self):
        """Load logo and set taskbar icon"""
        self.logo_path = "logo.png"
        self.logo_original = None
        self.icon_photos = []  # Keep references to prevent garbage collection
        
        if os.path.exists(self.logo_path):
            try:
                self.logo_original = Image.open(self.logo_path).convert("RGBA")
                
                # Create ICO file for Windows taskbar (more reliable)
                ico_path = "app_icon.ico"
                try:
                    # Save as ICO with multiple sizes
                    self.logo_original.save(ico_path, format='ICO', 
                                           sizes=[(16,16), (32,32), (48,48), (64,64), (128,128)])
                    # Set icon from ICO file
                    self.root.iconbitmap(ico_path)
                    
                except Exception as ico_error:
                    print(f"ICO creation failed: {ico_error}, trying PhotoImage method")
                
                # Also try PhotoImage method as backup
                icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
                for size in icon_sizes:
                    icon_img = self.logo_original.resize(size, Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(icon_img)
                    self.icon_photos.append(photo)
                
                # Set all icon sizes for best compatibility
                if self.icon_photos:
                    self.root.iconphoto(True, *self.icon_photos)
                
                
            except Exception as e:
                
                self.logo_original = None
                
        """Load logo and set taskbar icon"""
        self.logo_path = "C:/Users/smm66/Downloads/Internetspeed/logo.png"
        self.logo_original = None
        self.icon_photos = []  # Keep references to prevent garbage collection
        
        if os.path.exists(self.logo_path):
            try:
                self.logo_original = Image.open(self.logo_path).convert("RGBA")
                
                # Create multiple icon sizes for Windows taskbar
                icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128)]
                for size in icon_sizes:
                    icon_img = self.logo_original.resize(size, Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(icon_img)
                    self.icon_photos.append(photo)
                
                # Set all icon sizes for best compatibility
                self.root.iconphoto(True, *self.icon_photos)
                
            except Exception as e:
                
                self.logo_original = None
    
            
        
    def setup_ui(self):
        # Get initial theme background color
        initial_bg = self.themes[self.current_theme]["bg1"]
        
        # Canvas for gradient background
        self.canvas = tk.Canvas(self.root, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self.on_resize)
        
        # Main frame
        self.frame_main = tk.Frame(self.canvas, bg=initial_bg)
        self.canvas_frame = self.canvas.create_window(250, 300, window=self.frame_main, anchor="center")
        
        # Logo display
        if self.logo_original:
            self.logo_label = tk.Label(self.frame_main, bg=initial_bg, bd=0)
        else:
            self.logo_label = tk.Label(self.frame_main, text="🌐", font=("Segoe UI Emoji", 40), bg=initial_bg)
        self.logo_label.pack(pady=10)
        
        # Title
        self.title = tk.Label(self.frame_main, text="Internet Speed Test", 
                             font=("Segoe UI", 16, "bold"), bg=initial_bg)
        self.title.pack(pady=5)
        
        # Clock
        self.clock_label = tk.Label(self.frame_main, text="", font=("Segoe UI", 12, "bold"), 
                                    bg=initial_bg)
        self.clock_label.pack(pady=5)
        
        # Server info
        self.server_label = tk.Label(self.frame_main, text="", font=("Segoe UI", 9), 
                                     bg=initial_bg)
        self.server_label.pack(pady=2)
        
        # Info frame
        info_frame = tk.Frame(self.frame_main, bg=initial_bg)
        info_frame.pack(pady=15)
        
        self.label_download = tk.Label(info_frame, text="Download Speed:", 
                                       font=("Segoe UI", 11), bg=initial_bg)
        self.label_upload = tk.Label(info_frame, text="Upload Speed:", 
                                     font=("Segoe UI", 11), bg=initial_bg)
        self.label_ping = tk.Label(info_frame, text="Ping:", 
                                   font=("Segoe UI", 11), bg=initial_bg)
        
        self.label_download.grid(row=0, column=0, sticky="w", pady=5, padx=10)
        self.label_upload.grid(row=1, column=0, sticky="w", pady=5, padx=10)
        self.label_ping.grid(row=2, column=0, sticky="w", pady=5, padx=10)
        
        self.label_download_val = tk.Label(info_frame, text="-- Mbps", 
                                          font=("Segoe UI", 11, "bold"), bg=initial_bg)
        self.label_upload_val = tk.Label(info_frame, text="-- Mbps", 
                                        font=("Segoe UI", 11, "bold"), bg=initial_bg)
        self.label_ping_val = tk.Label(info_frame, text="-- ms", 
                                      font=("Segoe UI", 11, "bold"), bg=initial_bg)
        
        self.label_download_val.grid(row=0, column=1, padx=10)
        self.label_upload_val.grid(row=1, column=1, padx=10)
        self.label_ping_val.grid(row=2, column=1, padx=10)
        
        # Progress bar
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.progress = ttk.Progressbar(self.frame_main, orient="horizontal", 
                                       mode="determinate", length=350, maximum=100)
        self.progress.pack(pady=15)
        
        # Buttons frame
        btn_frame = tk.Frame(self.frame_main, bg=initial_bg)
        btn_frame.pack(pady=10)
        
        self.btn_test = ttk.Button(btn_frame, text="Start Test", command=self.run_test_thread)
        self.btn_test.grid(row=0, column=0, padx=5)
        
        self.btn_theme = ttk.Button(btn_frame, text="Switch to Light Theme", command=self.toggle_theme)
        self.btn_theme.grid(row=0, column=1, padx=5)
        
        # Status label
        self.label_status = tk.Label(self.frame_main, text="Ready to test", 
                                     font=("Segoe UI", 10), bg=initial_bg)
        self.label_status.pack(pady=5)
        
        # History frame
        history_frame = tk.Frame(self.frame_main, bg=initial_bg)
        history_frame.pack(pady=5, fill="x", padx=20)
        
        self.history_label = tk.Label(history_frame, text="Previous Tests:", 
                                      font=("Segoe UI", 9, "bold"), bg=initial_bg)
        self.history_label.pack(anchor="w")
        
        self.history_text = tk.Label(history_frame, text="No tests yet", 
                                     font=("Segoe UI", 8), bg=initial_bg, 
                                     justify="left", wraplength=400)
        self.history_text.pack(anchor="w")
        
        # Footer
        self.footer = tk.Label(self.frame_main, text="Developed by Saikat Majumder", 
                              font=("Segoe UI", 8), bg=initial_bg)
        self.footer.pack(pady=10)
        
    def create_gradient_image(self):
        """Create gradient as an image for better performance"""
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        if width <= 1 or height <= 1:
            self.root.after(100, self.create_gradient_image)
            return
        
        theme = self.themes[self.current_theme]
        
        # Convert colors
        c1 = self.root.winfo_rgb(theme["bg1"])
        c2 = self.root.winfo_rgb(theme["bg2"])
        
        # Create gradient image
        gradient = Image.new("RGB", (width, height))
        pixels = gradient.load()
        
        for y in range(height):
            ratio = y / height
            r = int(c1[0] * (1 - ratio) + c2[0] * ratio) >> 8
            g = int(c1[1] * (1 - ratio) + c2[1] * ratio) >> 8
            b = int(c1[2] * (1 - ratio) + c2[2] * ratio) >> 8
            
            for x in range(width):
                pixels[x, y] = (r, g, b)
        
        self.gradient_photo = ImageTk.PhotoImage(gradient)
        self.canvas.delete("gradient")
        self.canvas.create_image(0, 0, image=self.gradient_photo, anchor="nw", tags="gradient")
        self.canvas.tag_lower("gradient")
        
    def on_resize(self, event=None):
        """Handle window resize"""
        self.root.after(100, self.create_gradient_image)
        # Center the frame
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        self.canvas.coords(self.canvas_frame, width // 2, height // 2)
        
    def update_logo(self):
        """Update logo based on theme"""
        if self.logo_original:
            logo_resized = self.logo_original.resize((100, 100), Image.Resampling.LANCZOS)
            if self.current_theme == "Light":
                r, g, b, a = logo_resized.split()
                rgb_image = Image.merge("RGB", (r, g, b))
                inverted_image = ImageOps.invert(rgb_image)
                inverted_image.putalpha(a)
                logo_img = inverted_image
            else:
                logo_img = logo_resized
            
            # Keep strong reference to prevent garbage collection
            self.logo_photo = ImageTk.PhotoImage(logo_img)
            self.logo_label.config(image=self.logo_photo)
        
        # Update frame background to match theme
        theme_bg = self.themes[self.current_theme]["bg1"]
        self.frame_main.config(bg=theme_bg)
        
    def toggle_theme(self):
        """Toggle between dark and light themes"""
        self.current_theme = "Light" if self.current_theme == "Dark" else "Dark"
        self.apply_theme()
        self.update_logo()
        self.create_gradient_image()
        
    def apply_theme(self):
        """Apply the current theme to all widgets"""
        theme = self.themes[self.current_theme]
        fg = theme["fg"]
        accent = theme["accent"]
        bg = theme["bg1"]
        
        # Update frame background
        self.frame_main.config(bg=bg)
        
        # Get all frames
        info_frame = self.label_download.master
        btn_frame = self.btn_test.master
        history_frame = self.history_label.master
        
        for frame in [info_frame, btn_frame, history_frame]:
            frame.config(bg=bg)
        
        widgets = [self.title, self.label_download, self.label_upload, self.label_ping,
                  self.label_download_val, self.label_upload_val, self.label_ping_val,
                  self.label_status, self.footer, self.clock_label, self.server_label,
                  self.history_label, self.history_text, self.logo_label]
        
        for widget in widgets:
            widget.config(foreground=fg, bg=bg)
            
        self.style.configure("Horizontal.TProgressbar", background=accent, troughcolor="#333333")
        self.btn_theme.config(text=f"Switch to {'Dark' if self.current_theme == 'Light' else 'Light'} Theme")
        
    def update_clock(self):
        """Update the clock display"""
        now = datetime.now().strftime("%H:%M:%S")
        self.clock_label.config(text=now)
        self.root.after(1000, self.update_clock)
        
    def process_queue(self):
        """Process updates from the test thread"""
        try:
            while True:
                update = self.update_queue.get_nowait()
                update_type = update.get("type")
                
                if update_type == "status":
                    self.label_status.config(text=update["text"])
                elif update_type == "server":
                    self.server_label.config(text=update["text"])
                elif update_type == "download":
                    self.label_download_val.config(text=f"{update['value']:.2f} Mbps")
                elif update_type == "upload":
                    self.label_upload_val.config(text=f"{update['value']:.2f} Mbps")
                elif update_type == "ping":
                    self.label_ping_val.config(text=f"{update['value']:.2f} ms")
                elif update_type == "progress":
                    self.progress["value"] = update["value"]
                elif update_type == "button":
                    self.btn_test.config(state=update["state"])
                elif update_type == "error":
                    messagebox.showerror("Error", update["message"])
                elif update_type == "history":
                    self.add_to_history(update["data"])
                    
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_queue)
            
    def add_to_history(self, data):
        """Add test result to history"""
        self.test_history.append(data)
        # Keep only last 5 tests
        if len(self.test_history) > 5:
            self.test_history.pop(0)
        
        # Save to file
        self.save_history()
        
        # Display updated history
        self.display_history()
    
    def display_history(self):
        """Display test history"""
        if not self.test_history:
            self.history_text.config(text="No tests yet")
            return
            
        history_text = ""
        for i, test in enumerate(reversed(self.test_history), 1):
            date_str = test.get('date', test.get('time', ''))
            history_text += f"{i}. {date_str} - ↓{test['download']:.1f} ↑{test['upload']:.1f} Mbps, Ping: {test['ping']:.0f}ms\n"
        
        self.history_text.config(text=history_text.strip())
        
    def test_speed(self):
        """Run the speed test in a separate thread"""
        try:
            self.update_queue.put({"type": "button", "state": tk.DISABLED})
            self.update_queue.put({"type": "status", "text": "Initializing speed test..."})
            self.update_queue.put({"type": "progress", "value": 0})
            
            st = speedtest.Speedtest()
            
            self.update_queue.put({"type": "status", "text": "Finding best server..."})
            self.update_queue.put({"type": "progress", "value": 10})
            st.get_best_server()
            
            server_info = f"Server: {st.best['sponsor']} ({st.best['country']})"
            self.update_queue.put({"type": "server", "text": server_info})
            self.update_queue.put({"type": "progress", "value": 20})
            
            # Download test
            self.update_queue.put({"type": "status", "text": "Testing download speed..."})
            self.update_queue.put({"type": "progress", "value": 30})
            download_speed = st.download() / 1_000_000
            self.update_queue.put({"type": "download", "value": download_speed})
            self.update_queue.put({"type": "progress", "value": 60})
            
            # Upload test
            self.update_queue.put({"type": "status", "text": "Testing upload speed..."})
            self.update_queue.put({"type": "progress", "value": 70})
            upload_speed = st.upload() / 1_000_000
            self.update_queue.put({"type": "upload", "value": upload_speed})
            self.update_queue.put({"type": "progress", "value": 90})
            
            # Ping
            ping = st.results.ping
            self.update_queue.put({"type": "ping", "value": ping})
            self.update_queue.put({"type": "progress", "value": 100})
            
            # Add to history
            test_data = {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "time": datetime.now().strftime("%H:%M:%S"),
                "download": download_speed,
                "upload": upload_speed,
                "ping": ping
            }
            self.update_queue.put({"type": "history", "data": test_data})
            
            self.update_queue.put({"type": "status", "text": "✅ Test Completed Successfully"})
            
        except speedtest.ConfigRetrievalError:
            error_msg = "Failed to retrieve speedtest configuration. Please check your internet connection."
            self.update_queue.put({"type": "error", "message": error_msg})
            self.update_queue.put({"type": "status", "text": "❌ Configuration Error"})
        except speedtest.NoMatchedServers:
            error_msg = "No speedtest servers found. Please check your internet connection."
            self.update_queue.put({"type": "error", "message": error_msg})
            self.update_queue.put({"type": "status", "text": "❌ No Servers Found"})
        except Exception as e:
            error_msg = f"Test failed: {str(e)}\n\nPlease check:\n- Internet connection\n- Firewall settings\n- VPN configuration"
            self.update_queue.put({"type": "error", "message": error_msg})
            self.update_queue.put({"type": "status", "text": "❌ Test Failed"})
        finally:
            self.update_queue.put({"type": "button", "state": tk.NORMAL})
            self.update_queue.put({"type": "progress", "value": 0})
            
    def run_test_thread(self):
        """Start the speed test in a new thread"""
        threading.Thread(target=self.test_speed, daemon=True).start()

def main():
    root = tk.Tk()
    app = SpeedTestApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()