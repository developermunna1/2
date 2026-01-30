from flask import Flask, render_template, request, jsonify
import threading
import queue
from bot import worker_loop
import logging

app = Flask(__name__)

# Global queues for thread communication
log_queue = queue.Queue()
number_queue = queue.Queue()

# Store logs in memory to serve to client
log_history = []

def log_worker():
    """Reads from log_queue and appends to log_history"""
    while True:
        try:
            msg = log_queue.get()
            log_history.append(msg)
            # Keep only last 1000 logs
            if len(log_history) > 1000:
                log_history.pop(0)
        except:
            break

# Start log worker thread
threading.Thread(target=log_worker, daemon=True).start()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_bot():
    data = request.json
    numbers_text = data.get('numbers', '')
    
    if not numbers_text.strip():
        return jsonify({'status': 'error', 'message': 'No numbers provided'}), 400

    numbers = [line.strip() for line in numbers_text.splitlines() if line.strip()]
    
    if not numbers:
        return jsonify({'status': 'error', 'message': 'No valid numbers found'}), 400

    # Clear previous queue (optional, depending on behavior desired)
    with number_queue.mutex:
        number_queue.queue.clear()
        
    for num in numbers:
        number_queue.put(num)

    # Start bot thread if not already running (or just start a new one? For simplicity, we start new one)
    # Ideally should check if running, but for this simple tool multiple threads might be okay or handled by worker loop
    # We will just spawn a worker.
    
    log_queue.put(f"Starting job with {len(numbers)} numbers...")
    
    # We run the worker loop in a separate thread so it doesn't block Flask
    threading.Thread(target=worker_loop_wrapper, args=(numbers,), daemon=True).start()

    return jsonify({'status': 'success', 'message': f'Started with {len(numbers)} numbers'})

def worker_loop_wrapper(numbers):
    # Populate a fresh queue for this worker
    q = queue.Queue()
    for n in numbers:
        q.put(n)
        
    try:
        worker_loop(q, log_queue, headless=True)
    except Exception as e:
        log_queue.put(f"Critical Worker Error: {str(e)}")

@app.route('/logs')
def get_logs():
    # Return all logs for now, or could implement "since" logic
    # For simplicity, sending all logs. In production better to send only new ones.
    return jsonify({'logs': log_history})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
