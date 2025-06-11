
# Product Finder Service - Dịch vụ Tìm kiếm sản phẩm Ngữ nghĩa

Dự án này là một dịch vụ API backend được xây dựng bằng Python, FastAPI và MongoDB Atlas. Dịch vụ cho phép tìm kiếm các sản phẩm dựa trên ý nghĩa ngữ nghĩa của câu truy vấn thay vì chỉ dựa vào từ khóa. Điều này được thực hiện bằng cách sử dụng **Vector Search** của MongoDB Atlas.

## Tính năng chính

-   **Tìm kiếm Ngữ nghĩa (Semantic Search):** Tìm các bài báo liên quan đến một chủ đề ngay cả khi các từ khóa chính xác không xuất hiện trong văn bản.
-   **Vector Embeddings:** Sử dụng mô hình `bkai-foundation-models/vietnamese-bi-encoder` từ thư viện `sentence-transformers` để chuyển đổi nội dung văn bản thành các vector số học (embeddings).
-   **API Backend:** Xây dựng API RESTful bằng FastAPI để nhận truy vấn và trả về kết quả.
-   **Cơ sở dữ liệu Vector:** Lưu trữ và truy vấn các vector embeddings một cách hiệu quả bằng MongoDB Atlas Vector Search.

## Cấu trúc dự án

```
news-finder-python/
├── venv/
├── data/
│   └── products_data.json
├── .env
├── .gitignore
├── requirements.txt
├── load_data.py
├── main.py
└── README.md
```

-   `main.py`: Chứa mã nguồn cho API server FastAPI.
-   `load_data.py`: Kịch bản để xử lý dữ liệu thô, tạo vector embeddings, và tải lên MongoDB Atlas.
-   `data/products_data`: Dữ liệu mẫu chứa các bài báo.
-   `.env`: File cấu hình chứa các biến môi trường (cần được tạo thủ công).
-   `requirements.txt`: Các thư viện Python cần thiết cho dự án.

## Yêu cầu

-   Python 3.8+
-   Tài khoản [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register) (cluster M0 miễn phí là đủ).
-   `curl` hoặc `wget` để tải dữ liệu.

## Hướng dẫn cài đặt và chạy dự án

### 1. Clone và thiết lập Môi trường

```bash
# Clone repository (nếu có) hoặc tạo thư mục dự án
git clone <your-repository-url>
cd products-finder-python

# Tạo và kích hoạt môi trường ảo
python -m venv venv
source venv/bin/activate  # Trên Windows: venv\Scripts\activate

# Cài đặt các thư viện cần thiết
pip install -r requirements.txt
```

### 2. Cấu hình MongoDB Atlas

1.  **Tạo một Cluster trên MongoDB Atlas:** Đảm bảo bạn có một cluster đang chạy (M0 là đủ).
2.  **Tạo một người dùng Database:** Trong mục **Database Access**, tạo một người dùng với quyền đọc/ghi vào database của bạn (ví dụ: `readWriteAnyDatabase`). Ghi lại **username** và **password**.
3.  **Cho phép truy cập từ IP của bạn:** Trong mục **Network Access**, thêm địa chỉ IP hiện tại của bạn vào danh sách cho phép.
4.  **Lấy Hostname của Cluster:** Trong mục **Database**, nhấn vào nút **Connect** trên cluster của bạn, chọn **Drivers**, và sao chép phần hostname từ chuỗi kết nối (ví dụ: `cluster0.abcde.mongodb.net`).

### 3. Thiết lập biến Môi trường

Tạo một file có tên `.env` trong thư mục gốc của dự án và điền thông tin bạn đã lấy từ Bước 2.

**.env**
```env
# Thay thế bằng thông tin người dùng database của bạn trên Atlas
MONGO_USER=your_atlas_user
MONGO_PASS=your_atlas_password

# Thay thế bằng hostname của cluster của bạn
MONGO_HOST=your_cluster_hostname.mongodb.net

# Tên database và collection bạn muốn sử dụng
MONGO_DB=myvectordb
MONGO_COLLECTION=vectorized_data
```
### 4. Tạo foder data đưa file json vào và đặt tên như cấu trúc `data/products_data.json`
```bash
mkdir data
```
### 5. Chuẩn bị dữ liệu và Tải lên Atlas

