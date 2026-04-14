import sys
import socket
from pynput import keyboard

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    import pyWinhook
    import pythoncom

class Client:
    def __init__(self):
        self.IP = '192.168.1.120'
        self.PORT = 1223
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def OnPress(self, key):
        prr = f'press.{key}'
        if self.client_socket:
            self.client_socket.send(prr.encode())

    def OnRelease(self,key):
        rls = f'release.{key}'
        if self.client_socket:
            if 'Key' not in rls:
                pass
            else:
                self.client_socket.send(rls.encode())

    def OnKeyboardEvent(self, event):
        return False

    def RunClient(self):
        if IS_WINDOWS:
            hook_manager = pyWinhook.HookManager()
            hook_manager.KeyDown = self.OnKeyboardEvent
            hook_manager.HookKeyboard()

        listener = keyboard.Listener(on_press=self.OnPress,on_release=self.OnRelease)
        listener.start()
        self.client_socket.connect((self.IP, self.PORT))

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

        self.client_socket.close()

if __name__ == "__main__":
    try:
        client = Client()
        client.RunClient()
    except Exception as e:
        print(f"An error occurred: {str(e)}")
