import os
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from text_chunker import aggregate_search_results
import torch

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
    # Use the chunked collection
    collection = db[f"{MONGO_COLLECTION}"]
    print("Successfully connected to MongoDB Atlas (collection).")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    exit()
# Setup device
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Using device: {device}")
# 3. Tải mô hình embedding (sẽ được cache sau lần chạy đầu)
print("Loading sentence-transformer model...")
model = SentenceTransformer("bkai-foundation-models/vietnamese-bi-encoder", device=device)
print("Model loaded.")

# 4. Khởi tạo ứng dụng FastAPI
app = FastAPI(
    title="Products Finder API (with Chunking)",
    description="An API to find products using semantic vector search with text chunking for better accuracy.",
    version="2.0.0"
)

# --- ĐỊNH NGHĨA API ---

# 5. Định nghĩa mô hình dữ liệu cho request body
class SearchRequest(BaseModel):
    text: str
    limit: int = 5  # Số kết quả trả về, mặc định là 5
    chunk_limit: int = 20  # Số chunks tối đa để tìm kiếm, mặc định là 20

# 6. Tạo endpoint /search
@app.post("/search", summary="Find products by semantic search with chunking")
async def search_products(request: SearchRequest):
    """
    Nhận một chuỗi văn bản, tìm kiếm các sản phẩm có nội dung tương tự sử dụng chunking.
    - **text**: Câu hoặc đoạn văn bản để tìm kiếm.
    - **limit**: Số lượng sản phẩm tối đa muốn nhận.
    - **chunk_limit**: Số lượng chunks tối đa để tìm kiếm (sẽ được gộp lại thành sản phẩm).
    """
    if not request.text:
        raise HTTPException(status_code=400, detail="Search text cannot be empty.")

    try:
        # a. Vector hóa câu truy vấn từ client
        query_vector = model.encode(request.text, batch_size=128).tolist()

        # b. Xây dựng aggregation pipeline cho Vector Search với chunks
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_search_chunked",  # Tên index cho chunked collection
                    "path": "description_vector",      # Trường chứa vector trong document
                    "queryVector": query_vector,       # Vector của câu truy vấn
                    "numCandidates": request.chunk_limit * 5,  # Nhiều candidates hơn để có lựa chọn tốt
                    "limit": request.chunk_limit       # Số chunks tối đa để lấy
                }
            },
            {
                # c. Định dạng lại kết quả đầu ra
                "$project": {
                    "_id": 0,
                    "product_id": 1,
                    "name": 1,
                    "url": 1,
                    "brand": 1,
                    "category_name": 1,
                    "price": 1,
                    "market_price": 1,
                    "average_rating": 1,
                    "chunk_text": 1,
                    "chunk_id": 1,
                    "is_chunk": 1,
                    "descriptioninfo": "$chunk_text",  # Use chunk text as description
                    "score": {
                        "$meta": "vectorSearchScore"
                    }
                }
            }
        ]
        
        # d. Thực thi query và chuyển kết quả thành list
        chunk_results = list(collection.aggregate(pipeline))
        
        # e. Aggregate chunks back to products
        aggregated_results = aggregate_search_results(
            results=chunk_results,
            max_products=request.limit
        )
        
        return aggregated_results

    except Exception as e:
        # Trả về lỗi server nếu có vấn đề xảy ra
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")

# 7. Endpoint để kiểm tra thông tin về chunking
@app.get("/info", summary="Get information about the chunked data")
async def get_info():
    """
    Lấy thông tin về dữ liệu đã được chunk.
    """
    try:
        total_chunks = collection.count_documents({})
        unique_products = len(collection.distinct("product_id"))
        
        # Get some sample statistics
        pipeline = [
            {"$group": {
                "_id": "$product_id",
                "chunk_count": {"$sum": 1}
            }},
            {"$group": {
                "_id": None,
                "avg_chunks_per_product": {"$avg": "$chunk_count"},
                "max_chunks_per_product": {"$max": "$chunk_count"},
                "min_chunks_per_product": {"$min": "$chunk_count"}
            }}
        ]
        
        stats = list(collection.aggregate(pipeline))
        chunk_stats = stats[0] if stats else {}
        
        return {
            "total_chunks": total_chunks,
            "unique_products": unique_products,
            "average_chunks_per_product": round(chunk_stats.get("avg_chunks_per_product", 0), 2),
            "max_chunks_per_product": chunk_stats.get("max_chunks_per_product", 0),
            "min_chunks_per_product": chunk_stats.get("min_chunks_per_product", 0),
            "chunking_enabled": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting info: {e}")

# 8. Endpoint để tìm kiếm chunks cụ thể (for debugging)
@app.post("/search-chunks", summary="Search chunks directly (for debugging)")
async def search_chunks(request: SearchRequest):
    """
    Tìm kiếm trực tiếp các chunks (dành cho debug).
    """
    if not request.text:
        raise HTTPException(status_code=400, detail="Search text cannot be empty.")

    try:
        query_vector = model.encode(request.text).tolist()

        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_search_chunked",
                    "path": "description_vector",
                    "queryVector": query_vector,
                    "numCandidates": 100,
                    "limit": request.limit * 3  # More chunks for debugging
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "product_id": 1,
                    "name": 1,
                    "chunk_text": 1,
                    "chunk_id": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]
        
        results = list(collection.aggregate(pipeline))
        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching chunks: {e}")

# Lệnh để chạy server (sử dụng cho việc phát triển)
if __name__ == "__main__":
    print("Starting FastAPI server with chunking support...")
    uvicorn.run(app, host="0.0.0.0", port=8001)  # Use different port to avoid conflicts