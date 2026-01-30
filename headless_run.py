import threading
import queue
import time
from bot import worker_loop
import os
import sys

# Configure stdout logging to ensure logs appear in Render dashboard
import logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

def log_printer(log_queue):
    while True:
        try:
            msg = log_queue.get()
            print(f"[BOT LOG] {msg}")
            sys.stdout.flush()
        except:
            break

if __name__ == "__main__":
    print("Starting Headless Bot...")
    
    # Check for namber.text
    if not os.path.exists("namber.text"):
        print("Error: namber.text not found. Please ensure the file exists.")
        exit(1)

    try:
        with open("namber.text", "r") as f:
            numbers = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Error reading file: {e}")
        exit(1)

    if not numbers:
        print("No numbers found in namber.text")
        exit(1)

    print(f"Loaded {len(numbers)} numbers.")

    number_queue = queue.Queue()
    for n in numbers:
        number_queue.put(n)

    log_queue = queue.Queue()
    
    # Start log printer in background
    printing_thread = threading.Thread(target=log_printer, args=(log_queue,), daemon=True)
    printing_thread.start()

    # Run the worker
    print("Initializing worker...")
    # Using 1 worker for stability in headless environment
    # You can increase this if your server resources allow
    try:
        worker_loop(number_queue, log_queue, headless=True)
    except Exception as e:
        print(f"Critical Error: {e}")
    
    print("All tasks finished.")
