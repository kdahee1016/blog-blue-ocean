import streamlit as st
import google.generativeai as genai
import re

# 원고와 이미지를 갈라줄 고유 태그
SPLIT_TAG = "[[SPLIT_HERE_FOR_IMAGES]]"

st.set_page_config(page_title="정밀 글자수 블로그 메이커", layout="centered")

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
    return count, summary_txt, body_txt

st.title("📝 정밀 글자수 블로그 메이커")
st.caption("고정 태그 시스템으로 [요약문+본문] 글자 수만 정확히 계산합니다. 🎯")

with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input("Gemini API Key", type="password")
    st.divider()
    target_len = st.slider("목표 본문 글자 수 (공백 제외)", 300, 2500, 1100, 100)
    tone = st.selectbox("말투", ["일기체", "경어체", "정보전달체"])
    use_emo = st.checkbox("특수문자 이모티콘 활용", value=True)

# 입력 영역
main_k = st.text_input("📍 메인 키워드")
user_exp = st.text_area("📸 실제 경험 (흐름)", height=150)
img_req = st.text_input("🖼️ 이미지 목록")

if st.button("✨ 블로그 원고 생성", use_container_width=True):
    if not api_key or not main_k:
        st.error("API 키와 키워드를 확인해주세요.")
    else:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            emo_cmd = "특수문자 이모티콘((^o^), ٩(◕ᗜ◕)و 등) 적극 사용" if use_emo else "특수문자 이모티콘 금지"
            
            # 💡 [핵심] AI에게 고정 형식을 강제하는 프롬프트
            prompt = f"""
            주제: {main_k}
            내용: {user_exp}

            [작성 필수 규칙 - 아래 형식을 절대 엄수할 것]
            1. 모든 섹션은 반드시 대괄호 태그로 시작할 것.
            2. 형식:
            [제목추천]
            (여기에 제목 3개)
            
            [요약문]
            (여기에 요약 내용)
            
            [본문]
            (여기에 본문 내용)
            
            [해시태그]
            (여기에 태그 10개)

            [세부 조건]
            - [요약문]과 [본문]의 글자수 합계가 '공백 제외 {target_len}자' 내외가 되도록 작성.
            - 말투: {tone}
            - 이모티콘: {emo_cmd}
            - 마지막에 '{SPLIT_TAG}'를 쓰고 '{img_req}'에 대한 영어 프롬프트를 작성.
            """
            
            with st.spinner("형식에 맞춰 원고를 생성 중입니다..."):
                response = model.generate_content(prompt)
                st.session_state.blog_script = response.text
        except Exception as e:
            st.error(f"오류: {e}")

# 결과 출력
if st.session_state.blog_script:
    full_text = st.session_state.blog_script.split(SPLIT_TAG)[0].strip()
    
    # 정밀 카운팅 실행
    pure_count, s_txt, b_txt = get_clean_char_count(full_text)
    
    st.divider()
    st.subheader("📊 글자 수 리포트")
    
    # UI 개선: 메트릭으로 표시
    cols = st.columns(3)
    cols[0].metric("체크 대상 (요약+본문)", f"{pure_count}자")
    cols[1].metric("목표 글자 수", f"{target_len}자")
    cols[2].metric("차이", f"{pure_count - target_len}자")
    
    if pure_count < target_len * 0.9:
        st.warning("⚠️ 글자 수가 목표보다 부족합니다. 내용을 조금 더 보강하시는 것을 추천드려요!")

    st.subheader("📋 생성된 원고")
    st.text_area("내용 확인 (복사해서 사용하세요)", value=full_text, height=500)
