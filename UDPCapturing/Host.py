import socket
import cv2
import numpy as np
from mss import mss
import struct
import time

# ── Configuration ──────────────────────────────────────────────────
JPEG_QUALITY = 85       # High quality (0-100). 85 is near-lossless for screens.
MAX_FPS = 30            # Cap frame rate to avoid flooding the network
UDP_PORT = 9999
CHUNK_SIZE = 60000      # Max payload per UDP packet (bytes)
# ───────────────────────────────────────────────────────────────────


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


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    host_ip = get_local_ip()

    sock.bind((host_ip, UDP_PORT))
    print(f"HOST IP: {host_ip}")
    print(f"Waiting for client on port {UDP_PORT}...")

    # Client sends a "hello" packet to register its address
    while True:
        data, client_addr = sock.recvfrom(1024)
        if data == b"hello":
            print(f"Client connected from: {client_addr}")
            break
        print(f"Ignored unknown packet from {client_addr}: {data!r}")

    # Send screen dimensions so client knows the resolution
    sct = mss()
    monitor = sct.monitors[1]  # Primary monitor
    width = monitor["width"]
    height = monitor["height"]
    dimensions = struct.pack("!HH", width, height)
    sock.sendto(dimensions, client_addr)

    frame_seq = 0
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]

    print(f"Streaming {width}x{height} @ up to {MAX_FPS} FPS  |  JPEG quality {JPEG_QUALITY}")

    while True:
        start_time = time.time()

        # Capture screen with mss (5-10x faster than pyautogui)
        screenshot = sct.grab(monitor)
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

        # JPEG encode – compresses a 1080p frame from ~6 MB to ~200-400 KB
        _, encoded = cv2.imencode(".jpg", frame, encode_params)
        data = encoded.tobytes()

        # Split into UDP-safe chunks
        total_chunks = (len(data) + CHUNK_SIZE - 1) // CHUNK_SIZE

        for i in range(total_chunks):
            start = i * CHUNK_SIZE
            end = min(start + CHUNK_SIZE, len(data))
            chunk = data[start:end]

            # Header: frame_seq (4B) | chunk_index (2B) | total_chunks (2B)
            header = struct.pack("!IHH", frame_seq, i, total_chunks)
            sock.sendto(header + chunk, client_addr)

        frame_seq += 1

        # Cap frame rate
        elapsed = time.time() - start_time
        sleep_time = (1.0 / MAX_FPS) - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)

    sock.close()


if __name__ == "__main__":
    main()
