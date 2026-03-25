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
if "full_prompt" not in st.session_state:
    st.session_state.full_prompt = ""

st.title("📝 블로그 초안 생성기")
st.caption("직접 겪은 에피소드를 적어주시면 자연스러운 감성으로 맛있게 버무려 드려요! ✨")

# 사이드바: 설정
with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input("Gemini API Key를 입력하세요", type="password")

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
        main_k = st.text_input("📍 메인 키워드", placeholder="예: 영화 ㅇㅇㅇ 후기")
    with col2:
        sub_k1 = st.text_input("🔍 서브 키워드 1")
    col3, col4 = st.columns(2)
    with col3:
        sub_k2 = st.text_input("🔍 서브 키워드 2")
    with col4:
        sub_k3 = st.text_input("🔍 서브 키워드 3")
    user_experience = st.text_area("📸 나의 실제 경험 (흐름 적기)", height=150)
    image_requests = st.text_input("🖼️ 필요한 이미지 목록", placeholder="예: 30대 부모와 아이가 영화보는 모습 등")

# --- 원고 & 이미지 전체 생성 버튼 ---
if st.button("✨ 원고 & 이미지 생성하기", use_container_width=True):
    if not api_key or not main_k:
        st.error("API 키와 메인 키워드를 확인해주세요.")
    else:
        try:
            genai.configure(api_key=api_key)
            model = get_available_model()

            image_instruction = ""
            if image_requests.strip():
                image_instruction = f"모든 작성이 끝나면 마지막에 '{SPLIT_TAG}'를 쓰고 '{image_requests}'에 대한 상세한 영어 이미지 프롬프트를 작성해."

            # 💡 [필수 항목 절대 누락 금지 지시 추가]
            prompt_text = (
                f"주제: {main_k} (서브: {sub_k1}, {sub_k2}, {sub_k3})\n"
                f"내용: {user_experience}\n\n"
                "[필독 지시사항 - 이 순서대로 안 쓰면 오류임]\n"
                "다음 4가지는 반드시 순서대로 '모두' 포함되어야 함:\n"
                "1. 제목추천 (상위노출용 3개)\n"
                "2. 요약문 (240~280byte)\n"
                "3. 본문 (2,000자~2,500자)\n"
                "4. 추천해시태그 10개 (본문 하단에 배치)\n\n"
                "[원고 조건 - 엄격 준수]\n"
                f"- 키워드: '{main_k}' 4회, '{sub_k1}', '{sub_k2}', '{sub_k3}' 각 1회 자연스럽게 포함.\n"
                "- 말투: 무조건 30대 여성의 '간결한 혼잣말 일기체' (~했음, ~였다, ~이다, ~임 골고루 섞어서 쓰기).\n"
                "- 소제목 형식: 반드시 '[그림이모지 1개 + 소제목]' 형식을 지킬 것.\n"
                "- 가독성: 한 줄에 60-70byte 내외로 짧게 끊기(모바일 최적화).\n"
                "- 이모티콘: 리스트 중 5~6개 필수 사용 (!(•̀ᴗ•́)و ̑̑ , (*ᴗ͈ˬᴗ͈)ꕤ*.ﾟ , (୨୧ ❛ᴗ❛)✧ , (୨୧ •͈ᴗ•͈) , (•̆ꈊ•̆ ) , (ꈍᴗꈍ)♡ ,  ̗̀ෆ(˶'ᵕ'˶)ෆ ̖́- , ٩(*•̀ᴗ•́*)و /,٩( ᐢ-ᐢ ), / ٩(๑❛ᴗ❛๑)۶♡ , ٩(◕ᗜ◕)و , ദ്ദി( ¯꒳¯ ) , ☆٩(｡•ω<｡)﻿و , :) , :D , >_< , +ㅂ+ 등).\n"
                "- SEO: 상위노출을 위해 정보성과 경험을 듬뿍 담아 2,000~2,500자로 상세히 작성.\n"
                f"- {image_instruction}\n"
            )
            
            with st.spinner("정성 듬-뿍 담은 원고를 작성중입니다. 잠시만 기다려 주세요."):
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
            st.error(f"오류: {str(e)}")

