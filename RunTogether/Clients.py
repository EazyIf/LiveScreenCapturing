import sys
import socket
import cv2
import numpy as np
import pyautogui
import ray
import struct
from pynput import keyboard

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    import pyWinhook
    import pythoncom

ray.init()

@ray.remote
def ClientKeyboard():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    IP = '192.168.1.120'
    PORT = 1223
    client_socket.connect((IP, PORT))

    def OnPress(key):   
        prr = f'press.{key}'
        if client_socket:
            client_socket.send(prr.encode())
        
    def OnRelease(key):
        rls = f'release.{key}'
        if client_socket:
            if 'Key' not in rls:
                pass
            else:
                client_socket.send(rls.encode())

    def OnKeyboardEvent(event):
        return False

    def RunClient():
        if IS_WINDOWS:
            hook_manager = pyWinhook.HookManager()
            hook_manager.KeyDown = OnKeyboardEvent
            hook_manager.HookKeyboard()

        listener = keyboard.Listener(on_press=OnPress,on_release=OnRelease)
        listener.start()

        if IS_WINDOWS:
            try:
                pythoncom.PumpMessages()
            except KeyboardInterrupt:
                pass
            hook_manager.UnhookKeyboard()
        else:
            try:
                listener.join()
            except KeyboardInterrupt:
                pass

        client_socket.close()

    try:
        RunClient()
    except Exception as e:
        print(f"An error occurred: {str(e)}")

@ray.remote
def ClientScreenCapturing():
    HOST_IP = '192.168.1.120'  # Paste your server IP address here
    BUFFER_SIZE = 65535

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)

    sock.sendto(b"hello", (HOST_IP, 9999))
    print(f"Screen capture (UDP) connecting to {HOST_IP}:9999...")

    dim_data, _ = sock.recvfrom(1024)
    width, height = struct.unpack("!HH", dim_data)
    print(f"Host screen: {width}x{height}")

    sock.settimeout(5.0)

    frames = {}
    last_displayed_seq = -1

    while True:
        try:
            packet, _ = sock.recvfrom(BUFFER_SIZE)
        except socket.timeout:
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
            frame_data = b"".join(frames[frame_seq][i] for i in range(total_chunks))
            frame = cv2.imdecode(
                np.frombuffer(frame_data, dtype=np.uint8),
                cv2.IMREAD_COLOR,
            )

            if frame is not None:
                cv2.namedWindow("RECEIVING VIDEO", cv2.WINDOW_NORMAL)
                cv2.setWindowProperty("RECEIVING VIDEO", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
                cv2.imshow("RECEIVING VIDEO", frame)

            last_displayed_seq = frame_seq
            frames = {k: v for k, v in frames.items() if k > frame_seq}

        if cv2.waitKey(1) == ord("q"):
            break

    cv2.destroyAllWindows()
    sock.close()
    
@ray.remote
def ClientMouseCourseControlling():
    from pynput.mouse import Controller, Listener
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('192.168.1.120', 9922)
    client_socket.connect(server_address)
    
    screen_width, screen_height = pyautogui.size()
    middle_x = screen_width // 2
    middle_y = screen_height // 2
    mouse = Controller()
    mouse.position = (middle_x, middle_y)
    
    def send_event(event):
        client_socket.send(event.encode())
    
    def on_mouse_event(x, y, button, pressed):
        if pressed:
            event = f"PRESS {button} {x} {y}"
            send_event(event)
        else:
            event = f"RELEASE {button} {x} {y}"
            send_event(event)
    listener = Listener(on_click=on_mouse_event)
    listener.start()
    prev_x, prev_y = mouse.position
    
    try:
        while True:
            x, y = mouse.position
    
            if x != prev_x or y != prev_y:
                event = f"MOVE {x} {y}"
                send_event(event)
                prev_x, prev_y = x, y
    except KeyboardInterrupt:
        listener.stop()
    
    client_socket.close()

ray.get([ClientKeyboard.remote(), ClientScreenCapturing.remote(), ClientMouseCourseControlling.remote()])
