
import sounddevice as sd
import numpy as np
from scipy.signal import resample_poly
from faster_whisper import WhisperModel
import queue

DEVICE = 1
SAMPLE_RATE = 44100
WHISPER_RATE = 16000

PROCESS_SECONDS = 4
BLOCK_SIZE = SAMPLE_RATE  # Capture in 1-second blocks

audio_queue = queue.Queue()

print("Loading Whisper model...")
model = WhisperModel("base", device="cpu", compute_type="int8")
print("Whisper ready!")

def audio_callback(indata, frames, time, status):
    if status:
        print("Audio status:", status)

    audio_queue.put(indata.copy())


print("\nListening continuously. Speak clearly!")

try:
    audio_buffer = []

    with sd.InputStream(
        device=DEVICE,
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        blocksize=BLOCK_SIZE,
        callback=audio_callback
    ):

        while True:
            chunk = audio_queue.get()
            audio_buffer.append(chunk.flatten())

            if len(audio_buffer) >= PROCESS_SECONDS:
                audio = np.concatenate(audio_buffer)
                audio_buffer = []

                print("\nProcessing audio...")

                peak = np.max(np.abs(audio))
                print(f"Microphone level: {peak:.4f}")

                audio = resample_poly(
                    audio, 160, 441
                ).astype(np.float32)

                segments, info = model.transcribe(
                    audio,
                    beam_size=1,
                    vad_filter=False
                )

                text = " ".join(
                    segment.text.strip() for segment in segments
                ).strip()

                if text:
                    print("TRANSCRIPT:", text)
                else:
                    print("No speech recognized.")

except KeyboardInterrupt:
    print("\nStopped listening.")
