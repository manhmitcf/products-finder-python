import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime
import time

# Cấu hình trang
st.set_page_config(
    page_title="Products Finder - Tìm kiếm sản phẩm thông minh",
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
    .sidebar-info {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Hàm gọi API
def search_products(query, limit=5, api_url="http://localhost:8000"):
    """Gọi API để tìm kiếm sản phẩm"""
    try:
        response = requests.post(
            f"{api_url}/search",
            json={"text": query, "limit": limit},
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

# Hàm kiểm tra trạng thái API
def check_api_status(api_url="http://localhost:8000"):
    """Kiểm tra xem API có hoạt động không"""
    try:
        response = requests.get(f"{api_url}/docs", timeout=5)
        return response.status_code == 200
    except:
        return False

# Header chính
st.markdown('<h1 class="main-header">🔍 Products Finder</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Tìm kiếm sản phẩm thông minh với công nghệ AI</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown('<div class="sidebar-info">', unsafe_allow_html=True)
    st.markdown("### ⚙️ Cấu hình")
    
    # Cấu hình API URL
    api_url = st.text_input(
        "🌐 API URL", 
        value="http://localhost:8000",
        help="URL của API server"
    )
    
    # Số lượng kết quả
    limit = st.slider(
        "📊 Số kết quả tối đa", 
        min_value=1, 
        max_value=20, 
        value=5,
        help="Số lượng sản phẩm tối đa muốn hiển thị"
    )
    
    # Kiểm tra trạng thái API
    st.markdown("### 🔌 Trạng thái API")
    if st.button("Kiểm tra kết nối"):
        with st.spinner("Đang kiểm tra..."):
            if check_api_status(api_url):
                st.success("✅ API hoạt động bình thường")
            else:
                st.error("❌ Không thể kết nối đến API")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Thông tin hướng dẫn
    st.markdown("### 📖 Hướng dẫn sử dụng")
    st.markdown("""
    1. **Nhập từ khóa** tìm kiếm vào ô bên dưới
    2. **Nhấn Enter** hoặc click nút Tìm kiếm
    3. **Xem kết quả** được sắp xếp theo độ liên quan
    4. **Click vào link** để xem chi tiết sản phẩm
    """)
    
    # Ví dụ tìm kiếm
    st.markdown("### 💡 Ví dụ tìm kiếm")
    example_queries = [
        "điện thoại smartphone",
        "laptop gaming",
        "tai nghe bluetooth",
        "đồng hồ thông minh",
        "camera chụp ảnh"
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
        placeholder="Ví dụ: điện thoại iPhone, laptop Dell, tai nghe Sony...",
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
        with st.spinner(f"🔍 Đang tìm kiếm '{search_query}'..."):
            results, error = search_products(search_query, limit, api_url)
        
        if error:
            st.error(f"❌ {error}")
            
            # Gợi ý khắc phục
            st.markdown("### 🛠️ Cách khắc phục:")
            st.markdown("""
            1. **Kiểm tra API server**: Đảm bảo API đang chạy tại `http://localhost:8000`
            2. **Chạy API**: Sử dụng lệnh `uvicorn main:app --reload` hoặc `docker-compose up`
            3. **Kiểm tra URL**: Đảm bảo URL API trong sidebar là chính xác
            """)
            
        elif results:
            # Hiển thị kết quả
            st.success(f"✅ Tìm thấy {len(results)} kết quả cho '{search_query}'")
            
            # Tabs cho các cách hiển thị khác nhau
            tab1, tab2, tab3 = st.tabs(["📋 Danh sách", "📊 Bảng dữ liệu", "📈 Phân tích"])
            
            with tab1:
                # Hiển thị dạng card
                for i, item in enumerate(results, 1):
                    with st.container():
                        st.markdown(f"""
                        <div class="result-card">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <h3 style="margin: 0; color: #1f77b4;">#{i} {item.get('name', 'Không có tên')}</h3>
                                <span class="score-badge">Điểm: {item.get('score', 0):.3f}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Thông tin chi tiết
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            if item.get('descriptioninfo'):
                                st.write("📝 **Mô tả:**", item['descriptioninfo'][:200] + "..." if len(item.get('descriptioninfo', '')) > 200 else item.get('descriptioninfo', ''))
                            
                            if item.get('url'):
                                st.markdown(f"🔗 [Xem chi tiết sản phẩm]({item['url']})")
                        
                        with col2:
                            # Thêm các thông tin khác nếu có
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
                    
                    st.dataframe(
                        df_results,
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Nút download
                    csv = df_results.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 Tải xuống CSV",
                        data=csv,
                        file_name=f"search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            
            with tab3:
                # Phân tích kết quả
                if results:
                    scores = [item.get('score', 0) for item in results]
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Điểm cao nhất", f"{max(scores):.3f}")
                    
                    with col2:
                        st.metric("Điểm trung bình", f"{sum(scores)/len(scores):.3f}")
                    
                    with col3:
                        st.metric("Điểm thấp nhất", f"{min(scores):.3f}")
                    
                    # Biểu đồ điểm số
                    chart_data = pd.DataFrame({
                        'Sản phẩm': [f"#{i+1}" for i in range(len(results))],
                        'Điểm tương đồng': scores
                    })
                    
                    st.bar_chart(chart_data.set_index('Sản phẩm'))
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
    <p>🚀 <strong>Products Finder</strong> - Powered by AI & Vector Search</p>
    <p>Được phát triển với ❤️ bằng Streamlit & FastAPI</p>
</div>
""", unsafe_allow_html=True)