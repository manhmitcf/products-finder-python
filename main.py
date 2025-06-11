import os
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# --- KHỞI TẠO ---

# 1. Tải các biến môi trường
load_dotenv()
MONGO_USER = os.getenv('MONGO_USER')
MONGO_PASS = os.getenv('MONGO_PASS')
MONGO_HOST = os.getenv('MONGO_HOST')
MONGO_DB = os.getenv('MONGO_DB')
MONGO_COLLECTION = os.getenv('MONGO_COLLECTION')

# 2. Kết nối đến MongoDB Atlas
uri = f"mongodb+srv://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}/?retryWrites=true&w=majority"
try:
    client = MongoClient(uri)
    db = client[MONGO_DB]
    collection = db[MONGO_COLLECTION]
    print("Successfully connected to MongoDB Atlas.")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    exit()

# 3. Tải mô hình embedding (sẽ được cache sau lần chạy đầu)
print("Loading sentence-transformer model...")
model = SentenceTransformer("keepitreal/vietnamese-sbert")
print("Model loaded.")

# 4. Khởi tạo ứng dụng FastAPI
app = FastAPI(
    title="News Finder API",
    description="An API to find news articles using semantic vector search with MongoDB Atlas.",
    version="1.0.0"
)

# --- ĐỊNH NGHĨA API ---

# 5. Định nghĩa mô hình dữ liệu cho request body
class SearchRequest(BaseModel):
    text: str
    limit: int = 5 # Số kết quả trả về, mặc định là 5

# 6. Tạo endpoint /search
@app.post("/search", summary="Find news articles by semantic search")
async def search_news(request: SearchRequest):
    """
    Nhận một chuỗi văn bản, tìm kiếm các bài báo có nội dung tương tự.
    - **text**: Câu hoặc đoạn văn bản để tìm kiếm.
    - **limit**: Số lượng kết quả tối đa muốn nhận.
    """
    if not request.text:
        raise HTTPException(status_code=400, detail="Search text cannot be empty.")

    try:
        # a. Vector hóa câu truy vấn từ client
        query_vector = model.encode(request.text).tolist()

        # b. Xây dựng aggregation pipeline cho Vector Search
        # Đây là phần cốt lõi của việc tìm kiếm
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_search",       # Tên index bạn đã tạo trên Atlas
                    "path": "description_vector",   # Trường chứa vector trong document
                    "queryVector": query_vector,    # Vector của câu truy vấn
                    "numCandidates": 100,           # Số "ứng viên" gần nhất để xem xét
                    "limit": request.limit          # Số kết quả cuối cùng trả về
                }
            },
            {
                # c. Định dạng lại kết quả đầu ra, chỉ lấy các trường cần thiết
                "$project": {
                    "_id": 0,                     # Bỏ trường _id
                    "name": 1,
                    "url": 1,
                    "descriptioninfo": 1,
                    "score": {
                        "$meta": "vectorSearchScore" # Lấy điểm tương đồng từ kết quả search
                    }
                }
            }
        ]
        
        # d. Thực thi query và chuyển kết quả thành list
        results = list(collection.aggregate(pipeline))
        return results

    except Exception as e:
        # Trả về lỗi server nếu có vấn đề xảy ra
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")

# Lệnh để chạy server (sử dụng cho việc phát triển)
if __name__ == "__main__":
    print("Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)