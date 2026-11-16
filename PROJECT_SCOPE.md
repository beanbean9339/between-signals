
# BETWEEN SIGNALS
## Project Scope & Technical Requirements

**Project Type:** Interactive, Distributed Installation  
**Project Name:** Between Signals  
**Environments:** Environment A (Grass) and Environment B (Dirt)  
**Development Platform:** TouchDesigner, Python, WebSockets  
**Repository:** `between-signals`

---

# 1. Project Overview

Between Signals is an interactive installation consisting of two physically separate environments that communicate with one another through visitor movement and speech.

Each environment exists in its own physical room and has its own visual identity, sensors, computer, and interactive simulation.

- **Environment A:** A grass-based environment.
- **Environment B:** A dirt-based environment.

Although the environments are physically separated, they are digitally connected.

Visitors in Environment A influence the visual experience in Environment B through their movement and speech. Visitors in Environment B similarly influence Environment A.

The installation explores the relationship between physical presence, communication, distance, and interconnectedness. Visitors may not directly see or hear the people in the other room, but their presence leaves an impression on the environment.

The two environments should feel independent, yet connected through an invisible exchange of information.

## Core Concept

Two separate environments. Two groups of visitors. One shared system of communication.

Movement and language become signals that travel between spaces and influence how the other environment behaves.

---

# 2. Experience Goals

The installation should:

1. Create two distinct but interconnected interactive environments.
2. Allow visitors to influence the opposite environment through their physical movement.
3. Allow visitors' spoken words to travel between environments and appear visually.
4. Make interactions feel responsive, organic, and connected rather than like a conventional messaging application.
5. Preserve the individuality of each environment. The grass and dirt environments should interpret incoming signals in ways that make sense for their own visual identity.
6. Operate continuously without requiring visitors to understand the underlying technology.

## Desired Visitor Experience

A visitor enters Environment A.

Their movement is detected by the local depth sensor. Their movement is processed into structured information and sent to Environment B.

The grass environment responds to the presence and movement of the visitor in Environment B.

If the visitor speaks, their words are transcribed and sent to Environment B, where the text becomes part of the visual experience.

At the same time, visitors in Environment B are creating signals that travel back to Environment A.

The interaction should feel like the two environments are responding to one another.

---

# 3. Physical Installation

## Environment A: Grass

**Physical setup:**
- One computer running TouchDesigner.
- One depth sensor or depth camera.
- One microphone.
- Display or projection system.
- Grass-based visual simulation.

**Responsibilities:**
- Detect local visitor movement.
- Capture local speech.
- Process movement and speech into structured events.
- Send events to Environment B.
- Receive incoming events from Environment B.
- Interpret incoming events through the grass simulation.

## Environment B: Dirt

**Physical setup:**
- One computer running TouchDesigner.
- One depth sensor or depth camera.
- One microphone.
- Display or projection system.
- Dirt-based visual simulation.

**Responsibilities:**
- Detect local visitor movement.
- Capture local speech.
- Process movement and speech into structured events.
- Send events to Environment A.
- Receive incoming events from Environment A.
- Interpret incoming events through the dirt simulation.

The two computers may be connected to entirely different internet networks. They must not depend on being connected to the same local Wi-Fi network.

---

# 4. Technical Architecture

The system consists of three main layers:

1. Local input and processing.
2. Cloud-based communication.
3. Local visual output through TouchDesigner.

## 4.1 Overall Architecture

Environment A and Environment B each run an independent local application.

Each local application communicates with a shared cloud relay.

The cloud relay routes information between the two environments.

```text
              ENVIRONMENT A
       ┌──────────────────────────┐
       │                          │
       │  Depth Sensor            │
       │  Microphone              │
       │       ↓                  │
       │  Local Processing        │
       │  Movement Detection      │
       │  Speech Transcription    │
       │       ↓                  │
       │  Python Application      │
       │       ↓                  │
       │  TouchDesigner           │
       │       ↑                  │
       └───────┼──────────────────┘
               │
               │ Internet
               ↓
       ┌──────────────────────────┐
       │                          │
       │     CLOUD RELAY          │
       │                          │
       │  Event Routing           │
       │  Room Identification     │
       │  Message Delivery        │
       │                          │
       └──────────┬───────────────┘
                  │
                  │ Internet
                  ↓
              ENVIRONMENT B
       ┌──────────────────────────┐
       │                          │
       │  Python Application      │
       │       ↓                  │
       │  TouchDesigner           │
       │       ↑                  │
       │  Local Processing        │
       │  Movement Detection      │
       │  Speech Transcription    │
       │       ↑                  │
       │  Depth Sensor            │
       │  Microphone              │
       │                          │
       └──────────────────────────┘
```

