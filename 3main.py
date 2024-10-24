from deepgram import DeepgramClient
from flask import Flask, request, Response
from flask_sockets import Sockets
import base64
import json
import os
from dotenv import load_dotenv
from pyngrok import ngrok
from twilio.rest import Client
import asyncio
import websockets
import datetime

load_dotenv()

PORT = 5000
DEBUG = False
INCOMING_CALL_ROUTE = '/'  # Endpoint where Twilio sends the call
WEBSOCKET_ROUTE = '/realtime'  # WebSocket route for the audio stream
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
MY_NUM = os.getenv('MY_NUM')  # Your phone number
TWILIO_NUMBER = os.getenv('TWILIO_NUMBER')  # Twilio phone number to call

# Twilio authentication
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
client = Client(account_sid, auth_token)

app = Flask(__name__)
sockets = Sockets(app)

# Initialize Deepgram client
deepgram = DeepgramClient(DEEPGRAM_API_KEY)

@app.route(INCOMING_CALL_ROUTE, methods=['GET', 'POST'])
def receive_call():
    """Handle incoming Twilio calls and provide TwiML instructions."""
    # Generate TwiML response with WebSocket stream URL
    try:
        call = client.calls.create(
            from_=TWILIO_NUMBER,
            to="+923222772830",
            url=f"{NGROK_URL}{INCOMING_CALL_ROUTE}",  # URL for Twilio to hit for TwiML
        )
        print(f"Call initiated: {call.sid}")
        return f"Call initiated: {call.sid}"
    except Exception as e:
        print(f"Error initiating call: {e}")
    xml = f"""
<Response>
    <Say>Your speech is being transcribed.</Say>
    <Connect>
        <Stream url='wss://api.deepgram.com/v1/listen' />
    </Connect>
</Response>
    """.strip()
    return Response(xml, mimetype='text/xml')

@sockets.route(WEBSOCKET_ROUTE)
def transcription_websocket(ws):
    """Handle incoming audio from Twilio and send it to Deepgram for transcription."""
    try:
        # Deepgram WebSocket URL
        deepgram_ws_url = "wss://api.deepgram.com/v1/listen"

        # To store transcription data for saving to JSON
        transcriptions = []

        # Asynchronous function to send audio to Deepgram
        async def send_to_deepgram():
            async with websockets.connect(
                deepgram_ws_url,
                extra_headers={
                    "Authorization": f"Token {DEEPGRAM_API_KEY}",
                    "Content-Type": "audio/x-mulaw; rate=8000",
                }
            ) as dg_ws:
                while True:
                    # Receive base64-encoded audio data from Twilio WebSocket
                    data = json.loads(ws.receive())
                    
                    if data['event'] == "media":
                        payload_b64 = data['media']['payload']
                        payload_mulaw = base64.b64decode(payload_b64)

                        # Send the decoded mu-law audio to Deepgram WebSocket
                        await dg_ws.send(payload_mulaw)
                    
                    elif data['event'] == "stop":
                        print("Stream stopped.")
                        break

                # Receive and print the transcription result from Deepgram
                while True:
                    transcript_data = await dg_ws.recv()
                    transcript_json = json.loads(transcript_data)
                    transcript = transcript_json['channel']['alternatives'][0]['transcript']

                    # Print the transcript to the console
                    print(f"Transcript: {transcript}")

                    # Append the transcription to the list
                    transcriptions.append({
                        'timestamp': "TEST",
                        'transcription': transcript
                    })
        
        # Run the asynchronous transcription logic
        asyncio.run(send_to_deepgram())

        # Once done, save the transcriptions to a JSON file
        if transcriptions:
            # File naming format: transcripts_<date>.json
            filename = f"transcripts_{datetime.now()}.json"
            with open(filename, 'w') as f:
                json.dump(transcriptions, f, indent=4)
            print(f"Transcriptions saved to {filename}")

    except Exception as e:
        print(f"Error: {e}")
        ws.close()

if __name__ == '__main__':
    # Start the ngrok tunnel and Flask server
    listener = ngrok.connect(PORT)
    print(f"Ngrok tunnel opened at {listener.public_url} for port {PORT}")
    NGROK_URL = listener.public_url

    # Update Twilio number webhook to point to ngrok URL
    twilio_numbers = client.incoming_phone_numbers.list()
    twilio_number_sid = [num.sid for num in twilio_numbers if num.phone_number == TWILIO_NUMBER][0]
    client.incoming_phone_numbers(twilio_number_sid).update(voice_url=f"{NGROK_URL}{INCOMING_CALL_ROUTE}")

    # Run Flask app
    app.run(port=PORT, debug=DEBUG)
