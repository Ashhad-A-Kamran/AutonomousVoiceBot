import chromadb
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings  # or another embedding provider




# Initialize embeddings
embeddings = OpenAIEmbeddings()

# Create a ChromaDB instance
chroma_db = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)


    
collection = client.create_collection(name="live_audio")

async def handle_audio_stream(audio_data):
    # Convert audio data to embeddings
    embedding = convert_audio_to_embedding(audio_data)
    
    # Create metadata
    metadata = {
        "timestamp": get_current_timestamp(),  # Define how to get the current timestamp
        "additional_info": "some metadata",
    }

    # Store the embedding and metadata in ChromaDB
    collection.add([{"embedding": embedding, "metadata": metadata}])

# Handle incoming audio from Twilio in your streaming setup