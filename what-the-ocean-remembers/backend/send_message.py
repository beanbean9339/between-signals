"""
Simple tool to send messages between Environment A and Environment B

Usage:
    python send_message.py A "Your message here"
    python send_message.py B "Another message"
"""

import sys
from pythonosc.udp_client import SimpleUDPClient

LOCAL_HOST = "127.0.0.1"
ENV_A_PORT = 7001
ENV_B_PORT = 7002

environment_a = SimpleUDPClient(LOCAL_HOST, ENV_A_PORT)
environment_b = SimpleUDPClient(LOCAL_HOST, ENV_B_PORT)


def send_message(source_env, message):
    """Send a message from one environment to the other"""
    
    if source_env.upper() == "A":
        print(f"[A → B] Sending: {message}")
        environment_b.send_message("/ocean/text", message)
    elif source_env.upper() == "B":
        print(f"[B → A] Sending: {message}")
        environment_a.send_message("/ocean/text", message)
    else:
        print("Error: Source must be 'A' or 'B'")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python send_message.py <A|B> <message>")
        print("Example: python send_message.py A 'Hello from Environment A'")
        sys.exit(1)
    
    source = sys.argv[1]
    message = " ".join(sys.argv[2:])
    
    send_message(source, message)
