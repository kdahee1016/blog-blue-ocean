import streamlit as st

st.set_page_config(page_title="키워드 분석기", layout="wide")

st.title("🔍 블로그 키워드 분석기")
st.write("---")

# 사이드바 설정
st.sidebar.success("키워드 분석 페이지로 이동했습니다.")

# 카테고리 선택
category = st.selectbox(
    "관심 있는 카테고리를 선택하세요",
    ["국내여행", "해외여행", "육아", "초등학생", "스포츠(야구)", "도서", "영화"]
)

# 검색창
keyword = st.text_input(f"[{category}] 관련해서 분석하고 싶은 키워드를 입력하세요")

if st.button("데이터 분석 시작"):
    st.info(f"'{keyword}' 키워드에 대한 네이버 데이터를 불러오는 중입니다...")
    # 여기에 나중에 API 연동 코드를 넣으면 됩니다!
