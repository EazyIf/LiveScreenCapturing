import socket
import cv2
from mss import mss
from PIL import Image
import numpy as np
import pyautogui
import ray
import zlib
import pyWinhook
import pythoncom
from pynput import keyboard

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
        hook_manager = pyWinhook.HookManager()
        hook_manager.KeyDown = OnKeyboardEvent
        hook_manager.HookKeyboard()
        listener = keyboard.Listener(on_press=OnPress,on_release=OnRelease)
        listener.start()

        try:
            pythoncom.PumpMessages()
        except KeyboardInterrupt:
            pass

        hook_manager.UnhookKeyboard()
        client_socket.close()

    if __name__ == "__main__":
        try:
            RunClient()
        except Exception as e:
            print(f"An error occurred: {str(e)}")

@ray.remote
def ClientScreenCapturing():

    ClientScreenCapturingSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    HostScreenCapturingIP = '192.168.1.120' # Paste your server IP address here
    HostScreenCapturingPORT = 9999

    ClientScreenCapturingSocket.connect((HostScreenCapturingIP, HostScreenCapturingPORT))
    screen_width, screen_height = pyautogui.size()
    frame_size = (screen_width, screen_height)
    frame_size = 0
    frame_data = b""

    while True:
        size_data = ClientScreenCapturingSocket.recv(4)
        if not size_data:
            break
        frame_size = int.from_bytes(size_data, 'big')

        while len(frame_data) < frame_size:
            data = ClientScreenCapturingSocket.recv(frame_size - len(frame_data))
            if not data:
                break
            frame_data += data

        decompressed_frame = zlib.decompress(frame_data)
        frame = np.frombuffer(decompressed_frame, dtype=np.uint8).reshape((screen_height, screen_width, 3))
        cv2.namedWindow("RECEIVING VIDEO", cv2.WINDOW_NORMAL)
        cv2.setWindowProperty("RECEIVING VIDEO", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        cv2.imshow("RECEIVING VIDEO", frame)
        frame_data = b""
        if cv2.waitKey(1) == 35:
            break

    cv2.destroyAllWindows()
    ClientScreenCapturingSocket.close()
    
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
