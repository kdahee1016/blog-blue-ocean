import streamlit as st
import google.generativeai as genai
import re

st.set_page_config(page_title="오키랑의 프로 블로그 메이커", layout="centered")

# --- 세션 상태 초기화 ---
if "blog_script" not in st.session_state:
    st.session_state.blog_script = ""

# --- [중요] 모델 호출 오류 해결 로직 ---
def generate_content_safe(api_key, prompt):
    genai.configure(api_key=api_key)
    
    # 가장 오류가 적은 모델 명칭 순서대로 시도
    # 1. flash 최신버전 2. flash 일반 3. pro 버전
    model_list = ['gemini-1.5-flash', 'gemini-1.5-flash-latest', 'gemini-pro']
    
    last_error = None
    for model_name in model_list:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            last_error = e
            continue
            
    # 모든 모델 시도 실패 시 에러 메시지 상세 출력
    raise Exception(f"모델 연결 실패. (마지막 에러: {str(last_error)}) \nAPI 키가 활성화되었는지, 할당량이 남았는지 확인해주세요.")

# --- 글자 수 계산 함수 ---
def get_clean_char_count(text):
    summary_part = re.search(r"\[요약문\](.*?)(\[본문\]|\[해시태그\]|$)", text, re.DOTALL)
    summary_txt = summary_part.group(1).strip() if summary_part else ""
    
    body_part = re.search(r"\[본문\](.*?)(\[해시태그\]|$)", text, re.DOTALL)
    body_txt = body_part.group(1).strip() if body_part else ""
    
    combined = summary_txt + body_txt
    count = len(re.sub(r'\s', '', combined))
    return count

st.title("📝 프로 블로그 초안 생성기")
st.caption("오류 발생 가능성을 최소화한 안정화 버전입니다. ✨")

# 사이드바: 설정
with st.sidebar:
    st.header("⚙️ 설정 및 옵션")
    api_key = st.text_input("Gemini API Key", type="password", help="Google AI Studio에서 발급받은 키를 입력하세요.")
    
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

# 메인 화면: 키워드 입력
with st.container():
    st.subheader("🔑 키워드 설정")
    main_k = st.text_input("📍 메인 키워드 (본문 4회 노출)", placeholder="예: 제주도 가볼만한곳")
    
    col1, col2 = st.columns(2)
    with col1:
        sub_k1 = st.text_input("🔍 서브 키워드 1")
        sub_k2 = st.text_input("🔍 서브 키워드 2")
    with col2:
        sub_k3 = st.text_input("🔍 서브 키워드 3")
        sub_k4 = st.text_input("🔍 서브 키워드 4")
    
    st.divider()
    user_exp = st.text_area("📸 실제 경험 및 흐름", height=200, placeholder="구체적인 에피소드를 적어주세요.")

# --- 생성 버튼 ---
if st.button("✨ 맞춤 원고 생성하기", use_container_width=True):
    if not api_key or not main_k:
        st.error("API 키와 메인 키워드를 입력해 주세요.")
    else:
        try:
            emo_instruction = "상황에 맞는 특수문자 이모티콘을 5~8개 정도 적절히 섞어줘." if use_emo else "특수문자 이모티콘은 절대 사용하지 마."
            
            prompt = f"""
            주제: {main_k}
            서브 키워드: {sub_k1}, {sub_k2}, {sub_k3}, {sub_k4}
            내용: {user_exp}

            [작성 규칙 - 절대 엄수]
            1. 섹션 태그 고정: [제목추천], [요약문], [본문], [해시태그]
            2. 키워드 빈도: 메인 키워드 '{main_k}'는 4회 이상, 서브 키워드들은 각 1회 이상 본문에 포함.
            3. 분량: [요약문]과 [본문] 섹션의 합계가 '공백 제외 {target_len}자' 내외가 되도록 작성.
            4. 말투: {tone_choice}
            5. 이모티콘: {emo_instruction}
            """
            
            with st.spinner("AI가 원고를 작성 중입니다..."):
                # 수정된 안전 호출 함수 사용
                result_text = generate_content_safe(api_key, prompt)
                st.session_state.blog_script = result_text
                
        except Exception as e:
            st.error(f"⚠️ 오류가 발생했습니다: {e}")

# --- 결과 영역 ---
if st.session_state.blog_script:
    blog_content = st.session_state.blog_script.strip()
    pure_count = get_clean_char_count(blog_content)
    
    st.divider()
    st.subheader("📊 원고 분석 리포트")
    c1, c2, c3 = st.columns(3)
    c1.metric("체크된 글자 수", f"{pure_count}자")
    c2.metric("목표 글자 수", f"{target_len}자")
    c3.metric("차이", f"{pure_count - target_len}자")

    st.subheader("📋 생성된 블로그 원고")
    st.text_area("내용 (드래그하여 복사)", value=blog_content, height=500)
