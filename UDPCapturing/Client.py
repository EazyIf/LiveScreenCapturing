import socket
import cv2
import numpy as np
import struct

# ── Configuration ──────────────────────────────────────────────────
HOST_IP = "192.168.50.13"   # Paste your server IP address here
UDP_PORT = 9999
BUFFER_SIZE = 65535          # Max UDP datagram size
# ───────────────────────────────────────────────────────────────────

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Increase receive buffer to reduce packet drops on burst traffic
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)

    # Register with host
    sock.sendto(b"hello", (HOST_IP, UDP_PORT))
    print(f"Connecting to {HOST_IP}:{UDP_PORT}...")

    # Receive screen dimensions from host
    dim_data, _ = sock.recvfrom(1024)
    width, height = struct.unpack("!HH", dim_data)
    print(f"Host screen: {width}x{height}")

    # Timeout so the client doesn't hang forever if the host dies
    sock.settimeout(5.0)

    frames = {}               # {frame_seq: {chunk_idx: data}}
    chunk_counts = {}          # {frame_seq: total_chunks}
    last_displayed_seq = -1

    while True:
        try:
            packet, _ = sock.recvfrom(BUFFER_SIZE)
        except socket.timeout:
            print("No data received for 5s – host may have disconnected.")
            continue
        except socket.error:
            continue

        if len(packet) < 8:
            continue

        # Parse header
        frame_seq, chunk_idx, total_chunks = struct.unpack("!IHH", packet[:8])
        chunk_data = packet[8:]

        # Drop frames older than the last one we displayed
        if frame_seq <= last_displayed_seq:
            continue

        # Store chunk
        if frame_seq not in frames:
            frames[frame_seq] = {}
            chunk_counts[frame_seq] = total_chunks
        frames[frame_seq][chunk_idx] = chunk_data

        # Check if frame is complete
        if len(frames[frame_seq]) == total_chunks:
            # Reassemble in order
            frame_data = b"".join(frames[frame_seq][i] for i in range(total_chunks))

            # Decode JPEG (dimensions are embedded in the JPEG data)
            frame = cv2.imdecode(
                np.frombuffer(frame_data, dtype=np.uint8),
                cv2.IMREAD_COLOR,
            )

            if frame is not None:
                cv2.namedWindow("RECEIVING VIDEO", cv2.WINDOW_NORMAL)
                cv2.setWindowProperty(
                    "RECEIVING VIDEO",
                    cv2.WND_PROP_FULLSCREEN,
                    cv2.WINDOW_FULLSCREEN,
                )
                cv2.imshow("RECEIVING VIDEO", frame)

            last_displayed_seq = frame_seq

            # Discard all frames up to and including the one we just showed
            frames = {k: v for k, v in frames.items() if k > frame_seq}
            chunk_counts = {k: v for k, v in chunk_counts.items() if k > frame_seq}

        if cv2.waitKey(1) == ord("q"):
            break

    cv2.destroyAllWindows()
    sock.close()


if __name__ == "__main__":
    main()