if st.session_state.blog_script and len(st.session_state.blog_script) < 1000:
    if st.button("🔽 본문이 누락됐거나 짧나요? 다시 길게 생성하기", use_container_width=True):
        try:
            genai.configure(api_key=api_key)
            model = get_available_model()
            retry_prompt = f"{st.session_state.full_prompt}\n\n방금 요약만 하고 본문을 안 썼어. 요약은 무시하고 '본문'부터 2,000자~2,500자로 길게 다시 써줘."
            with st.spinner("본문을 다시 꽉 채워 생성 중입니다..."):
                response = model.generate_content(retry_prompt)
                st.session_state.blog_script = response.text
                st.toast("원고가 다시 생성되었습니다!")
        except Exception as e:
            st.error(f"오류: {e}")

# --- 결과 출력 영역 ---
if st.session_state.blog_script:
    st.divider()
    st.subheader("📋 생성된 블로그 원고")
    
    # 보고서 텍스트 필터링
    stop_keywords = ["원고 조건 확인", "조건 적용 완료", "[원고 조건", "---"]
    clean_blog = st.session_state.blog_script
    for stop_word in stop_keywords:
        if stop_word in clean_blog:
            clean_blog = clean_blog.split(stop_word)[0]
    
    clean_blog = clean_blog.strip()
    st.text_area("전체 원고 (복사해서 사용하세요)", value=clean_blog, height=500)
    
    # 원고 전체 복사 버튼
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
            alert('원고가 복사되었습니다!');
        }}
        </script>
        <button onclick="copyText()" style="width:100%; height:45px; background-color:#4CAF50; color:white; border:none; border-radius:10px; cursor:pointer; font-weight:bold; font-size:16px;">📋 원고 전체 복사하기</button>
    """, height=50)

    # 이미지 추가 생성 버튼
    if st.button("🖼️ 이미지만 추가/교체 생성", use_container_width=True):
        if not api_key or not image_requests:
            st.warning("이미지 주제를 입력해주세요.")
        else:
            try:
                genai.configure(api_key=api_key)
                model = get_available_model()
                img_prompt = f"'{image_requests}'에 대한 Bing용 영어 이미지 프롬프트 3개 작성. 서론 없이 프롬프트만."
                with st.spinner("이미지 프롬프트 생성 중..."):
                    res = model.generate_content(img_prompt).text
                    st.session_state.image_prompts = [line.strip() for line in res.strip().split('\n') if len(line) > 10]
                    st.toast("프롬프트가 업데이트되었습니다!")
            except Exception as e:
                st.error(f"오류: {e}")

# --- 이미지 프롬프트 결과 영역 ---
if st.session_state.image_prompts:
    st.divider()
    st.subheader("🖼️ 이미지 생성 가이드")
    for i, p in enumerate(st.session_state.image_prompts):
        p_clean = p.split(':', 1)[-1] if ':' in p else p
        p_clean = p_clean.split('.', 1)[-1] if '.' in p_clean[:3] else p_clean
        p_clean = p_clean.strip().replace('"', '')
        
        st.text_input(f"이미지 {i+1}", value=p_clean, key=f"input_{i}")
        c1, c2 = st.columns(2)
        with c1:
            st.components.v1.html(f"""
                <script>function cp{i}(){{const el=document.createElement('textarea');el.value=`{p_clean}`;document.body.appendChild(el);el.select();document.execCommand('copy');document.body.removeChild(el);alert('복사완료!');}}</script>
                <button onclick="cp{i}()" style="width:100%; height:35px; background-color:#007BFF; color:white; border:none; border-radius:5px; cursor:pointer;">📝 복사</button>
            """, height=40)
        with c2:
            st.link_button("🎨 Bing 생성", url="https://www.bing.com/images/create")
