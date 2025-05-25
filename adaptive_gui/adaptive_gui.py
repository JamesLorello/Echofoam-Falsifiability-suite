import tkinter as tk
import numpy as np
import json
import time
import threading

# Grid resolution for tension field
GRID = 20
# GUI dimensions (pixels)
WIDTH = 400
HEIGHT = 300

# initialize tau field representing user hesitation/backtracking
tau = np.zeros((GRID, GRID), dtype=float)
chi_signal = 0.0

memory = {"events": []}
last_move_time = None
threshold = 1.0  # tension spike threshold


def log_event(event_type, x, y):
    entry = {"t": time.time(), "type": event_type, "x": x, "y": y}
    memory["events"].append(entry)
    with open("memory.json", "w") as f:
        json.dump(memory, f, indent=2)


def update_tau_from_motion(x, y, dt):
    gx = int(x / WIDTH * GRID)
    gy = int(y / HEIGHT * GRID)
    gx = max(0, min(GRID - 1, gx))
    gy = max(0, min(GRID - 1, gy))
    tau[gy, gx] += dt


def on_motion(event):
    global last_move_time
    now = time.time()
    if last_move_time is None:
        dt = 0
    else:
        dt = now - last_move_time
    last_move_time = now
    update_tau_from_motion(event.x, event.y, dt)
    log_event("move", event.x, event.y)


def on_click(event):
    gx = int(event.x / WIDTH * GRID)
    gy = int(event.y / HEIGHT * GRID)
    gx = max(0, min(GRID - 1, gx))
    gy = max(0, min(GRID - 1, gy))
    tau[gy, gx] *= 0.5  # clicking relieves tension
    log_event("click", event.x, event.y)


# GUI reorganization based on tension gradient
help_visible = False

def manage_interface():
    global tau, help_visible, chi_signal
    tau *= 0.95  # natural tension decay
    grad_y, grad_x = np.gradient(tau)
    grad_mag = np.sqrt(grad_x ** 2 + grad_y ** 2)
    spike = grad_mag.max()
    if spike > threshold and not help_visible:
        help_label.pack(side="bottom", fill="x")
        help_visible = True
        chi_signal = 1.0
    elif spike <= threshold and help_visible:
        help_label.pack_forget()
        help_visible = False
    if chi_signal > 0:
        help_label.config(fg="blue")
        root.after(200, lambda: help_label.config(fg="black"))
        chi_signal = 0
    root.after(100, manage_interface)


# Simulation of user interactions to demonstrate tau relief

def simulate_user_flow():
    path = list(range(50, WIDTH - 50, 10))
    for x in path:
        on_motion(type("Event", (), {"x": x, "y": HEIGHT // 2}))
        time.sleep(0.02)
    on_click(type("Event", (), {"x": path[-1], "y": HEIGHT // 2}))


# Build Tkinter interface
root = tk.Tk()
root.geometry(f"{WIDTH}x{HEIGHT}")
root.title("Adaptive Echofoam GUI")

main_frame = tk.Frame(root)
main_frame.pack(expand=True, fill="both")

for i in range(3):
    btn = tk.Button(main_frame, text=f"Button {i+1}")
    btn.pack(pady=5)

help_label = tk.Label(root, text="Need help?", bg="yellow")

root.bind("<Motion>", on_motion)
root.bind("<Button-1>", on_click)
root.after(100, manage_interface)

# run simulation in background
sim_thread = threading.Thread(target=simulate_user_flow, daemon=True)
sim_thread.start()

root.mainloop()
