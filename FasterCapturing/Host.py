import socket
import cv2
import numpy as np
import pyautogui
import zlib

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host_name = socket.gethostname()
host_ip = socket.gethostbyname(host_name)
print('HOST IP:', host_ip)
port = 9999
socket_address = (host_ip, port)
server_socket.bind(socket_address)
server_socket.listen(5)
print("LISTENING AT:", socket_address)

client_socket, addr = server_socket.accept()
print('GOT CONNECTION FROM:', addr)

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
    client_socket.sendall(frame_size.to_bytes(4, 'big') + compressed_frame)
    if cv2.waitKey(1) == ord('q'):
        break

out.release()
cv2.destroyAllWindows()
client_socket.close()
server_socket.close()
