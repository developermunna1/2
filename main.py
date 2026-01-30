import customtkinter as ctk
import threading
import queue
import os
from tkinter import filedialog
from bot import worker_loop
import concurrent.futures

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Facebook Recovery Tool - High Speed")
        self.geometry("650x550")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        # File Selection
        self.file_frame = ctk.CTkFrame(self)
        self.file_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        
        self.file_label = ctk.CTkLabel(self.file_frame, text="Select namber.text File:")
        self.file_label.pack(side="left", padx=10)
        
        self.file_path_entry = ctk.CTkEntry(self.file_frame, width=300)
        self.file_path_entry.pack(side="left", padx=10)
        if os.path.exists("namber.text"):
            self.file_path_entry.insert(0, os.path.abspath("namber.text"))
        
        self.browse_btn = ctk.CTkButton(self.file_frame, text="Browse", command=self.browse_file)
        self.browse_btn.pack(side="left", padx=10)

        # Worker Configuration
        self.config_frame = ctk.CTkFrame(self)
        self.config_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        self.worker_label = ctk.CTkLabel(self.config_frame, text="Number of Workers (Simultaneous Browsers):")
        self.worker_label.pack(side="left", padx=10)
        
        self.worker_slider = ctk.CTkSlider(self.config_frame, from_=1, to=10, number_of_steps=9, command=self.update_worker_label)
        self.worker_slider.set(5)
        self.worker_slider.pack(side="left", padx=10, fill="x", expand=True)
        
        self.worker_count_label = ctk.CTkLabel(self.config_frame, text="5")
        self.worker_count_label.pack(side="left", padx=10)

        # Options Configuration
        self.option_frame = ctk.CTkFrame(self)
        self.option_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self.show_browser_var = ctk.BooleanVar(value=True)
        self.show_browser_switch = ctk.CTkSwitch(self.option_frame, text="Show Browsers (Uncheck to Hide/Headless)", variable=self.show_browser_var, onvalue=True, offvalue=False)
        self.show_browser_switch.pack(side="left", padx=20, pady=10)

        self.proxy_label = ctk.CTkLabel(self.option_frame, text="Proxy (IP:Port):")
        self.proxy_label.pack(side="left", padx=5)
        self.proxy_entry = ctk.CTkEntry(self.option_frame, width=200, placeholder_text="e.g. 127.0.0.1:8080")
        self.proxy_entry.pack(side="left", padx=10)

        # Controls
        self.control_frame = ctk.CTkFrame(self)
        self.control_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        self.start_btn = ctk.CTkButton(self.control_frame, text="START RECOVERY", command=self.start_process, fg_color="green", height=40)
        self.start_btn.pack(side="left", padx=10, expand=True, fill="x")
        
        # Log Area
        self.log_textbox = ctk.CTkTextbox(self, width=600, height=250)
        self.log_textbox.grid(row=4, column=0, padx=20, pady=10, sticky="nsew")
        self.log_textbox.configure(state="disabled")

        self.log_queue = queue.Queue()
        self.is_running = False
        
        self.after(100, self.process_queue)

    def browse_file(self):
        filename = filedialog.askopenfilename(initialdir=os.getcwd(), title="Select namber.text", filetypes=(("Text files", "*.text"), ("Text files", "*.txt"), ("All files", "*.*")))
        if filename:
            self.file_path_entry.delete(0, "end")
            self.file_path_entry.insert(0, filename)

    def update_worker_label(self, value):
        self.worker_count_label.configure(text=str(int(value)))

    def log(self, message):
        self.log_queue.put(message)

    def process_queue(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.log_textbox.configure(state="normal")
                self.log_textbox.insert("end", msg + "\n")
                self.log_textbox.see("end")
                self.log_textbox.configure(state="disabled")
        except queue.Empty:
            pass
        self.after(100, self.process_queue)

    def start_process(self):
        if self.is_running:
            return
        
        file_path = self.file_path_entry.get()
        if not os.path.exists(file_path):
            self.log(f"Error: File not found: {file_path}")
            return
        
        try:
            with open(file_path, "r") as f:
                numbers = [line.strip() for line in f if line.strip()]
        except Exception as e:
            self.log(f"Error reading file: {e}")
            return
            
        if not numbers:
            self.log("Error: No numbers found in file.")
            return
            
        self.is_running = True
        self.start_btn.configure(state="disabled", text="Running...")
        worker_count = int(self.worker_slider.get())
        show_browser = self.show_browser_var.get()
        headless = not show_browser
        
        worker_count = int(self.worker_slider.get())
        show_browser = self.show_browser_var.get()
        headless = not show_browser
        proxy = self.proxy_entry.get().strip()
        
        self.log(f"Starting with {len(numbers)} numbers using {worker_count} workers. Headless: {headless}. Proxy: {proxy if proxy else 'None'}...")
        
        # Create a queue and populate it with numbers
        number_queue = queue.Queue()
        for num in numbers:
            number_queue.put(num)

        threading.Thread(target=self.run_workers, args=(number_queue, worker_count, headless, proxy), daemon=True).start()

    def run_workers(self, number_queue, worker_count, headless, proxy):
        # Create worker count number of threads
        threads = []
        for i in range(worker_count):
            t = threading.Thread(target=worker_loop, args=(number_queue, self.log_queue, headless, proxy))
            t.start()
            threads.append(t)
            
        # Wait for all threads to finish
        for t in threads:
            t.join()
            
        self.log("All tasks completed.")
        self.is_running = False
        self.start_btn.configure(state="normal", text="START RECOVERY")

if __name__ == "__main__":
    app = App()
    app.mainloop()
