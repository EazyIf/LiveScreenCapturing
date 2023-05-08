import socket
import cv2
import numpy as np
import pyautogui

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host_ip = '192.168.1.120' # Paste your server IP address here
port = 9999
server_socket.bind((host_ip, port))
server_socket.listen(5)
print("LISTENING AT:", (host_ip, port))

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
    frame_size = len(encoded_frame)
    client_socket.sendall(frame_size.to_bytes(4, 'big') + encoded_frame)
    if cv2.waitKey(1) == ord('q'):
        break

out.release()
cv2.destroyAllWindows()
client_socket.close()
server_socket.close()