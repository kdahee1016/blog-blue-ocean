import streamlit as st
import google.generativeai as genai
import time

# 페이지 설정
st.set_page_config(page_title="오키랑의 블로그 초안 생성기", layout="centered")

# CSS로 모바일 가독성 스타일 살짝 추가
st.markdown("""
    <style>
    .reportview-container .main .block-container { max-width: 800px; }
    .stButton>button { width: 100%; border-radius: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📝 오키랑의 블로그 초안 메이커")
st.caption("키워드만 넣으면 SEO에 최적화된 일기체 원고를 작성해 드려요!")

# 사이드바: 설정
with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input("Gemini API Key를 입력하세요", type="password")
    st.info("API 키는 Google AI Studio에서 무료로 발급 가능합니다.")

# 메인 화면: 입력 폼
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        main_k = st.text_input("📍 메인 키워드 (4회 반복)", placeholder="예: 파스타맛집")
    with col2:
        sub_k1 = st.text_input("🔍 서브 키워드 1", placeholder="예: 아이랑 가기 좋은")
        
    col3, col4 = st.columns(2)
    with col3:
        sub_k2 = st.text_input("🔍 서브 키워드 2", placeholder="예: 무한리필")
    with col4:
        sub_k3 = st.text_input("🔍 서브 키워드 3", placeholder="예: 내돈내산 후기")

# 실행 버튼
if st.button("✨ 블로그 초안 생성하기"):
    if not api_key:
        st.error("API 키를 입력해주세요!")
    elif not main_k:
        st.warning("메인 키워드는 필수입니다.")
    else:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro')
            
            with st.spinner("30대 감성을 한 방울 섞어 글을 짓는 중입니다..."):
                prompt = f"""
                주제: {main_k} (서브: {sub_k1}, {sub_k2}, {sub_k3})
                네이버 블로그 원고를 작성해줘. 아래 조건을 엄격히 지켜줘:

                1. 키워드: '{main_k}' 4회, '{sub_k1}', '{sub_k2}', '{sub_k3}' 각 1회 자연스럽게 포함.
                2. 제목: 클릭율 높이는 제목 3개 추천.
                3. 말투: 30대 여성의 일기체 (~했음, ~했다, 혼잣말). 친근하고 편안하게.
                4. 가독성: 한 줄에 공백포함 최대 60-70byte 내외로 끊어서 작성(모바일 최적화).
                5. 이모티콘: 리스트 중 5~6개 필수 사용 !(•̀ᴗ•́)و ̑̑ , (*ᴗ͈ˬᴗ͈)ꕤ*.ﾟ , (୨୧ ❛ᴗ❛)✧ , (୨୧ •͈ᴗ•͈) , (•̆ꈊ•̆ ) , (ꈍᴗꈍ)♡ ,  ̗̀ෆ(˶'ᵕ'˶)ෆ ̖́- , ٩(*•̀ᴗ•́*)و /,٩( ᐢ-ᐢ ), / ٩(๑❛ᴗ❛๑)۶♡ , ٩(◕ᗜ◕)و , ദ്ദി( ¯꒳¯ ) , ☆٩(｡•ω<｡)﻿و , :) , :D , >_< , +ㅂ+ 등).
                6. 이모지: 문맥에 맞는 그림 이모지 8개 내외 활용.
                7. AI가 쓴 것 같지 않도록 작성하되 중복문서 걸리지 않게 이중검토
                8. 분량: 한글 기준 약 3,500자 내외로 아주 상세하게.
                9. 상위노출SEO 반영해서 내용 작성
                10. 요약문: 최상단에 240~280byte 요약문 포함.
                """
                
                response = model.generate_content(prompt)
                full_text = response.text
                
                st.success("🎉 원고 작성이 완료되었습니다!")
                st.divider()
                
                # 결과 출력 및 복사 기능
                st.subheader("📋 생성된 블로그 원고")
                st.text_area("결과물 (드래그해서 복사하세요)", value=full_text, height=600)
                
                st.download_button(
                    label="💾 텍스트 파일로 다운로드",
                    data=full_text,
                    file_name=f"{main_k}_블로그초안.txt",
                    mime="text/plain"
                )
                
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
