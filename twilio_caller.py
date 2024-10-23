import os
from twilio.rest import Client
from dotenv import load_dotenv
import ngrok
from flask import Flask, request, Response
from flask_sockets import Sockets
from pyngrok import ngrok
load_dotenv()


app = Flask(__name__)
sockets = Sockets(app)



# Find your Account SID and Auth Token at twilio.com/console
# and set the environment variables. See http://twil.io/secure
account_sid = os.environ["TWILIO_ACCOUNT_SID"]
auth_token = os.environ["TWILIO_AUTH_TOKEN"]
MY_NUM = os.getenv('MY_NUM') # Your phone number
NGROK_AUTH_TOKEN = os.getenv('NGROK_AUTHTOKEN')
TWILIO_NUMBER = os.getenv('TWILIO_NUMBER') # Twilio phone number to call
PORT = 5000
DEBUG = False
INCOMING_CALL_ROUTE = '/'  # Endpoint where Twilio sends the call
ngrok.set_auth_token(NGROK_AUTH_TOKEN)

client = Client(account_sid, auth_token)
# Open Ngrok tunnel
listener = ngrok.connect(PORT)
print(f"Ngrok tunnel opened at {listener.public_url} for port {PORT}")
NGROK_URL = listener.public_url

# Set ngrok URL to be the webhook for the appropriate Twilio number
# twilio_numbers = client.incoming_phone_numbers.list()
# twilio_number_sid = [num.sid for num in twilio_numbers if num.phone_number == TWILIO_NUMBER][0]
# client.incoming_phone_numbers(twilio_number_sid).update(voice_url=f"{NGROK_URL}{INCOMING_CALL_ROUTE}")


call = client.calls.create(
    from_=TWILIO_NUMBER,
    to=MY_NUM,
    url= NGROK_URL,
)

print(call.sid)

if __name__ == '__main__':
    app.run(port=PORT, debug=DEBUG)