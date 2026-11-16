
from pythonosc.udp_client import SimpleUDPClient

client = SimpleUDPClient("127.0.0.1", 8000)

# Send text from Environment A to B
client.send_message(
    "/input/text",
    ["A", "Hello from the other ocean"]
)

# Send movement from Environment A to B
client.send_message(
    "/input/movement",
    ["A", 0.5, 0.8, 0.9]
)

# Send an object request from Environment A to B
client.send_message(
    "/input/object",
    ["A", "glass_flower"]
)

# Send audio intensity from Environment A to B
client.send_message(
    "/input/audio",
    ["A", 0.75]
)

print("Test messages sent!")
