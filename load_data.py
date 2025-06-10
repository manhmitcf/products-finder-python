import os
import json
from pymongo import MongoClient
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# 1. Tải các biến môi trường từ file .env
load_dotenv()
MONGO_USER = os.getenv('MONGO_USER')
MONGO_PASS = os.getenv('MONGO_PASS')
MONGO_HOST = os.getenv('MONGO_HOST')
MONGO_DB = os.getenv('MONGO_DB')
MONGO_COLLECTION = os.getenv('MONGO_COLLECTION')
DATA_PATH = r"data/products_data.json"

# Xây dựng chuỗi kết nối Atlas
uri = f"mongodb+srv://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}/?retryWrites=true&w=majority"

# 2. Tải mô hình embedding
print("Loading sentence-transformer model...")
model = SentenceTransformer("bkai-foundation-models/vietnamese-bi-encoder")
print("Model loaded.")

client = None
try:
    # 3. Kết nối đến MongoDB Atlas
    print("Connecting to MongoDB Atlas...")
    client = MongoClient(uri)
    db = client[MONGO_DB]
    collection = db[MONGO_COLLECTION]
    print("Successfully connected to MongoDB Atlas.")

    # Xóa dữ liệu cũ trong collection để tránh trùng lặp (tùy chọn)
    print(f"Clearing old data from collection '{MONGO_COLLECTION}'...")
    collection.delete_many({})
    
    # 4. Đọc file dữ liệu JSON
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        news_array = json.load(f)

    # 5. Xử lý và tải từng bài báo lên
    print(f"Processing and uploading {len(news_array)} articles...")
    count = 0
    for i, news_item in enumerate(news_array):
        # Lấy mô tả ngắn để tạo embedding
        text_to_embed = news_item.get('descriptioninfo')
        
        # Bỏ qua nếu không có mô tả
        if not text_to_embed:
            continue

        # Tạo vector embedding cho văn bản
        embedding = model.encode(text_to_embed)
        
        # Thêm trường vector vào document
        # Phải chuyển đổi numpy array thành list để MongoDB có thể lưu trữ
        news_item['description_vector'] = embedding.tolist()

        # Chèn document đã được vector hóa vào collection
        collection.insert_one(news_item)
        print(f"  ({i+1}/{len(news_array)}) Stored: '{news_item['name'][:50]}...'")
        count += 1
        if count == 1000:
            break
        
    print("\nData loading and vectorization complete!")
    print(f"Total documents in collection: {collection.count_documents({})}")

except Exception as e:
    print(f"An error occurred: {e}")
finally:
    # 6. Đảm bảo kết nối được đóng
    if client:
        client.close()
        print("MongoDB connection closed.")