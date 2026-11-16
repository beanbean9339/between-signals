"""
Simple OSC Backend Server - Routes messages between Environment A and B

Run this to enable the routing system:
    python backend_server.py

Then use send_message.py to send messages between environments.
"""

from communication import start_server

if __name__ == "__main__":
    print("Starting OSC Backend Server...")
    print("Listening on port 8000")
    print("\nUse send_message.py to send messages:")
    print("  python send_message.py A 'Message to Environment B'")
    print("  python send_message.py B 'Message to Environment A'")
    print("\nPress Ctrl+C to stop.\n")
    
    start_server()
