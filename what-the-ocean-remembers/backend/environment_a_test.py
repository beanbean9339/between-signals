from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer

def receive_message(address, *args):
    print(f"[ENVIRONMENT A] {address}: {args}")

dispatcher = Dispatcher()
dispatcher.set_default_handler(receive_message)

server = ThreadingOSCUDPServer(
    ("127.0.0.1", 7001),
    dispatcher
)

print("Environment A listening on port 7001...")
server.serve_forever()