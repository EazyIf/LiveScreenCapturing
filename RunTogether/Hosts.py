import socket
import cv2
import numpy as np
from mss import mss
import pyautogui
from threading import Thread
import struct
import time


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
print(f"[*] Listening as {host_ip} : 1223 | 9999 (UDP) | 9922")


def HostKeyboard():
    from pynput.keyboard import Key, Controller

    keyboard = Controller()
    HostKeyboardSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    PORT = 1223
    HostKeyboardSocket.bind((host_ip, PORT))
    HostKeyboardSocket.listen(3)

    ClientKeyboardSocket, ClientKeyboardAddr = HostKeyboardSocket.accept()
    print('GOT CONNECTION FROM:', ClientKeyboardAddr)

    while True:
        msg = ClientKeyboardSocket.recv(1024).decode()
        try:
            if 'Key' not in msg:
                keyboard.type(eval(msg.split('.')[1]))
            else:
                key = getattr(Key, msg.split(".")[2])
                function = getattr(keyboard, msg.split(".")[0])
                function(key)
        except AttributeError:
            print("AttributeError: enterpress")
        except SyntaxError:
            print("SyntaxError: unexpected EOF while parsing")

    ClientKeyboardSocket.close()
    HostKeyboardSocket.close()


def HostScreenCapturing():
    JPEG_QUALITY = 85
    MAX_FPS = 30
    CHUNK_SIZE = 60000

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host_ip, 9999))
    print("Screen capture (UDP) waiting for client on port 9999...")

    while True:
        data, client_addr = sock.recvfrom(1024)
        if data == b"hello":
            print(f"Screen client connected from: {client_addr}")
            break
        print(f"Ignored unknown packet from {client_addr}: {data!r}")

    sct = mss()
    monitor = sct.monitors[1]
    width = monitor["width"]
    height = monitor["height"]
    sock.sendto(struct.pack("!HH", width, height), client_addr)

    frame_seq = 0
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]

    while True:
        start_time = time.time()

        screenshot = sct.grab(monitor)
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

        _, encoded = cv2.imencode(".jpg", frame, encode_params)
        data = encoded.tobytes()

        total_chunks = (len(data) + CHUNK_SIZE - 1) // CHUNK_SIZE
        for i in range(total_chunks):
            start = i * CHUNK_SIZE
            end = min(start + CHUNK_SIZE, len(data))
            header = struct.pack("!IHH", frame_seq, i, total_chunks)
            sock.sendto(header + data[start:end], client_addr)

        frame_seq += 1

        elapsed = time.time() - start_time
        sleep_time = (1.0 / MAX_FPS) - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)

    sock.close()


def HostMouseCourseControlling():
    from pynput.mouse import Button, Controller

    Mouse_Coruse_Server_Socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    Mouse_Coruse_Port = 9922

    Mouse_Coruse_Server_Address = (host_ip, Mouse_Coruse_Port)
    Mouse_Coruse_Server_Socket.bind(Mouse_Coruse_Server_Address)
    Mouse_Coruse_Server_Socket.listen(1)
    Mouse_Coruse_Client_Socket, Mouse_Coruse_Client_Address = Mouse_Coruse_Server_Socket.accept()

    screenW, screenH = pyautogui.size()
    midX = screenW // 2
    midY = screenH // 2
    mouse = Controller()
    mouse.position = (midX, midY)

    def get_button_from_string(button_str):
        if button_str == 'Button.left':
            return Button.left
        elif button_str == 'Button.right':
            return Button.right
        elif button_str == 'Button.middle':
            return Button.middle
        else:
            return Button.unknown

    try:
        while True:
            data = Mouse_Coruse_Client_Socket.recv(1024).decode()
            if not data:
                break
            events = data.split('\n')
            for event in events:
                event_parts = event.split()
                if len(event_parts) < 2:
                    continue

                event_type = event_parts[0]

                if event_type == 'MOVE':
                    if len(event_parts) < 3:
                        continue
                    try:
                        x, y = int(event_parts[1]), int(event_parts[2])
                        mouse.position = (x, y)
                    except ValueError:
                        continue

                elif event_type == 'PRESS' or event_type == 'RELEASE':
                    if len(event_parts) < 4:
                        continue
                    button_str = event_parts[1]
                    button = get_button_from_string(button_str)
                    try:
                        x, y = int(event_parts[2]), int(event_parts[3])
                        if event_type == 'PRESS':
                            mouse.position = (x, y)
                            mouse.press(button)
                        else:
                            mouse.position = (x, y)
                            mouse.release(button)
                    except ValueError:
                        continue
    except KeyboardInterrupt:
        pass

    Mouse_Coruse_Client_Socket.close()
    Mouse_Coruse_Server_Socket.close()


# Keyboard and mouse as background threads
Thread(target=HostKeyboard, daemon=True).start()
Thread(target=HostMouseCourseControlling, daemon=True).start()

# Screen capture in main thread
HostScreenCapturing()
