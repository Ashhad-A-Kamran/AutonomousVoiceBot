from flask import Flask, request, Response
from flask_sockets import Sockets

PORT = 5000
DEBUG = False
INCOMING_CALL_ROUTE = '/' # Endpoint in our app where TWilio looks for code when we receive a call
WEBSCOKET_ROUTE = '/realtime' # Route of the websocket where audio stream will be sent 


app = Flask(__name__)
sockets = Sockets(app)


@app.route(INCOMING_CALL_ROUTE, methods=['GET', 'POST'])
def receive_call():
    if request.method == 'POST':
        xml = f""" 
        <Reponse>
            <Say> Hello! Welcome to Deepgram. Please start speaking after the beep. </Say>
        </Reponse>
        """.strip()
        return Response(xml, mimetype='text/xml')
    else:
        return "Hello, World!"

@sockets.route(WEBSCOKET_ROUTE)
def transcription_websocket(ws):
    pass

if __name__ == '__main__':
    app.run(port=PORT, debug=DEBUG)

