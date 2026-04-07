import streamlit as st
import google.generativeai as genai

# 원고와 이미지를 갈라줄 고유 태그
SPLIT_TAG = "[[SPLIT_HERE_FOR_IMAGES]]"

# 페이지 설정
st.set_page_config(page_title="커스텀 블로그 메이커", layout="centered")

# --- 세션 상태 초기화 ---
if "blog_script" not in st.session_state:
    st.session_state.blog_script = ""
if "image_prompts" not in st.session_state:
    st.session_state.image_prompts = []
if "full_prompt" not in st.session_state:
    st.session_state.full_prompt = ""

st.title("📝 커스텀 블로그 초안 생성기")
st.caption("글자 수, 말투, 이모티콘까지 내 마음대로 조절하는 블로그 메이커 ✨")

# 사이드바: 설정
with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input("Gemini API Key를 입력하세요", type="password")
    
    st.divider()
    st.subheader("🛠️ 세부 옵션")
    # 1. 글자수 입력칸 추가
    target_length = st.slider("목표 글자 수 (공백 포함)", min_value=500, max_value=3000, value=1500, step=100)
    
    # 2. 말투 선택 추가
    tone_style = st.selectbox("말투 선택", [
        "30대 여성의 간결한 혼잣말 일기체 (~했음, ~임)",
        "친절하고 부드러운 경어체 (~해요, ~했습니다)",
        "신뢰감 있는 전문적인 정보전달체 (~입니다, ~합니다)",
        "톡톡 튀는 MZ 세대 말투 (~함, 대박, 레알 등 사용)"
    ])
    
    # 3. 특수문자 이모티콘 활용 여부
    use_emoticons = st.checkbox("특수문자 이모티콘 활용 (예: (•̀ᴗ•́)و )", value=True)

# --- 자동 모델 선택 함수 ---
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

# 메인 화면: 입력 폼
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        main_k = st.text_input("📍 메인 키워드", placeholder="예: 제주도 맛집 탐방")
    with col2:
        sub_k1 = st.text_input("🔍 서브 키워드 1")
    
    col3, col4 = st.columns(2)
    with col3:
        sub_k2 = st.text_input("🔍 서브 키워드 2")
    with col4:
        sub_k3 = st.text_input("🔍 서브 키석드 3")
        
    user_experience = st.text_area("📸 나의 실제 경험 (흐름 적기)", height=150, placeholder="어디를 갔고, 무엇을 느꼈는지 자유롭게 적어주세요.")
    image_requests = st.text_input("🖼️ 필요한 이미지 목록", placeholder="예: 맛있는 음식 사진, 카페 내부 전경 등")

# --- 원고 & 이미지 전체 생성 버튼 ---
if st.button("✨ 블로그 원고 생성하기", use_container_width=True):
    if not api_key or not main_k:
        st.error("API 키와 메인 키워드를 확인해주세요.")
    else:
        try:
            genai.configure(api_key=api_key)
            model = get_available_model()

            image_instruction = ""
            if image_requests.strip():
                image_instruction = f"모든 작성이 끝나면 마지막에 '{SPLIT_TAG}'를 쓰고 '{image_requests}'에 대한 상세한 영어 이미지 프롬프트를 작성해."

            # 이모티콘 지시문 동적 생성
            emo_instruction = ""
            if use_emoticons:
                emo_instruction = "본문 중간중간에 상황에 맞는 특수문자 이모티콘을 5~10개 정도 섞어서 가독성을 높여줘. (예: (˶'ᵕ'˶), ٩(◕ᗜ◕)و, ദ്ദി( ¯꒳¯ ) 등)"
            else:
                emo_instruction = "특수문자 이모티콘(예: (^^), (>_<))은 절대 사용하지 말고 텍스트와 일반 이모지(😀, ✨)만 사용해줘."

            prompt_text = (
                f"주제: {main_k} (서브 키워드: {sub_k1}, {sub_k2}, {sub_k3})\n"
                f"사용자 경험: {user_experience}\n\n"
                f"[작성 지시사항]\n"
                f"1. 제목: 상위 노출을 위한 매력적인 제목 3개 추천\n"
                f"2. 요약문: 서론에 들어갈 짧은 요약 (3줄 이내)\n"
                f"3. 본문: 반드시 {target_length}자 내외로 상세하게 작성할 것.\n"
                f"4. 말투: {tone_style}로 작성할 것.\n"
                f"5. 이모티콘: {emo_instruction}\n"
                f"6. 키워드 삽입: 메인 키워드 '{main_k}'를 자연스럽게 4회 이상 반복.\n"
                f"7. 해시태그: 관련 해시태그 10개 포함.\n"
                f"8. 가독성: 소제목을 사용하고 문단을 자주 나누어 모바일에서 보기 편하게 작성.\n"
                f"{image_instruction}\n"
            )
            
            st.session_state.full_prompt = prompt_text # 리트라이 대비 저장

            with st.spinner("맞춤형 원고를 작성 중입니다..."):
                response = model.generate_content(prompt_text)
                res_text = response.text
                
                if SPLIT_TAG in res_text:
                    parts = res_text.split(SPLIT_TAG)
                    st.session_state.blog_script = parts[0]
                    st.session_state.image_prompts = [line.strip() for line in parts[1].strip().split('\n') if len(line) > 10]
                else:
                    st.session_state.blog_script = res_text
                    st.session_state.image_prompts = []
        except Exception as e:
            st.error(f"오류가 발생했습니다: {str(e)}")

# --- 결과 출력 영역 ---
if st.session_state.blog_script:
    st.divider()
    st.subheader("📋 완성된 블로그 원고")
    
    clean_blog = st.session_state.blog_script.strip()
    st.text_area("원고 내용", value=clean_blog, height=500)
    
    # 복사 기능 (HTML/JS)
    safe_text = clean_blog.replace('`','\\`').replace('$','\\$').replace('\n','\\n')
    st.components.v1.html(f"""
        <script>
        function copyText() {{
            const el = document.createElement('textarea');
            el.value = `{safe_text}`;
            document.body.appendChild(el);
            el.select();
            document.execCommand('copy');
            document.body.removeChild(el);
            alert('원고가 클립보드에 복사되었습니다!');
        }}
        </script>
        <button onclick="copyText()" style="width:100%; height:45px; background-color:#4CAF50; color:white; border:none; border-radius:10px; cursor:pointer; font-weight:bold;">📋 원고 전체 복사하기</button>
    """, height=50)
