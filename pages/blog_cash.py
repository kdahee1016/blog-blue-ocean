import streamlit as st
import google.generativeai as genai
import re

st.set_page_config(page_title="오키랑의 프로 블로그 메이커", layout="centered")

# --- 세션 상태 초기화 ---
if "blog_script" not in st.session_state:
    st.session_state.blog_script = ""

# --- [안정성 검증된] 자동 모델 선택 함수 ---
def get_available_model():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        priority_list = ["models/gemini-1.5-flash", "models/gemini-1.5-flash-latest", "models/gemini-pro"]
        for model_path in priority_list:
            if model_path in available_models:
                return genai.GenerativeModel(model_path)
        return genai.GenerativeModel(available_models[0])
    except:
        return genai.GenerativeModel("gemini-pro")

# --- 글자 수 계산 함수 (공백 제외) ---
def get_clean_char_count(text):
    # [요약문]과 [본문] 섹션만 추출
    summary_part = re.search(r"\[요약문\](.*?)(\[본문\]|\[해시태그\]|$)", text, re.DOTALL)
    summary_txt = summary_part.group(1).strip() if summary_part else ""
    
    body_part = re.search(r"\[본문\](.*?)(\[해시태그\]|$)", text, re.DOTALL)
    body_txt = body_part.group(1).strip() if body_part else ""
    
    combined = summary_txt + body_txt
    count = len(re.sub(r'\s', '', combined))
    return count

st.title("📝 프로 블로그 초안 생성기")
st.caption("SEO 최적화 및 인간적인 서술 방식이 강화된 버전입니다. ✨")

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input("Gemini API Key를 입력하세요", type="password")
    
    st.divider()
    st.subheader("📏 분량 및 스타일")
    target_len = st.slider("목표 글자 수 (요약+본문, 공백제외)", 500, 3000, 1100, 100)
    
    tone_choice = st.selectbox("말투 선택", [
        "30대 여성의 간결한 혼잣말 일기체 (~했음, ~였다, ~임)",
        "친절하고 부드러운 경어체 (~해요, ~했습니다, ~인가요?)",
        "신뢰감 있는 전문적인 정보전달체 (~입니다, ~합니다, ~가 특징입니다)",
        "톡톡 튀는 MZ세대 말투 (~용, 대박, 레알, 대확행 등 사용)"
    ])
    
    use_emo = st.checkbox("특수문자 이모티콘 활용 ( (•̀ᴗ•́)و 등 )", value=True)

# 메인 화면: 키워드 설정
with st.container():
    st.subheader("🔑 키워드 설정")
    main_k = st.text_input("📍 메인 키워드 (본문 4회 노출)", placeholder="예: 한남동 핫플레이스 탐방")
    
    col1, col2 = st.columns(2)
    with col1:
        sub_k1 = st.text_input("🔍 서브 키워드 1")
        sub_k2 = st.text_input("🔍 서브 키워드 2")
    with col2:
        sub_k3 = st.text_input("🔍 서브 키워드 3")
        sub_k4 = st.text_input("🔍 서브 키워드 4")
    
    st.divider()
    user_exp = st.text_area("📸 실제 경험 및 흐름", height=200, placeholder="구체적인 에피소드를 적어주세요.")

# --- 원고 생성 버튼 ---
if st.button("✨ 맞춤 원고 생성하기", use_container_width=True):
    if not api_key or not main_k:
        st.error("API 키와 메인 키워드를 입력해 주세요.")
    else:
        try:
            genai.configure(api_key=api_key)
            model = get_available_model()
            
            emo_instruction = "특수문자 이모티콘을 문장 중간중간에 5~8개 적절히 섞어줘." if use_emo else "특수문자 이모티콘은 절대 사용하지 마."
            
            prompt = f"""
            주제: {main_k}
            서브 키워드: {sub_k1}, {sub_k2}, {sub_k3}, {sub_k4}
            내용: {user_exp}

            [작성 규칙 - 절대 엄수]
            1. 아래 고정 태그 형식을 반드시 유지할 것:
               [제목 5개 추천] / [요약문] / [본문] / [해시태그]
            
            2. 키워드 빈도 및 SEO:
               - 메인 키워드 '{main_k}'는 본문에 자연스럽게 '4회' 이상 언급.
               - 서브 키워드 '{sub_k1}', '{sub_k2}', '{sub_k3}', '{sub_k4}'는 본문에 각 '1회' 이상 언급.
               - SEO 최적화를 위해 상단, 중단, 하단에 키워드를 고르게 배치하고 가독성 좋은 소제목을 필수로 사용할 것.

            3. 인간적인 서술 및 중복 방지 (매우 중요):
               - AI가 작성한 것처럼 느껴지는 상투적인 표현(예: '최근 ~가 각광받고 있습니다', '결론적으로 ~입니다')을 지양할 것.
               - 직접 겪은 듯한 생생한 묘사와 감정 표현을 듬뿍 담아 '인간적인 서술 방식'으로 작성할 것.
               - 유사 문서(중복 문서) 판독에 걸리지 않도록 문장 구조를 다채롭게 쓰고, 흔한 블로그 문구는 피할 것.

            4. 분량 및 말투:
               - [요약문]과 [본문]의 총 합계가 '공백 제외 {target_len}자' 내외가 되도록 상세히 작성.
               - 말투: {tone_choice}
               - 이모티콘: {emo_instruction}
            """
            
            with st.spinner("SEO 최적화 및 인간적인 서술을 반영하여 원고를 작성 중입니다..."):
                response = model.generate_content(prompt)
                st.session_state.blog_script = response.text
                
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")

# --- 결과 출력 영역 ---
if st.session_state.blog_script:
    blog_content = st.session_state.blog_script.strip()
    pure_count = get_clean_char_count(blog_content)
    
    st.divider()
    st.subheader("📊 원고 분석 리포트")
    c1, c2, c3 = st.columns(3)
    c1.metric("체크된 글자 수", f"{pure_count}자", help="[요약문]과 [본문] 섹션의 공백 제외 글자수입니다.")
    c2.metric("목표 글자 수", f"{target_len}자")
    c3.metric("차이", f"{pure_count - target_len}자")

    st.subheader("📋 생성된 블로그 원고")
    st.text_area("내용 확인 및 복사", value=blog_content, height=550)