Chạy kịch bản `load_data.py` để tạo vector embeddings cho các bài báo và lưu chúng vào MongoDB Atlas.

```bash
python load_data.py
```
Quá trình này có thể mất vài phút, tùy thuộc vào tốc độ mạng và máy tính của bạn, vì nó cần tải mô hình embedding lần đầu và xử lý dữ liệu.

### 6. Tạo Vector Search Index

Đây là bước quan trọng để kích hoạt tìm kiếm ngữ nghĩa. Bạn cần thực hiện trên giao diện web của MongoDB Atlas.

1.  Đi đến cluster của bạn, chọn tab **Atlas Search**.
2.  Nhấn **Create Search Index** và chọn **Atlas Vector Search** (JSON Editor).
3.  Đặt tên Index là `vector_search`.
4.  Chọn Database là `myvectordb` và Collection là `vectorized_data`.
5.  Dán định nghĩa JSON sau:

    ```json
    {
      "mappings": {
        "dynamic": false,
        "fields": {
          "description_vector": {
            "type": "knnVector",
            "dimensions": 768,
            "similarity": "cosine"
          }
        }
      }
    }
    ```
    > **Lưu ý:** `numDimensions` là **384** vì chúng ta sử dụng mô hình `all-MiniLM-L6-v2`.

6.  Tạo index và chờ cho đến khi trạng thái chuyển thành **Active**.

### 7. Chạy API Server

Bây giờ bạn đã sẵn sàng để khởi động dịch vụ API.

```bash
uvicorn main:app --reload
```
Server sẽ chạy tại `http://localhost:8000`.

### 8. Thử nghiệm API

Mở một terminal khác và sử dụng `curl` để gửi yêu cầu đến API.

```bash
curl -X POST http://localhost:8000/search \
-H "Content-Type: application/json" \
-d '{"text": "your_queery"}'
```

Bạn cũng có thể truy cập `http://localhost:8000/docs` trong trình duyệt để xem giao diện tài liệu API tương tác của FastAPI (Swagger UI).

## Giao diện người dùng với Streamlit

Dự án đã được tích hợp giao diện người dùng thân thiện bằng Streamlit để dễ dàng sử dụng mà không cần gọi API trực tiếp.

### Chạy với Python

#### 1. Chạy cả API và UI cùng lúc

**Trên Windows:**
```bash
.\run_app.bat
```

**Trên Linux/Mac:**
```bash
chmod +x run_app.sh
./run_app.sh
```

#### 2. Hoặc chạy riêng từng service

```bash
# Terminal 1: Chạy API
uvicorn main:app --reload

# Terminal 2: Chạy Streamlit UI
streamlit run streamlit_app.py
```

### Truy cập ứng dụng

- **Streamlit UI:** http://localhost:8501 (Giao diện chính)
- **FastAPI:** http://localhost:8000 (API Backend)
- **API Docs:** http://localhost:8000/docs (Tài liệu API)

### Tính năng Streamlit UI

- ✅ **Giao diện thân thiện** - Dễ sử dụng cho người không kỹ thuật
- ✅ **Tìm kiếm thông minh** - Nhập từ khóa và nhận kết quả ngay lập tức
- ✅ **Hiển thị đa dạng** - Danh sách, bảng dữ liệu, và biểu đồ phân tích
- ✅ **Lịch sử tìm kiếm** - Lưu và tái sử dụng các truy vấn trước
- ✅ **Ví dụ tìm kiếm** - Gợi ý từ khóa phổ biến
- ✅ **Kiểm tra kết nối** - Theo dõi trạng thái API
- ✅ **Xuất dữ liệu** - Tải kết quả dưới dạng CSV
- ✅ **Responsive design** - Tương thích mọi thiết bị
