from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer

def receive_message(address, *args):
    print(f"[ENVIRONMENT B] {address}: {args}")

dispatcher = Dispatcher()
dispatcher.set_default_handler(receive_message)

server = ThreadingOSCUDPServer(
    ("127.0.0.1", 7002),
    dispatcher
)

print("Environment B listening on port 7002...")
server.serve_forever()