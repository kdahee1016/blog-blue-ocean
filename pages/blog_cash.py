import streamlit as st
import google.generativeai as genai
import re

# 원고와 이미지를 갈라줄 고유 태그
SPLIT_TAG = "[[SPLIT_HERE_FOR_IMAGES]]"

st.set_page_config(page_title="오키랑의 프로 블로그 메이커", layout="centered")

# --- 세션 상태 초기화 ---
if "blog_script" not in st.session_state:
    st.session_state.blog_script = ""

# --- 글자 수 계산 함수 (고정 태그 기준) ---
def get_clean_char_count(text):
    # [요약문] 내용 추출
    summary_part = re.search(r"\[요약문\](.*?)(\[본문\]|\[해시태그\]|$)", text, re.DOTALL)
    summary_txt = summary_part.group(1).strip() if summary_part else ""
    
    # [본문] 내용 추출
    body_part = re.search(r"\[본문\](.*?)(\[해시태그\]|$)", text, re.DOTALL)
    body_txt = body_part.group(1).strip() if body_part else ""
    
    # 두 섹션 합쳐서 공백 제거 카운트
    combined = summary_txt + body_txt
    count = len(re.sub(r'\s', '', combined))
    return count

st.title("📝 프로 블로그 초안 생성기")
st.caption("키워드 반복 횟수와 섹션별 글자 수까지 완벽하게 관리합니다. ✨")

# 사이드바: 상세 설정
with st.sidebar:
    st.header("⚙️ 설정 및 옵션")
    api_key = st.text_input("Gemini API Key", type="password")
    
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

# 메인 화면: 키워드 및 내용 입력
with st.container():
    st.subheader("🔑 키워드 설정")
    main_k = st.text_input("📍 메인 키워드 (본문 4회 노출)", placeholder="예: 성수동 맛집 추천")
    
    col1, col2 = st.columns(2)
    with col1:
        sub_k1 = st.text_input("🔍 서브 키워드 1")
        sub_k2 = st.text_input("🔍 서브 키워드 2")
    with col2:
        sub_k3 = st.text_input("🔍 서브 키워드 3")
        sub_k4 = st.text_input("🔍 서브 키워드 4")
    
    st.divider()
    user_exp = st.text_area("📸 실제 경험 및 흐름", height=150, placeholder="직접 겪은 에피소드를 적어주세요.")
    img_req = st.text_input("🖼️ 필요한 이미지 목록", placeholder="예: 카페 외관, 커피 근접샷 등")

# --- 생성 버튼 로직 ---
if st.button("✨ 맞춤 원고 생성하기", use_container_width=True):
    if not api_key or not main_k:
        st.error("API 키와 메인 키워드는 필수입니다.")
    else:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            emo_instruction = "특수문자 이모티콘을 문장 중간중간에 5~8개 적절히 섞어줘." if use_emo else "특수문자 이모티콘은 절대 사용하지 마."
            
            prompt = f"""
            주제: {main_k}
            서브 키워드: {sub_k1}, {sub_k2}, {sub_k3}, {sub_k4}
            내용: {user_exp}

            [작성 규칙 - 절대 엄수]
            1. 아래 고정 태그 형식을 반드시 유지할 것:
               [제목추천] / [요약문] / [본문] / [해시태그]
            
            2. 키워드 빈도:
               - 메인 키워드 '{main_k}'는 본문에 자연스럽게 '4회' 이상 언급.
               - 서브 키워드 '{sub_k1}', '{sub_k2}', '{sub_k3}', '{sub_k4}'는 본문에 각 '1회' 이상 언급.

            3. 분량 및 말투:
               - [요약문]과 [본문]의 총 합계가 '공백 제외 {target_len}자' 내외가 되도록 상세히 작성.
               - 말투: {tone_choice}
               - 이모티콘: {emo_instruction}
               - 가독성을 위해 소제목을 활용하고 문장을 짧게 끊어서 작성.

            4. 이미지 프롬프트:
               - 모든 작성이 끝나면 '{SPLIT_TAG}'를 쓰고 '{img_req}'에 대한 영어 이미지 프롬프트 3개를 작성.
            """
            
            with st.spinner("키워드와 분량을 맞추어 정성껏 작성 중입니다..."):
                response = model.generate_content(prompt)
                st.session_state.blog_script = response.text
        except Exception as e:
            st.error(f"오류: {e}")

# --- 결과 출력 영역 ---
if st.session_state.blog_script:
    res_parts = st.session_state.blog_script.split(SPLIT_TAG)
    blog_content = res_parts[0].strip()
    
    # 정밀 카운팅
    pure_count = get_clean_char_count(blog_content)
    
    st.divider()
    st.subheader("📊 원고 분석 리포트")
    c1, c2, c3 = st.columns(3)
    c1.metric("체크된 글자 수", f"{pure_count}자", help="[요약문]과 [본문] 섹션의 공백 제외 글자수입니다.")
    c2.metric("목표 글자 수", f"{target_len}자")
    c3.metric("차이", f"{pure_count - target_len}자")

    st.subheader("📋 생성된 블로그 원고")
    st.text_area("전체 원고 내용", value=blog_content, height=500)
    
    # 이미지 프롬프트 출력
    if len(res_parts) > 1:
        st.divider()
        st.subheader("🖼️ 이미지 생성 프롬프트")
        st.info(res_parts[1].strip())
