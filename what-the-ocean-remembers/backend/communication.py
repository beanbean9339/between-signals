
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient

LOCAL_HOST = "127.0.0.1"

ENV_A_PORT = 7001
ENV_B_PORT = 7002
BACKEND_PORT = 8000

environment_a = SimpleUDPClient(LOCAL_HOST, ENV_A_PORT)
environment_b = SimpleUDPClient(LOCAL_HOST, ENV_B_PORT)


def get_target(source):
    if source == "A":
        return environment_b
    elif source == "B":
        return environment_a

    print(f"Unknown source: {source}")
    return None




def handle_text(address, destination, message):
    print(f"[TEXT] Destination {destination}: {message}")

    if destination == "A":
        environment_a.send_message("/ocean/text", str(message))

    elif destination == "B":
        environment_b.send_message("/ocean/text", str(message))

    else:
        print(f"Unknown destination: {destination}")




def handle_movement(address, source, x, y, intensity):
    print(f"[MOVEMENT] {source}: {x}, {y}, {intensity}")

    target = get_target(source)

    if target:
        target.send_message(
            "/ocean/movement",
            [float(x), float(y), float(intensity)]
        )


def handle_object(address, source, object_name):
    print(f"[OBJECT] {source}: {object_name}")

    target = get_target(source)

    if target:
        target.send_message("/ocean/object", str(object_name))


def handle_audio(address, source, level):
    print(f"[AUDIO] {source}: {level}")

    target = get_target(source)

    if target:
        target.send_message("/ocean/audio_level", float(level))


def start_server():
    dispatcher = Dispatcher()

    dispatcher.map("/input/text", handle_text)
    dispatcher.map("/input/movement", handle_movement)
    dispatcher.map("/input/object", handle_object)
    dispatcher.map("/input/audio", handle_audio)

    server = ThreadingOSCUDPServer(
        (LOCAL_HOST, BACKEND_PORT),
        dispatcher
    )

    print(f"Backend listening on {BACKEND_PORT}")
    server.serve_forever()
