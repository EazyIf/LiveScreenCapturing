import socket
import cv2
import numpy as np
import pyautogui
import zlib

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host_ip = '192.168.1.126'  # Paste your server IP address here
port = 9999
client_socket.connect((host_ip, port))

screen_width, screen_height = pyautogui.size()
frame_size = (screen_width, screen_height)
frame_size = 0
frame_data = b""

while True:
    size_data = client_socket.recv(4)
    if not size_data:
        break
    frame_size = int.from_bytes(size_data, 'big')

    while len(frame_data) < frame_size:
        data = client_socket.recv(frame_size - len(frame_data))
        if not data:
            break
        frame_data += data

    decompressed_frame = zlib.decompress(frame_data)
    frame = np.frombuffer(decompressed_frame, dtype=np.uint8).reshape((screen_height, screen_width, 3))
    cv2.namedWindow("RECEIVING VIDEO", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("RECEIVING VIDEO", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    cv2.imshow("RECEIVING VIDEO", frame)
    frame_data = b""
    if cv2.waitKey(1) == ord('q'):
        break

cv2.destroyAllWindows()
client_socket.close()
