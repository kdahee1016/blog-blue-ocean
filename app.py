import streamlit as st
import google.generativeai as genai

# 원고와 이미지를 갈라줄 고유 태그
SPLIT_TAG = "[[SPLIT_HERE_FOR_IMAGES]]"

# 페이지 설정
st.set_page_config(page_title="오키랑의 블로그 메이커", layout="centered")

# --- 세션 상태 초기화 ---
if "blog_script" not in st.session_state:
    st.session_state.blog_script = ""
if "image_prompts" not in st.session_state:
    st.session_state.image_prompts = []

st.title("📝 내 경험과 이미지가 담긴 블로그 초안 생성기")
st.caption("직접 겪은 에피소드를 적어주시면 자연스러운 감성으로 맛있게 버무려 드려요! ✨")

# 사이드바: 설정
with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input("Gemini API Key를 입력하세요", type="password")

# --- 자동 모델 선택 함수 ---
def get_available_model():
    try:
        # 내 API 키로 사용 가능한 모델 목록을 가져옵니다.
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # 선호하는 모델 순서 (최신 순)
        priority_list = [
            "models/gemini-1.5-flash", 
            "models/gemini-1.5-flash-latest", 
            "models/gemini-pro"
        ]
        for model_path in priority_list:
            if model_path in available_models:
                return genai.GenerativeModel(model_path)
        # 목록에 없으면 첫 번째 사용 가능한 모델 반환
        return genai.GenerativeModel(available_models[0])
    except:
        # 오류 발생 시 가장 기본 모델명 시도
        return genai.GenerativeModel("gemini-pro")

# 메인 화면: 입력 폼
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        main_k = st.text_input("📍 메인 키워드", placeholder="예: 영화 ㅇㅇㅇ 후기")
    with col2:
        sub_k1 = st.text_input("🔍 서브 키워드 1")
        
    col3, col4 = st.columns(2)
    with col3:
        sub_k2 = st.text_input("🔍 서브 키워드 2")
    with col4:
        sub_k3 = st.text_input("🔍 서브 키워드 3")

    st.subheader("📸 나의 실제 경험 (흐름 적기)")
    user_experience = st.text_area("블로그에 꼭 넣고 싶은 내용이나 흐름을 자유롭게 적어주세요.", height=150)

    st.subheader("🖼️ 필요한 이미지 목록")
    image_requests = st.text_input("이미지 주제들을 적어주세요.", placeholder="예: 30대 부모와 아이가 영화보는 모습 등")

# --- 버튼 레이아웃 ---
if st.button("✨ 원고 & 이미지 전체 생성", use_container_width=True):
    if not api_key or not main_k:
        st.warning("API 키와 메인 키워드를 확인해주세요.")
    else:
        try:
            genai.configure(api_key=api_key)
            model = get_available_model() # 자동 모델 선택 적용

            image_instruction = ""
            if image_requests.strip():
                image_instruction = f"원고 작성이 완전히 끝나면 반드시 '{SPLIT_TAG}'라는 문구를 한 줄 쓰고, 그 아래에 '{image_requests}'에 대한 Bing용 영어 프롬프트를 번호 붙여 상세히 작성해줘."

            prompt_text = (
                f"주제: {main_k} (서브: {sub_k1}, {sub_k2}, {sub_k3})\n"
                f"내용: {user_experience}\n\n"
                "[지시사항]\n1. 아래 양식에 맞춰 네이버 블로그 원고를 작성해줘.\n"
                f"2. {image_instruction}\n\n"
                "[원고 조건]\n"
                f"1. 키워드: '{main_k}' 4회, '{sub_k1}', '{sub_k2}', '{sub_k3}' 각 1회 자연스럽게 포함.\n"
                "2. 제목: 상위노출 될 수 있는 제목 3개 추천.\n"
                "3. 말투: 30대 여성의 일기체 (~했음, ~했다, 혼잣말). 친근하고 편안하게.\n"
                "4. 가독성: 한 줄에 공백포함 최대 60-70byte 내외로 끊어서 작성(모바일 최적화).\n"
                "5. 이모티콘: 리스트 중 5~6개 필수 사용 (!(•̀ᴗ•́)و ̑̑ , (*ᴗ͈ˬᴗ͈)ꕤ*.ﾟ , (୨୧ ❛ᴗ❛)✧ , (୨୧ •͈ᴗ•͈) , (•̆ꈊ•̆ ) , (ꈍᴗꈍ)♡ , ̗̀ෆ(˶'ᵕ'˶)ෆ ̖́- , ٩(*•̀ᴗ•́*)و /, ٩( ᐢ-ᐢ ), / ٩(๑❛ᴗ❛๑)۶♡ , ٩(◕ᗜ◕)و , ദ്디( ¯꒳¯ ) , ☆٩(｡•ω<｡)﻿و , :) , :D , >_< , +ㅂ+ 등).\n"
                "6. 이모지: 문맥에 맞는 그림 이모지 10개 내외 활용.\n"
                "7. AI가 쓴 것 같지 않도록 작성하되 중복문서 걸리지 않게 이중검토\n"
                "8. 분량: 한글 기준 약 3,500자 내외로 아주 상세하게.\n"
                "9. 상위노출SEO 반영해서 소제목 및 본문 작성\n"
                "10. 흐름에 맞춰 소제목 넣기 (그림이모지1개+소제목)\n"
                "11. 요약문: 최상단에 240~280byte 요약문 포함."
            )
            
            with st.spinner("원고와 이미지를 준비 중입니다!"):
                response = model.generate_content(prompt_text)
                res_text = response.text
                if SPLIT_TAG in res_text:
                    st.session_state.blog_script, raw_
