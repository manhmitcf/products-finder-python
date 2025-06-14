import os
import json
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from text_chunker import process_products_with_chunking
import torch
def load_and_process_data():
    """
    Load product data, create chunks, generate embeddings, and store in MongoDB
    """
    
    # Load environment variables
    load_dotenv()
    MONGO_USER = os.getenv('MONGO_USER')
    MONGO_PASS = os.getenv('MONGO_PASS')
    MONGO_HOST = os.getenv('MONGO_HOST')
    MONGO_DB = os.getenv('MONGO_DB')
    MONGO_COLLECTION = os.getenv('MONGO_COLLECTION')
    
    # Connect to MongoDB
    uri = f"mongodb+srv://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}/?retryWrites=true&w=majority"
    try:
        client = MongoClient(uri)
        db = client[MONGO_DB]
        
        # Use a new collection for chunked data
        collection = db[f"{MONGO_COLLECTION}"]
        print("Successfully connected to MongoDB Atlas.")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        return
    # Setup device
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")
    # Load the sentence transformer model
    print("Loading sentence-transformer model...")
    model = SentenceTransformer("bkai-foundation-models/vietnamese-bi-encoder", device=device)
    print("Model loaded successfully.")
    
    # Load product data
    print("Loading product data...")
    with open('data/products_data.json', 'r', encoding='utf-8') as f:
        products = json.load(f)
    print(f"Loaded {len(products)} products.")
    
    # Process products with chunking
    print("Processing products with chunking...")
    chunked_documents = process_products_with_chunking(
        products=products,
        model=model,
        chunk_size=300,  # Adjust based on your needs
        overlap=50       # Overlap between chunks
    )
    
    # Clear existing data
    print("Clearing existing chunked data...")
    collection.delete_many({})
    
    # Insert chunked documents
    print(f"Inserting {len(chunked_documents)} chunked documents...")
    batch_size = 100
    
    for i in range(0, len(chunked_documents), batch_size):
        batch = chunked_documents[i:i + batch_size]
        try:
            collection.insert_many(batch)
            print(f"Inserted batch {i//batch_size + 1}/{(len(chunked_documents) + batch_size - 1)//batch_size}")
        except Exception as e:
            print(f"Error inserting batch: {e}")
    
    print("Data processing and insertion completed!")
    
    # Create index for vector search (if not exists)
    try:
        # Note: You'll need to create the vector search index manually in MongoDB Atlas
        # This is just a regular index for other fields
        collection.create_index([("product_id", 1)])
        collection.create_index([("name", "text")])
        print("Indexes created successfully.")
    except Exception as e:
        print(f"Note: {e}")
    
    print("\n" + "="*50)
    print("IMPORTANT: Vector Search Index Setup")
    print("="*50)
    print("You need to create a vector search index in MongoDB Atlas:")
    print("1. Go to your MongoDB Atlas cluster")
    print("2. Navigate to Search -> Create Search Index")
    print("3. Choose 'JSON Editor' and use this configuration:")
    print("""
{
  "fields": [
    {
      "numDimensions": 768,
      "path": "description_vector",
      "similarity": "cosine",
      "type": "vector"
    }
  ]
}
    """)
    print(f"4. Name the index: 'vector_search_chunked'")
    print(f"5. Apply to collection: '{MONGO_COLLECTION}'")
    print("="*50)

if __name__ == "__main__":
    load_and_process_data()