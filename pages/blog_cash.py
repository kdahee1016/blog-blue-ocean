import streamlit as st
import google.generativeai as genai
import re

# 원고와 이미지를 갈라줄 고유 태그
SPLIT_TAG = "[[SPLIT_HERE_FOR_IMAGES]]"

# 페이지 설정
st.set_page_config(page_title="커스텀 블로그 메이커", layout="centered")

# --- 세션 상태 초기화 ---
if "blog_script" not in st.session_state:
    st.session_state.blog_script = ""
if "image_prompts" not in st.session_state:
    st.session_state.image_prompts = []

st.title("📝 커스텀 블로그 초안 생성기")
st.caption("공백 제외 글자 수 체크 기능이 추가되었습니다! ✨")

# 사이드바: 설정
with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input("Gemini API Key를 입력하세요", type="password")
    
    st.divider()
    st.subheader("🛠️ 세부 옵션")
    # 1. 공백 제외 글자수 설정
    target_length = st.slider("목표 글자 수 (공백 제외)", min_value=300, max_value=2500, value=1100, step=100)
    
    # 2. 말투 선택
    tone_style = st.selectbox("말투 선택", [
        "30대 여성의 간결한 혼잣말 일기체 (~했음, ~임)",
        "친절하고 부드러운 경어체 (~해요, ~했습니다)",
        "신뢰감 있는 전문적인 정보전달체 (~입니다, ~합니다)",
        "톡톡 튀는 MZ 세대 말투"
    ])
    
    # 3. 특수문자 이모티콘 활용 여부
    use_emoticons = st.checkbox("특수문자 이모티콘 활용", value=True)

# --- 자동 모델 선택 함수 ---
def get_available_model():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        priority_list = ["models/gemini-1.5-flash", "models/gemini-pro"]
        for model_path in priority_list:
            if model_path in available_models:
                return genai.GenerativeModel(model_path)
        return genai.GenerativeModel(available_models[0])
    except:
        return genai.GenerativeModel("gemini-pro")

# 메인 화면: 입력 폼
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        main_k = st.text_input("📍 메인 키워드", placeholder="예: 맛집 탐방")
    with col2:
        sub_k1 = st.text_input("🔍 서브 키워드 1")
    with col2:
        sub_k1 = st.text_input("🔍 서브 키워드 2")
    with col2:
        sub_k1 = st.text_input("🔍 서브 키워드 3")
    
    user_experience = st.text_area("📸 나의 실제 경험", height=150)
    image_requests = st.text_input("🖼️ 필요한 이미지 목록")

# --- 생성 버튼 ---
if st.button("✨ 블로그 원고 생성하기", use_container_width=True):
    if not api_key or not main_k:
        st.error("API 키와 메인 키워드를 확인해주세요.")
    else:
        try:
            genai.configure(api_key=api_key)
            model = get_available_model()

            emo_instruction = "특수문자 이모티콘을 적극 활용해줘." if use_emoticons else "특수문자 이모티콘은 사용하지 마."

            prompt_text = (
                f"주제: {main_k} (서브 키워드 포함)\n"
                f"내용: {user_experience}\n\n"
                f"[조건]\n"
                f"- 전체 본문 분량: 반드시 '공백을 제외하고' {target_length}자 내외로 작성할 것.\n"
                f"- 말투: {tone_style}\n"
                f"- 이모티콘: {emo_instruction}\n"
                f"- 구성: 제목 3개, 요약문, 본문, 해시태그 순서로 작성.\n"
                f"마지막에 '{SPLIT_TAG}'를 쓰고 '{image_requests}'에 대한 영어 프롬프트를 써줘."
            )

            with st.spinner("원고 작성 중..."):
                response = model.generate_content(prompt_text)
                res_text = response.text
                
                if SPLIT_TAG in res_text:
                    parts = res_text.split(SPLIT_TAG)
                    st.session_state.blog_script = parts[0].strip()
                    st.session_state.image_prompts = [line.strip() for line in parts[1].strip().split('\n') if len(line) > 5]
                else:
                    st.session_state.blog_script = res_text.strip()
        except Exception as e:
            st.error(f"오류: {str(e)}")

# --- 결과 출력 및 글자 수 카운터 ---
if st.session_state.blog_script:
    st.divider()
    
    # 글자 수 계산 (공백 제외)
    text_content = st.session_state.blog_script
    char_count_with_spaces = len(text_content)
    char_count_no_spaces = len(re.sub(r'\s', '', text_content)) # 정규표현식으로 모든 공백 제거 후 카운트
    
    st.subheader("📋 생성된 블로그 원고")
    
    # 글자 수 지표 표시
    c1, c2 = st.columns(2)
    c1.metric("공백 포함", f"{char_count_with_spaces}자")
    c2.metric("공백 제외 (실제 분량)", f"{char_count_no_spaces}자", 
              delta=f"{char_count_no_spaces - target_length}자" if target_length else None)

    st.text_area("내용 확인 및 수정", value=text_content, height=400)
    
    # 복사 버튼 (이전과 동일)
    safe_text = text_content.replace('`','\\`').replace('$','\\$').replace('\n','\\n')
    st.components.v1.html(f"""
        <script>
        function copyText() {{
            const el = document.createElement('textarea');
            el.value = `{safe_text}`;
            document.body.appendChild(el);
            el.select();
            document.execCommand('copy');
            document.body.removeChild(el);
            alert('복사되었습니다!');
        }}
        </script>
        <button onclick="copyText()" style="width:100%; height:45px; background-color:#4CAF50; color:white; border:none; border-radius:10px; cursor:pointer; font-weight:bold;">📋 원고 전체 복사하기</button>
    """, height=50)
