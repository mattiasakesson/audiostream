import asyncio
import ssl
import websockets
import sounddevice as sd
import numpy as np

API_KEY = "my-secret-api-key-123"  # Replace with a strong secret key
SAMPLERATE = 44100
CHANNELS = 1

# Start an output audio stream to play back incoming audio in real-time
stream = sd.OutputStream(samplerate=SAMPLERATE, channels=CHANNELS, dtype="int16")
stream.start()


async def authenticate_and_handle(websocket):
    # 1. Authentication: Verify headers during the handshake
    client_key = websocket.request_headers.get("X-API-Key")
    if client_key != API_KEY:
        print(f"Rejected connection from {websocket.remote_address}: Invalid API key")
        await websocket.close(code=4001, reason="Unauthorized")
        return

    print(f"Authorized client connected from {websocket.remote_address}!")

    # 2. Receive and play back the audio stream
    try:
        async for message in websocket:
            # Convert raw bytes back to a numpy array and output to speakers
            data = np.frombuffer(message, dtype=np.int16)
            stream.write(data)
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected.")


async def main():
    # Configure SSL/TLS context for secure communication (WSS)
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    # Update paths if using real domain certificates (e.g., Let's Encrypt)
    ssl_context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

    # Start the WebSocket server with TLS enabled and message size limits
    async with websockets.serve(
        authenticate_and_handle,
        "0.0.0.0",
        8765,
        ssl=ssl_context,
        max_size=10_000_000,  # Limit max message size to 10MB to prevent DoS
    ):
        print("Secure WSS server started on port 8765...")
        await asyncio.Future()  # Keep server running perpetually


if __name__ == "__main__":
    asyncio.run(main())
