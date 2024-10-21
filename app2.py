from dotenv import load_dotenv
import os
from deepgram import DeepgramClient, PrerecordedOptions
import json
load_dotenv()




DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

#Speech-to-Text
# We have to give the customer's voice to this AUDIO_URL which we are getting from 
AUDIO_URL = {
    "url": "https://static.deepgram.com/examples/Bueller-Life-moves-pretty-fast.wav"
}

def main():
    try:
        #Speech to Text
        deepgram = DeepgramClient(DEEPGRAM_API_KEY)

        options = PrerecordedOptions(
            model="nova-2",
            language="en",
            smart_format=True,
        )

        response = deepgram.listen.prerecorded.v("1").transcribe_url(AUDIO_URL, options)
        print(response.to_json(indent=4))
        with open('response.json', 'w') as json_file:
            json.dump(response, json_file, indent=4)

    except Exception as e:
        print(f"Exception: {e}")









if __name__ == "__main__":
    main()