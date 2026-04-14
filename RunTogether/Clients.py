import sys
import os
import socket
import cv2
import numpy as np
import pyautogui
import struct
import time
import tkinter as tk
from threading import Thread, Event
from pynput import keyboard as kb
from pynput.keyboard import Key

shutdown = Event()


# ── Connect Dialog ────────────────────────────────────────────────

def get_host_ip():
    """Show a dialog asking the user for the host IP. Returns IP or None."""
    result = {"ip": None}

    def on_connect():
        ip = entry.get().strip()
        if ip:
            result["ip"] = ip
            root.destroy()

    root = tk.Tk()
    root.title("Live Screen Capture - Connect")
    root.configure(bg="#2b2b2b")
    root.resizable(False, False)
    root.protocol("WM_DELETE_WINDOW", root.destroy)

    w, h = 380, 220
    x = (root.winfo_screenwidth() - w) // 2
    y = (root.winfo_screenheight() - h) // 2
    root.geometry(f"{w}x{h}+{x}+{y}")

    tk.Label(root, text="Live Screen Capture",
             font=("Arial", 18, "bold"), fg="white",
             bg="#2b2b2b").pack(pady=(25, 2))
    tk.Label(root, text="CLIENT",
             font=("Arial", 11), fg="#888",
             bg="#2b2b2b").pack(pady=(0, 20))

    frame = tk.Frame(root, bg="#2b2b2b")
    frame.pack()
    tk.Label(frame, text="Host IP:",
             font=("Arial", 12), fg="white",
             bg="#2b2b2b").pack(side=tk.LEFT, padx=(0, 8))
    entry = tk.Entry(frame, font=("Arial", 13), width=18)
    entry.pack(side=tk.LEFT)

    tk.Button(root, text="Connect",
              font=("Arial", 12, "bold"), fg="white",
              bg="#4CAF50", activebackground="#388E3C",
              command=on_connect, padx=25, pady=5,
              relief=tk.FLAT).pack(pady=22)

    entry.bind("<Return>", lambda e: on_connect())
    entry.focus_set()

    root.mainloop()
    return result["ip"]


# ── Keyboard (with local input suppression) ───────────────────────

def ClientKeyboard(host_ip):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host_ip, 1223))
    except Exception as e:
        print(f"Keyboard connection failed: {e}")
        return
    print("Keyboard connected")

    def on_press(key):
        if shutdown.is_set():
            return False
        # ESC = exit, don't forward to host
        if key == Key.esc:
            shutdown.set()
            return False
        try:
            sock.send(f"press.{key}".encode())
        except Exception:
            pass

    def on_release(key):
        if shutdown.is_set():
            return False
        rls = f"release.{key}"
        if "Key" in rls:
            try:
                sock.send(rls.encode())
            except Exception:
                pass

    # suppress=True locks local keyboard — keys only go to host
    try:
        listener = kb.Listener(on_press=on_press, on_release=on_release,
                               suppress=True)
        listener.start()
        print("Keyboard input locked (press ESC to exit)")
    except Exception:
        listener = kb.Listener(on_press=on_press, on_release=on_release)
        listener.start()
        print("Keyboard connected (WARNING: could not lock local input)")

    while not shutdown.is_set():
        time.sleep(0.1)

    listener.stop()
    sock.close()


# ── Mouse ─────────────────────────────────────────────────────────