## 4.2 Local Processing

Each environment processes its own sensor information locally.

The system should not continuously stream raw camera footage, depth maps, or microphone recordings over the internet.

Instead, each computer extracts meaningful information and sends lightweight structured events.

This reduces network usage, improves responsiveness, and avoids unnecessary transmission of raw visitor data.

## 4.3 Cloud Communication

Use a cloud-based communication relay to connect the two computers.

**Preferred starting approach:** Python WebSocket server with secure WebSocket connections (WSS) for production deployment.

The relay should:
- Accept connections from both environments.
- Identify which environment each connection represents.
- Route Environment A events exclusively to Environment B.
- Route Environment B events exclusively to Environment A.
- Support bidirectional communication.
- Handle disconnections and automatic reconnection.
- Avoid sending an event back to its originating environment.
- Support structured JSON event messages.

The communication layer should be independent of TouchDesigner so it can be tested separately.

---

# 5. Movement Detection

Each environment has its own depth sensor.

The sensor detects visitor movement within the physical space.

Movement information is processed locally and sent to the opposite environment.

## Required Movement Information

The initial implementation should support:

- Visitor presence.
- Visitor entering or leaving the interaction area.
- Normalized X and Y position.
- Movement direction.
- Movement speed or velocity.
- Movement intensity.
- Timestamp.
- Source environment.

If the selected sensor and tracking system support it, the system may also include a temporary visitor or tracking ID.

## Movement Event Example

```json
{
  "event_id": "unique-event-id",
  "type": "movement",
  "source": "A",
  "timestamp": 1794850000,
  "data": {
    "present": true,
    "position": {
      "x": 0.45,
      "y": 0.62
    },
    "velocity": 0.35,
    "direction": "right",
    "intensity": 0.7
  }
}
```

Values for position and intensity should be normalized where possible.

The receiving environment should be able to interpret this information without knowing the exact hardware or sensor used by the sending environment.

## Movement Requirements

- Movement should update continuously or at a controlled frequency.
- Prioritize the most recent movement information.
- Discard stale movement updates instead of building up a queue.
- Smooth incoming movement data to prevent abrupt visual changes.
- Avoid transmitting unnecessary sensor data.
- Support multiple visitors where the selected hardware and tracking implementation allow it.

---

# 6. Speech Detection and Transcription

Each environment has a local microphone.

Speech should be captured and transcribed locally before being sent to the opposite environment.

## Processing Flow

1. Capture speech from the local microphone.
2. Detect speech activity.
3. Process the audio using speech-to-text.
4. Generate a text transcription.
5. Package the transcription as a structured event.
6. Send the event to the opposite environment.
7. Display or otherwise interpret the incoming words in TouchDesigner.

## Speech-to-Text

Use Whisper or a suitable local Whisper implementation as the initial transcription approach.

The preferred goal is local transcription rather than sending raw audio to an external cloud transcription service.

The implementation should:
- Support microphone input.
- Detect speech segments.
- Avoid sending silence.
- Produce readable text.
- Attach a timestamp and source environment.
- Handle transcription failures gracefully.

## Speech Event Example

```json
{
  "event_id": "unique-event-id",
  "type": "speech",
  "source": "A",
  "timestamp": 1794850000,
  "data": {
    "text": "I wonder what is growing over there.",
    "language": "en"
  }
}
```

## Speech Visualization

Incoming speech should be passed to TouchDesigner as text.

The visualization should feel integrated into the environment rather than appearing as a conventional chat interface.

Potential visual treatments include:
- Words appearing and fading.
- Text emerging from the ground or surrounding environment.
- Words influencing the movement or behavior of visual elements.
- Text appearing at positions influenced by incoming movement data.

The exact visual treatment will be developed artistically within TouchDesigner.

The initial implementation does not need AI-generated responses or semantic analysis of speech.

---

# 7. Event Communication Protocol

All information exchanged between environments must follow a shared event structure.

This allows the communication system to remain consistent even if the sensors, visualizations, or processing methods change.

## Supported Event Types

| Event | Description |
|---|---|
| `movement` | Visitor position and movement information |
| `presence` | Visitor presence, entry, or exit |
| `speech` | Transcribed speech |
| `object_detection` | Optional future object detection events |

## General Event Structure

```json
{
  "event_id": "unique-event-id",
  "type": "movement",
  "source": "A",
  "timestamp": 1794850000,
  "data": {}
}
```

Every event should include:
- Unique event ID.
- Event type.
- Source environment.
- Timestamp.
- Event-specific data.

The receiving environment should validate incoming messages before processing them.

Speech events should be handled as discrete messages. Movement events should prioritize freshness and smoothness.

