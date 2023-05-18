import socket
import cv2
import numpy as np
from mss import mss
import socket
import pyautogui
from threading import Thread
import ray
import zlib

ray.init()

host_name  = socket.gethostname()
host_ip = socket.gethostbyname(host_name)
print(f"[*] Listening as {host_ip} : 1223,|:|, 9999|:|, 9922")

@ray.remote
def HostKeyboard():
    from pynput.keyboard import Key, Controller
    import keyboard

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

@ray.remote
def HostScreenCapturing():
    HostScreenCapturingSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    HostScreenCapturingPort = 9999

    socket_address = (host_ip,HostScreenCapturingPort)
    HostScreenCapturingSocket.bind(socket_address)
    HostScreenCapturingSocket.listen(5)

    ClientScreenCapturingSocket, ClientScreenCapturingAddr = HostScreenCapturingSocket.accept()
    print('GOT CONNECTION FROM:', ClientScreenCapturingAddr)

    screen_width, screen_height = pyautogui.size()
    frame_size = (screen_width, screen_height)
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('output.mp4', fourcc, 15.0, frame_size)
    
    while True:
        img = pyautogui.screenshot()
        frame = np.array(img)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
        out.write(frame)
    
        encoded_frame = frame.tobytes()
        compressed_frame = zlib.compress(encoded_frame)
    
        frame_size = len(compressed_frame)
        ClientScreenCapturingSocket.sendall(frame_size.to_bytes(4, 'big') + compressed_frame)
        if cv2.waitKey(1) == ord('q'):
            break
        
    out.release()
    cv2.destroyAllWindows()
    ClientScreenCapturingSocket.close()
    ClientScreenCapturingSocket.close()

@ray.remote
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

ray.get([HostKeyboard.remote(), HostScreenCapturing.remote(), HostMouseCourseControlling.remote()])