def ClientMouseCourseControlling(host_ip):
    from pynput.mouse import Controller, Listener

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host_ip, 9922))
    except Exception as e:
        print(f"Mouse connection failed: {e}")
        return
    print("Mouse connected")

    mouse = Controller()
    sw, sh = pyautogui.size()
    mouse.position = (sw // 2, sh // 2)

    def send_event(event):
        if shutdown.is_set():
            return
        try:
            sock.send((event + "\n").encode())
        except Exception:
            pass

    def on_click(x, y, button, pressed):
        if shutdown.is_set():
            return False
        if pressed:
            send_event(f"PRESS {button} {x} {y}")
        else:
            send_event(f"RELEASE {button} {x} {y}")

    listener = Listener(on_click=on_click)
    listener.start()
    prev_x, prev_y = mouse.position

    while not shutdown.is_set():
        x, y = mouse.position
        if x != prev_x or y != prev_y:
            send_event(f"MOVE {x} {y}")
            prev_x, prev_y = x, y
        time.sleep(0.01)

    listener.stop()
    sock.close()


# ── Screen Capture (main thread) ─────────────────────────────────

def ClientScreenCapturing(host_ip):
    """Must run in the main thread — cv2.imshow requires it on Linux."""
    BUFFER_SIZE = 65535

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)
    sock.settimeout(5.0)

    sock.sendto(b"hello", (host_ip, 9999))
    print(f"Screen connecting to {host_ip}:9999...")

    try:
        dim_data, _ = sock.recvfrom(1024)
    except socket.timeout:
        print("ERROR: No response from host. Is it running?")
        shutdown.set()
        return

    host_w, host_h = struct.unpack("!HH", dim_data)
    print(f"Host screen: {host_w}x{host_h}")

    sock.settimeout(0.5)

    # EXIT button position (top-right of the frame)
    btn_w, btn_h = 100, 40
    btn_x = host_w - btn_w - 10
    btn_y = 10
    exit_clicked = [False]

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if btn_x <= x <= btn_x + btn_w and btn_y <= y <= btn_y + btn_h:
                exit_clicked[0] = True

    cv2.namedWindow("RECEIVING VIDEO", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("RECEIVING VIDEO", cv2.WND_PROP_FULLSCREEN,
                          cv2.WINDOW_FULLSCREEN)
    cv2.setMouseCallback("RECEIVING VIDEO", on_mouse)

    frames = {}
    last_displayed_seq = -1
    timeout_count = 0

    while not shutdown.is_set() and not exit_clicked[0]:
        try:
            packet, _ = sock.recvfrom(BUFFER_SIZE)
            timeout_count = 0
        except socket.timeout:
            timeout_count += 1
            if timeout_count > 20:
                print("Host disconnected.")
                break
            cv2.waitKey(1)
            continue
        except socket.error:
            continue

        if len(packet) < 8:
            continue

        frame_seq, chunk_idx, total_chunks = struct.unpack("!IHH", packet[:8])
        chunk_data = packet[8:]

        if frame_seq <= last_displayed_seq:
            continue

        if frame_seq not in frames:
            frames[frame_seq] = {}
        frames[frame_seq][chunk_idx] = chunk_data

        if len(frames[frame_seq]) == total_chunks:
            frame_bytes = b"".join(
                frames[frame_seq][i] for i in range(total_chunks))
            frame = cv2.imdecode(
                np.frombuffer(frame_bytes, dtype=np.uint8),
                cv2.IMREAD_COLOR)

            if frame is not None:
                # Draw EXIT button
                cv2.rectangle(frame,
                              (btn_x, btn_y),
                              (btn_x + btn_w, btn_y + btn_h),
                              (0, 0, 200), -1)
                cv2.rectangle(frame,
                              (btn_x, btn_y),
                              (btn_x + btn_w, btn_y + btn_h),
                              (0, 0, 160), 2)
                cv2.putText(frame, "EXIT",
                            (btn_x + 18, btn_y + 28),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7, (255, 255, 255), 2)
                cv2.imshow("RECEIVING VIDEO", frame)

            last_displayed_seq = frame_seq
            frames = {k: v for k, v in frames.items() if k > frame_seq}

        cv2.waitKey(1)

    shutdown.set()
    cv2.destroyAllWindows()
    sock.close()


# ── Main ──────────────────────────────────────────────────────────

host_ip = get_host_ip()
if not host_ip:
    sys.exit(0)

print(f"Connecting to {host_ip}...")

# Keyboard and mouse in background threads
Thread(target=ClientKeyboard, args=(host_ip,), daemon=True).start()
Thread(target=ClientMouseCourseControlling, args=(host_ip,), daemon=True).start()

# Screen capture MUST run in the main thread (cv2.imshow on Linux)
ClientScreenCapturing(host_ip)
os._exit(0)