The system should prevent duplicate speech messages and avoid forwarding remotely received events back to the originating room.

---

# 8. TouchDesigner Integration

TouchDesigner is responsible for the visual experience.

Python handles sensor processing, communication, and the connection between local hardware and the cloud relay.

The preferred integration approach is:

**Local Python application → OSC → TouchDesigner**

OSC allows the Python application to send structured information to TouchDesigner over the local computer.

## TouchDesigner Responsibilities

- Receive incoming movement information.
- Receive incoming speech transcriptions.
- Distinguish local and remote events when needed.
- Update visual parameters.
- Trigger visual responses.
- Control the grass or dirt simulation.
- Handle incoming events without interrupting the visual experience.

## Environment-Specific Behavior

The two environments should share a communication protocol but should not be required to share identical visual behavior.

For example:
- Environment A may interpret movement through the behavior of grass, bending, growth, or disturbance.
- Environment B may interpret movement through the behavior of soil, particles, displacement, or other dirt-based visual elements.

These are artistic possibilities, not fixed implementation requirements.

The communication system should provide the data. Each TouchDesigner environment should decide how to interpret it.

---

# 9. Development and Simulation Mode

A major development requirement is that the entire system must be testable using one computer before deploying to two separate physical computers.

The project must support two operating modes.

## Mode 1: Simulation

Used during development.

One computer runs two independent room instances:

- Room A simulates the grass environment.
- Room B simulates the dirt environment.

Each instance should have:
- Its own room configuration.
- Its own application process.
- Its own communication connection.
- Its own simulated movement input.
- Its own simulated speech input.
- Its own TouchDesigner destination.

Simulated inputs should use exactly the same event structures as real sensor inputs.

The simulation must demonstrate that:
- Movement from A reaches B.
- Movement from B reaches A.
- Speech from A reaches B.
- Speech from B reaches A.
- Events are not accidentally echoed to their originating room.
- Each environment can receive and process multiple event types.

Simulated input should be easy to trigger through a command-line interface or simple development controls.

## Mode 2: Production

Used during the physical installation.

Each computer runs one room instance.

For example:

**Computer A**
- Room A configuration.
- Grass environment.
- Real depth sensor.
- Real microphone.
- Local speech transcription.
- Cloud communication client.
- TouchDesigner.

**Computer B**
- Room B configuration.
- Dirt environment.
- Real depth sensor.
- Real microphone.
- Local speech transcription.
- Cloud communication client.
- TouchDesigner.

The same communication protocol and core application logic should work in both modes.

Only the input source and room configuration should change.

---

# 10. Configuration and Room Separation

Each room should be configurable independently.

Use configuration files instead of hardcoding room-specific values throughout the application.

Example:

`config/room_a.json`

```json
{
  "room_id": "A",
  "environment": "grass",
  "mode": "simulation",
  "osc": {
    "host": "127.0.0.1",
    "port": 7001
  }
}
```

`config/room_b.json`

```json
{
  "room_id": "B",
  "environment": "dirt",
  "mode": "simulation",
  "osc": {
    "host": "127.0.0.1",
    "port": 7002
  }
}
```

Configuration should eventually include:
- Room identity.
- Environment type.
- Simulation or production mode.
- Local OSC settings.
- Cloud relay URL.
- Sensor configuration.
- Microphone configuration.
- Transcription settings.

Do not hardcode private credentials or production connection secrets into the repository.

The two environments may use one shared TouchDesigner project template with different configuration, or separate TouchDesigner files if their visual systems require it. This should not affect the shared communication architecture.

---

# 11. Reliability and Performance

The installation should operate continuously during exhibition hours.

## Required Behavior

- Automatically reconnect to the cloud relay after a connection is lost.
- Continue running the local visual simulation if internet connectivity is interrupted.
- Avoid crashing if a microphone or depth sensor disconnects.
- Handle invalid or incomplete incoming events.
- Prevent duplicate speech messages.
- Avoid processing outdated movement events.
- Log important errors and connection changes.
- Provide a clear indication of whether each room is connected.

## Performance Priorities

1. Low-latency movement communication.
2. Reliable speech delivery.
3. Smooth visual transitions.
4. Stable long-running operation.
5. Efficient CPU and memory usage.

Movement data should be sent at a controlled rate based on testing. It does not need to transmit every raw sensor frame.

Speech can be sent when a transcription segment is complete.

The system should be tested under realistic network conditions before exhibition deployment.

---

# 12. Privacy Considerations

- Process depth information locally.
- Process microphone audio locally when possible.
- Send structured movement information rather than raw camera footage.
- Send transcribed speech rather than raw audio.
- Do not permanently store visitor speech by default.
- Avoid collecting personally identifiable visitor information.
- Use secure connections for production communication.
- Keep credentials and API keys out of GitHub.

