import asyncio
import ssl
import websockets
import sounddevice as sd

# Note the 'wss://' scheme instead of 'ws://'
SERVER_URI = "wss://localhost:8765"
API_KEY = "my-secret-api-key-123"

SAMPLERATE = 44100
CHANNELS = 1
BLOCKSIZE = 1024  # Frame size per chunk (smaller = lower latency)


async def stream_audio():
    # Configure SSL context for client connection
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    # Note: Set check_hostname=True and verify_mode=ssl.CERT_REQUIRED in production with real certificates!
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE  # For self-signed testing certificates

    # Include the API key in the connection headers
    extra_headers = {"X-API-Key": API_KEY}

    async with websockets.connect(
        SERVER_URI, ssl=ssl_context, extra_headers=extra_headers
    ) as websocket:
        print("Securely connected and authorized! Streaming audio...")

        loop = asyncio.get_running_loop()

        # Callback invoked by sounddevice whenever new microphone data is available
        def callback(indata, frames, time, status):
            if status:
                print(f"Stream status: {status}")
            # Asynchronously transmit raw audio bytes over the WebSocket
            asyncio.run_coroutine_threadsafe(websocket.send(indata.tobytes()), loop)

        # Start recording audio stream from default input device
        with sd.InputStream(
            samplerate=SAMPLERATE,
            channels=CHANNELS,
            dtype="int16",
            blocksize=BLOCKSIZE,
            callback=callback,
        ):
            print("Press Ctrl+C to stop streaming.")
            while True:
                await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        asyncio.run(stream_audio())
    except KeyboardInterrupt:
        print("\nStreaming stopped by user.")
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"Connection rejected by server: {e}")
