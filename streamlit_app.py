import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime
import time

# Cấu hình trang
st.set_page_config(
    page_title="Products Finder - Tìm kiếm sản phẩm thông minh (Chunked)",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS tùy chỉnh
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .search-box {
        font-size: 1.1rem;
        padding: 0.5rem;
        border-radius: 10px;
        border: 2px solid #1f77b4;
    }
    .result-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
    }
    .score-badge {
        background-color: #28a745;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .chunk-badge {
        background-color: #17a2b8;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 15px;
        font-size: 0.7rem;
        font-weight: bold;
        margin-left: 0.5rem;
    }
    .sidebar-info {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .improvement-badge {
        background-color: #28a745;
        color: white;
        padding: 0.3rem 0.6rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        margin-left: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Hàm gọi API
def search_products(query, limit=5, api_url="http://localhost:8001"):
    """Gọi API để tìm kiếm sản phẩm với chunking"""
    try:
        response = requests.post(
            f"{api_url}/search",
            json={"text": query, "limit": limit, "chunk_limit": limit * 4},
            timeout=30
        )
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"Lỗi API: {response.status_code} - {response.text}"
    except requests.exceptions.ConnectionError:
        return None, "Không thể kết nối đến API. Vui lòng kiểm tra xem API server đã chạy chưa."
    except requests.exceptions.Timeout:
        return None, "Timeout: API mất quá nhiều thời gian để phản hồi."
    except Exception as e:
        return None, f"Lỗi không xác định: {str(e)}"

# Hàm lấy thông tin về chunking
def get_chunking_info(api_url="http://localhost:8001"):
    """Lấy thông tin về dữ liệu chunked"""
    try:
        response = requests.get(f"{api_url}/info", timeout=10)
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"Lỗi API: {response.status_code}"
    except:
        return None, "Không thể lấy thông tin chunking"

# Hàm kiểm tra trạng thái API
def check_api_status(api_url="http://localhost:8001"):
    """Kiểm tra xem API có hoạt động không"""
    try:
        response = requests.get(f"{api_url}/docs", timeout=5)
        return response.status_code == 200
    except:
        return False

# Header chính
st.markdown('<h1 class="main-header">🔍 Products Finder <span class="improvement-badge">✨ Chunked</span></h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Tìm kiếm sản phẩm thông minh với công nghệ AI và Text Chunking</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown('<div class="sidebar-info">', unsafe_allow_html=True)
    st.markdown("### ⚙️ Cấu hình")
    
    # Cấu hình API URL
    api_url = st.text_input(
        "🌐 API URL", 
        value="http://localhost:8001",
        help="URL của API server (chunked version)"
    )
    
    # Số lượng kết quả
    limit = st.slider(
        "📊 Số kết quả tối đa", 
        min_value=1, 
        max_value=20, 
        value=5,
        help="Số lượng sản phẩm tối đa muốn hiển thị"
    )
    
    # Kiểm tra trạng thái API và thông tin chunking
    st.markdown("### 🔌 Trạng thái API")
    if st.button("Kiểm tra kết nối"):
        with st.spinner("Đang kiểm tra..."):
            if check_api_status(api_url):
                st.success("✅ API hoạt động bình thường")
                
                # Lấy thông tin chunking
                info, error = get_chunking_info(api_url)
                if info:
                    st.markdown("### 📊 Thông tin Chunking")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Tổng chunks", info.get('total_chunks', 0))
                        st.metric("Sản phẩm", info.get('unique_products', 0))
                    with col2:
                        st.metric("TB chunks/SP", info.get('average_chunks_per_product', 0))
                        st.metric("Max chunks/SP", info.get('max_chunks_per_product', 0))
            else:
                st.error("❌ Không thể kết nối đến API")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Thông tin về chunking
    st.markdown("### 🧩 Text Chunking")
    st.markdown("""
    **Cải tiến mới:**
    - ✂️ Chia nhỏ mô tả dài thành các đoạn ngắn
    - 🎯 Tìm kiếm chính xác hơn trong nội dung chi tiết
    - 🚀 Tăng tốc độ xử lý và độ chính xác
    - 🔄 Gộp kết quả từ nhiều đoạn văn
    """)
    
    # Thông tin hướng dẫn
    st.markdown("### 📖 Hướng dẫn sử dụng")
    st.markdown("""
    1. **Nhập từ khóa** tìm kiếm vào ô bên dưới
    2. **Nhấn Enter** hoặc click nút Tìm kiếm
    3. **Xem kết quả** được sắp xếp theo độ liên quan
    4. **Click vào link** để xem chi tiết sản phẩm
    5. **Xem số chunks** tìm thấy cho mỗi sản phẩm
    """)
    
    # Ví dụ tìm kiếm
    st.markdown("### 💡 Ví dụ tìm kiếm")
    example_queries = [
        "sữa rửa mặt cho da dầu",
        "kem chống nắng SPF 50",
        "serum vitamin C",
        "mặt nạ dưỡng ẩm",
        "toner cho da nhạy cảm"
    ]
    
    for query in example_queries:
        if st.button(f"🔍 {query}", key=f"example_{query}"):
            st.session_state.search_query = query

# Khởi tạo session state
if 'search_history' not in st.session_state:
    st.session_state.search_history = []
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""

# Giao diện tìm kiếm chính
col1, col2 = st.columns([4, 1])

with col1:
    search_query = st.text_input(
        "🔍 Nhập từ khóa tìm kiếm:",
        value=st.session_state.search_query,
        placeholder="Ví dụ: sữa rửa mặt cho da nhạy cảm, kem dưỡng chống lão hóa...",
        key="main_search"
    )

with col2:
    st.markdown("<br>", unsafe_allow_html=True)  # Spacer
    search_button = st.button("🚀 Tìm kiếm", type="primary")

# Xử lý tìm kiếm
if search_button or (search_query and search_query != st.session_state.get('last_query', '')):
    if search_query.strip():
        st.session_state.last_query = search_query
        
        # Thêm vào lịch sử tìm kiếm
        if search_query not in st.session_state.search_history:
            st.session_state.search_history.insert(0, search_query)
            if len(st.session_state.search_history) > 10:
                st.session_state.search_history.pop()
        
        # Hiển thị loading
        with st.spinner(f"🔍 Đang tìm kiếm với chunking '{search_query}'..."):
            start_time = time.time()
            results, error = search_products(search_query, limit, api_url)
            search_time = time.time() - start_time
        
        if error:
            st.error(f"❌ {error}")
            
            # Gợi ý khắc phục
            st.markdown("### 🛠️ Cách khắc phục:")
            st.markdown("""
            1. **Kiểm tra API server**: Đảm bảo API đang chạy tại `http://localhost:8001`
            2. **Chạy API**: Sử dụng lệnh `python main_chunked.py`
            3. **Kiểm tra URL**: Đảm bảo URL API trong sidebar là chính xác
            4. **Chunked data**: Đảm bảo đã chạy `python load_data_with_chunking.py`
            """)
            
        elif results:
            # Hiển thị kết quả
            st.success(f"✅ Tìm thấy {len(results)} kết quả cho '{search_query}' trong {search_time:.2f}s")
            
            # Tabs cho các cách hiển thị khác nhau
            tab1, tab2, tab3 = st.tabs(["📋 Danh sách", "📊 Bảng dữ liệu", "📈 Phân tích"])
            
            with tab1:
                # Hiển thị dạng card
                for i, item in enumerate(results, 1):
                    with st.container():
                        # Header với thông tin chunking
                        chunk_info = ""
                        if item.get('total_chunks_found', 0) > 1:
                            chunk_info = f'<span class="chunk-badge">{item.get("total_chunks_found", 1)} chunks</span>'
                        
                        st.markdown(f"""
                        <div class="result-card">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <h3 style="margin: 0; color: #1f77b4;">#{i} {item.get('name', 'Không có tên')}</h3>
                                <div>
                                    <span class="score-badge">Điểm: {item.get('score', 0):.3f}</span>
                                    {chunk_info}
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Thông tin chi tiết
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            # Hiển thị mô tả chính
                            if item.get('descriptioninfo'):
                                st.write("📝 **Mô tả chính:**", item['descriptioninfo'])
                            
                            # Hiển thị các chunks liên quan khác (nếu có)
                            if item.get('relevant_chunks') and len(item.get('relevant_chunks', [])) > 1:
                                with st.expander(f"📄 Xem thêm {len(item.get('relevant_chunks', [])) - 1} đoạn liên quan"):
                                    for j, chunk in enumerate(item.get('relevant_chunks', [])[1:], 2):
                                        st.write(f"**Đoạn {j}:** {chunk}")
                            
                            if item.get('url'):
                                st.markdown(f"🔗 [Xem chi tiết sản phẩm]({item['url']})")
                        
                        with col2:
                            # Thông tin sản phẩm
                            if item.get('price'):
                                st.metric("Giá", f"{item['price']:,}đ")
                            if item.get('brand'):
                                st.write(f"🏷️ **Thương hiệu:** {item['brand']}")
                            if item.get('average_rating'):
                                st.write(f"⭐ **Đánh giá:** {item['average_rating']}/5")
                            st.metric("Độ liên quan", f"{item.get('score', 0):.1%}")
                        
                        st.divider()
            
            with tab2:
                # Hiển thị dạng bảng
                df_results = pd.DataFrame(results)
                if not df_results.empty:
                    # Làm tròn score
                    if 'score' in df_results.columns:
                        df_results['score'] = df_results['score'].round(3)
                    
                    # Cắt ngắn mô tả
                    if 'descriptioninfo' in df_results.columns:
                        df_results['descriptioninfo'] = df_results['descriptioninfo'].apply(
                            lambda x: x[:100] + "..." if len(str(x)) > 100 else x
                        )
                    
                    # Thêm cột chunks info
                    if 'total_chunks_found' in df_results.columns:
                        df_results['chunks'] = df_results['total_chunks_found']
                    
                    # Chọn các cột hiển thị
                    display_columns = ['name', 'brand', 'price', 'score', 'chunks', 'descriptioninfo']
                    display_df = df_results[[col for col in display_columns if col in df_results.columns]]
                    
                    st.dataframe(
                        display_df,
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Nút download
                    csv = df_results.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 Tải xuống CSV",
                        data=csv,
                        file_name=f"chunked_search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            
            with tab3:
                # Phân tích kết quả
                if results:
                    scores = [item.get('score', 0) for item in results]
                    chunks_counts = [item.get('total_chunks_found', 1) for item in results]
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Điểm cao nhất", f"{max(scores):.3f}")
                    with col2:
                        st.metric("Điểm trung bình", f"{sum(scores)/len(scores):.3f}")
                    with col3:
                        st.metric("Tổng chunks", sum(chunks_counts))
                    with col4:
                        st.metric("TB chunks/SP", f"{sum(chunks_counts)/len(chunks_counts):.1f}")
                    
                    # Biểu đồ điểm số
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Điểm tương đồng**")
                        chart_data = pd.DataFrame({
                            'Sản phẩm': [f"#{i+1}" for i in range(len(results))],
                            'Điểm tương đồng': scores
                        })
                        st.bar_chart(chart_data.set_index('Sản phẩm'))
                    
                    with col2:
                        st.markdown("**Số chunks tìm thấy**")
                        chunk_chart_data = pd.DataFrame({
                            'Sản phẩm': [f"#{i+1}" for i in range(len(results))],
                            'Số chunks': chunks_counts
                        })
                        st.bar_chart(chunk_chart_data.set_index('Sản phẩm'))
        else:
            st.warning("🤷‍♂️ Không tìm thấy kết quả nào phù hợp.")
    else:
        st.warning("⚠️ Vui lòng nhập từ khóa tìm kiếm.")

# Lịch sử tìm kiếm
if st.session_state.search_history:
    st.markdown("### 📚 Lịch sử tìm kiếm")
    
    # Hiển thị lịch sử dạng chips
    cols = st.columns(min(len(st.session_state.search_history), 5))
    for i, query in enumerate(st.session_state.search_history[:5]):
        with cols[i]:
            if st.button(f"🔄 {query}", key=f"history_{i}"):
                st.session_state.search_query = query
                st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>🚀 <strong>Products Finder</strong> - Powered by AI, Vector Search & Text Chunking</p>
    <p>Được phát triển với ❤️ bằng Streamlit & FastAPI</p>
    <p><small>✨ Phiên bản Chunked - Tìm kiếm chính xác hơn với mô tả dài</small></p>
</div>
""", unsafe_allow_html=True)