Any additional recording or storage should be an intentional project decision.

---

# 13. Proposed Repository Structure

The codebase should be organized into independent modules.

```text
between-signals/
│
├── touchdesigner/
│   ├── environment.toe
│   └── README.md
│
├── backend/
│   ├── sensors/
│   │   ├── depth_camera.py
│   │   ├── movement.py
│   │   └── simulated_sensor.py
│   │
│   ├── speech/
│   │   ├── microphone.py
│   │   ├── transcription.py
│   │   └── simulated_speech.py
│   │
│   ├── communication/
│   │   ├── cloud_server.py
│   │   ├── cloud_client.py
│   │   ├── local_bridge.py
│   │   └── event_router.py
│   │
│   ├── visualization/
│   │   └── osc_output.py
│   │
│   └── main.py
│
├── config/
│   ├── room_a.json
│   └── room_b.json
│
├── tests/
│
├── models/
│   └── README.md
│
├── docs/
│   ├── architecture.md
│   ├── event_protocol.md
│   └── deployment.md
│
├── PROJECT_SCOPE.md
├── README.md
├── requirements.txt
├── .env.example
└── .gitignore
```

This is a proposed structure, not an instruction to recreate existing files.

Before adding new modules, inspect the existing repository and reuse or refactor existing code where appropriate.

---

# 14. Development Roadmap

Development should happen incrementally. Each phase must be tested before moving to the next.

## Phase 1: Repository and Foundation

- Inspect existing project files and code.
- Establish the repository structure.
- Create room configurations.
- Define shared event schemas.
- Separate configuration from application logic.
- Document the architecture.

**Deliverable:** A clean project foundation with a documented event protocol.

## Phase 2: Local Simulation

- Create two independent room instances.
- Simulate movement events.
- Simulate speech events.
- Implement event routing.
- Verify bidirectional communication.
- Verify that events only reach the opposite environment.

**Deliverable:** Two simulated environments communicating on one computer.

## Phase 3: Cloud Communication

- Implement a cloud relay.
- Connect both room instances to the relay.
- Support different internet networks.
- Implement reconnection behavior.
- Test message delivery and event routing.

**Deliverable:** Two computers can exchange events over the internet.

## Phase 4: Real Sensor Integration

- Integrate the selected depth sensor.
- Implement movement detection.
- Integrate microphone input.
- Implement local speech transcription.
- Convert real sensor inputs into the shared event protocol.

**Deliverable:** Real movement and speech data can be exchanged between environments.

## Phase 5: TouchDesigner Integration

- Connect the Python application to TouchDesigner through OSC.
- Receive movement and speech events.
- Map incoming information to visual parameters.
- Implement environment-specific reactions.
- Test both environments independently and together.

**Deliverable:** Both environments respond visually to signals from the opposite room.

## Phase 6: Deployment and Installation Testing

- Configure each physical computer.
- Install dependencies.
- Configure sensors and microphones.
- Connect each room to the cloud relay.
- Test across separate networks.
- Test extended runtime.
- Optimize performance.
- Prepare startup and recovery instructions.

**Deliverable:** A stable, fully operational two-room installation.

---

# 15. Initial Scope Boundaries

The first working version should prioritize the core interaction.

## Required for Initial Version

- Two independent environments.
- Bidirectional communication.
- Movement detection.
- Speech-to-text transcription.
- Structured event protocol.
- Cloud-based communication.
- TouchDesigner integration.
- One-computer simulation mode.
- Two-computer production mode.

## Future Possibilities

These features are not required for the first working version:

- Object detection.
- More sophisticated visitor tracking.
- Semantic analysis of speech.
- AI-generated responses.
- Persistent interaction histories.
- More complex environmental memory.
- Additional types of sensor input.
- More elaborate relationships between movement and visual behavior.

These can be explored after the core system is reliable.

---

# 16. Definition of Success

Between Signals is technically successful when:

1. Two computers can run independent environments.
2. The computers can communicate over separate internet networks.
3. Movement in Environment A influences Environment B.
4. Movement in Environment B influences Environment A.
5. Speech in Environment A appears in Environment B.
6. Speech in Environment B appears in Environment A.
7. The two environments interpret incoming information independently.
8. Communication continues reliably throughout the installation.
9. Local simulations continue operating during temporary network interruptions.
10. The entire system can be tested and demonstrated before physical deployment.

Artistically, the installation should make visitors feel that their presence and actions have an effect beyond the space they occupy.

The two environments should feel separate, but not isolated.

**Between Signals is about what happens between two places when information, movement, and language travel from one to the other.**