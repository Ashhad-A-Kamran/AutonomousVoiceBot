from deepgram import DeepgramClient, PrerecordedOptions
from flask import Flask, request, Response
from flask_sockets import Sockets
from dotenv import load_dotenv
import base64
import json
import os
from pyngrok import ngrok
from twilio.rest import Client
import asyncio
import websockets


load_dotenv()

PORT = 5000
DEBUG = False
INCOMING_CALL_ROUTE = '/'  # Endpoint where Twilio sends the call
WEBSOCKET_ROUTE = '/realtime'  # WebSocket route for the audio stream
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
MY_NUM = os.getenv('MY_NUM') # Your phone number
TWILIO_NUMBER = os.getenv('TWILIO_NUMBER') # Twilio phone number to call

# Twilio authentication
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
client = Client(account_sid, auth_token)

app = Flask(__name__)
sockets = Sockets(app)

# Initialize Deepgram client
deepgram = DeepgramClient(DEEPGRAM_API_KEY)

# listener = ngrok.connect(PORT)
# print(f"Ngrok tunnel opened at {listener.public_url} for port {PORT}")
# NGROK_URL = listener.public_url


@app.route(INCOMING_CALL_ROUTE, methods=['GET'])
def receive_call():
    """Handle incoming Twilio calls."""
    try:
        # Initiate an outgoing call via Twilio
        call = client.calls.create(
            from_=TWILIO_NUMBER,
            to=MY_NUM,
            url=f"{NGROK_URL}{INCOMING_CALL_ROUTE}",  # URL for Twilio to hit for TwiML
        )
        print(f"Call initiated: {call.sid}")
        return f"Call initiated: {call.sid}"
    except Exception as e:
        print(f"Error initiating call: {e}")
        
        """Respond with TwiML to direct the call."""
    xml = f"""
<Response>
    <Say>Your speech is being transcribed.</Say>
    <Connect>
        <Stream url='wss://{request.host}{WEBSOCKET_ROUTE}' />
    </Connect>
    <Say> Your speech has been transcribed. </Say>
</Response>
    """.strip()
    return Response(xml, mimetype='text/xml')


# @app.route(INCOMING_CALL_ROUTE, methods=['POST'])
# def handle_twilio_callback():
#     """Respond with TwiML to direct the call."""
#     xml = f"""
# <Response>
#     <Say>Your speech is being transcribed.</Say>
#     <Connect>
#         <Stream url='wss://{request.host}{WEBSOCKET_ROUTE}' />
#     </Connect>
#     <Say> Your speech has been transcribed. </Say>
# </Response>
#     """.strip()
#     return Response(xml, mimetype='text/xml')


# @sockets.route(WEBSOCKET_ROUTE)
# def transcription_websocket(ws):
#     """Handle the incoming WebSocket audio stream from Twilio."""
#     try:
#         while True:
#             # Receive audio data from Twilio via WebSocket
#             data = json.loads(ws.receive())
            
#             # Event handling logic
#             if data['event'] == "connected":
#                 print('WebSocket connected')
#             elif data['event'] == "start":
#                 print('Stream started')
#             elif data['event'] == "media":
#                 # Decode the base64 audio payload from Twilio
#                 payload_b64 = data['media']['payload']
#                 payload_mulaw = base64.b64decode(payload_b64)
                
#                 # Send the audio data to Deepgram for transcription
#                 transcript = stream_audio_to_deepgram(payload_mulaw)
#                 print(f"Transcript: {transcript}")

#             elif data['event'] == "stop":
#                 print('Stream stopped')
#                 ws.close()
#     except Exception as e:
#         print(f"Error in WebSocket: {e}")



@sockets.route(WEBSOCKET_ROUTE)
def stream_audio_to_deepgram(audio_data):
    """Send audio data to Deepgram WebSocket for transcription."""
    try:
        # Define the connection to Deepgram's WebSocket for real-time transcription
        deepgram_ws_url = "wss://api.deepgram.com/v1/listen"

        # WebSocket connection to Deepgram
        async def transcribe():
            async with websockets.connect(
                deepgram_ws_url,
                extra_headers={
                    "Authorization": f"Token {DEEPGRAM_API_KEY}",
                    "Content-Type": "audio/x-mulaw; rate=8000",
                },
            ) as websocket:
                # Send the audio data to Deepgram
                await websocket.send(audio_data)

                # Receive transcription result
                response = await websocket.recv()
                result = json.loads(response)

                # Extract and return the transcript
                transcript = result['channel']['alternatives'][0]['transcript']
                return transcript

        return asyncio.run(transcribe())

    except Exception as e:
        print(f"Deepgram Exception: {e}")
        return None

if __name__ == '__main__':
    try:
        # Open Ngrok tunnel
        listener = ngrok.connect(PORT)
        print(f"Ngrok tunnel opened at {listener.public_url} for port {PORT}")
        NGROK_URL = listener.public_url

        # Set ngrok URL to be the webhook for the appropriate Twilio number
        twilio_numbers = client.incoming_phone_numbers.list()
        twilio_number_sid = [num.sid for num in twilio_numbers if num.phone_number == TWILIO_NUMBER][0]
        client.incoming_phone_numbers(twilio_number_sid).update(voice_url=f"{NGROK_URL}{INCOMING_CALL_ROUTE}")

        # run the app
        app.run(port=PORT, debug=DEBUG)
    finally:
        # Always disconnect the ngrok tunnel
        ngrok.disconnect()
