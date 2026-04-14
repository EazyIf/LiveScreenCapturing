import sys
import os
import socket
import cv2
import numpy as np
from mss import mss
import pyautogui
import struct
import time
import tkinter as tk
from threading import Thread, Event

shutdown = Event()


def get_local_ip():
    """Get LAN IP address (works on both Windows and Linux)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return socket.gethostbyname(socket.gethostname())


host_ip = get_local_ip()


# ── Services ──────────────────────────────────────────────────────

def HostKeyboard(on_status):
    from pynput.keyboard import Key, Controller
    kbd = Controller()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(1.0)
    sock.bind((host_ip, 1223))
    sock.listen(3)

    client = None
    while not shutdown.is_set():
        try:
            client, addr = sock.accept()
            on_status(f"Connected ({addr[0]})")
            break
        except socket.timeout:
            continue

    if not client:
        sock.close()
        return

    client.settimeout(1.0)
    while not shutdown.is_set():
        try:
            msg = client.recv(1024).decode()
            if not msg:
                break
            try:
                if 'Key' not in msg:
                    kbd.type(eval(msg.split('.')[1]))
                else:
                    key = getattr(Key, msg.split(".")[2])
                    func = getattr(kbd, msg.split(".")[0])
                    func(key)
            except (AttributeError, SyntaxError, IndexError):
                pass
        except socket.timeout:
            continue
        except Exception:
            break

    client.close()
    sock.close()


def HostScreenCapturing(on_status):
    JPEG_QUALITY = 85
    MAX_FPS = 30
    CHUNK_SIZE = 60000

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(1.0)
    sock.bind((host_ip, 9999))

    client_addr = None
    while not shutdown.is_set():
        try:
            data, addr = sock.recvfrom(1024)
            if data == b"hello":
                client_addr = addr
                on_status(f"Connected ({addr[0]})")
                break
        except socket.timeout:
            continue

    if not client_addr:
        sock.close()
        return

    sct = mss()
    monitor = sct.monitors[1]
    width, height = monitor["width"], monitor["height"]
    sock.sendto(struct.pack("!HH", width, height), client_addr)

    frame_seq = 0
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]

    while not shutdown.is_set():
        t = time.time()

        screenshot = sct.grab(monitor)
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

        _, encoded = cv2.imencode(".jpg", frame, encode_params)
        data = encoded.tobytes()

        total_chunks = (len(data) + CHUNK_SIZE - 1) // CHUNK_SIZE
        for i in range(total_chunks):
            s = i * CHUNK_SIZE
            e = min(s + CHUNK_SIZE, len(data))
            header = struct.pack("!IHH", frame_seq, i, total_chunks)
            try:
                sock.sendto(header + data[s:e], client_addr)
            except Exception:
                pass

        frame_seq += 1
        sleep = (1.0 / MAX_FPS) - (time.time() - t)
        if sleep > 0:
            time.sleep(sleep)

    sock.close()


def HostMouseCourseControlling(on_status):
    from pynput.mouse import Button, Controller

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(1.0)
    sock.bind((host_ip, 9922))
    sock.listen(1)

    client = None
    while not shutdown.is_set():
        try:
            client, addr = sock.accept()
            on_status(f"Connected ({addr[0]})")
            break
        except socket.timeout:
            continue

    if not client:
        sock.close()
        return

    mouse = Controller()
    screenW, screenH = pyautogui.size()
    mouse.position = (screenW // 2, screenH // 2)

    buttons = {
        'Button.left': Button.left,
        'Button.right': Button.right,
        'Button.middle': Button.middle,
    }

    client.settimeout(1.0)
    while not shutdown.is_set():
        try:
            data = client.recv(1024).decode()
            if not data:
                break
            for event in data.split('\n'):
                parts = event.split()
                if len(parts) < 2:
                    continue
                etype = parts[0]
                try:
                    if etype == 'MOVE' and len(parts) >= 3:
                        mouse.position = (int(parts[1]), int(parts[2]))
                    elif etype in ('PRESS', 'RELEASE') and len(parts) >= 4:
                        btn = buttons.get(parts[1], Button.unknown)
                        x, y = int(parts[2]), int(parts[3])
                        mouse.position = (x, y)
                        if etype == 'PRESS':
                            mouse.press(btn)
                        else:
                            mouse.release(btn)
                except ValueError:
                    continue
        except socket.timeout:
            continue
        except Exception:
            break

    client.close()
    sock.close()


# ── GUI ───────────────────────────────────────────────────────────

class HostGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Live Screen Capture - Host")
        self.root.configure(bg="#2b2b2b")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        w, h = 400, 340
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        # Title
        tk.Label(self.root, text="Live Screen Capture",
                 font=("Arial", 18, "bold"), fg="white",
                 bg="#2b2b2b").pack(pady=(25, 2))
        tk.Label(self.root, text="HOST",
                 font=("Arial", 11), fg="#888",
                 bg="#2b2b2b").pack(pady=(0, 15))

        # IP display
        ip_frame = tk.Frame(self.root, bg="#2b2b2b")
        ip_frame.pack()
        tk.Label(ip_frame, text="IP:  ",
                 font=("Arial", 14), fg="white",
                 bg="#2b2b2b").pack(side=tk.LEFT)
        tk.Label(ip_frame, text=host_ip,
                 font=("Arial", 14, "bold"), fg="#4CAF50",
                 bg="#2b2b2b").pack(side=tk.LEFT)

        # Status panel
        status_frame = tk.Frame(self.root, bg="#363636", padx=15, pady=12)
        status_frame.pack(pady=18, padx=30, fill=tk.X)

        self.vars = {}
        for name in ("Keyboard", "Screen", "Mouse"):
            row = tk.Frame(status_frame, bg="#363636")
            row.pack(fill=tk.X, pady=3)
            tk.Label(row, text=f"{name}:",
                     font=("Arial", 11), fg="white",
                     bg="#363636", width=10, anchor="e").pack(side=tk.LEFT)
            v = tk.StringVar(value="Waiting...")
            self.vars[name.lower()] = v
            tk.Label(row, textvariable=v,
                     font=("Arial", 11), fg="#FFC107",
                     bg="#363636").pack(side=tk.LEFT, padx=8)

        # Stop button
        tk.Button(self.root, text="Stop Server",
                  font=("Arial", 12, "bold"), fg="white",
                  bg="#f44336", activebackground="#d32f2f",
                  command=self.on_close, padx=20, pady=6,
                  relief=tk.FLAT).pack(pady=18)

    def set_status(self, service, text):
        self.root.after(0, lambda: self.vars[service].set(text))

    def on_close(self):
        shutdown.set()
        self.root.destroy()
        os._exit(0)

    def run(self):
        self.root.mainloop()


# ── Start ─────────────────────────────────────────────────────────

gui = HostGUI()

Thread(target=HostKeyboard,
       args=(lambda t: gui.set_status("keyboard", t),), daemon=True).start()
Thread(target=HostScreenCapturing,
       args=(lambda t: gui.set_status("screen", t),), daemon=True).start()
Thread(target=HostMouseCourseControlling,
       args=(lambda t: gui.set_status("mouse", t),), daemon=True).start()

gui.run()
