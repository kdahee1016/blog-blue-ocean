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

# 메인 화면: 입력 폼
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        main_k = st.text_input("📍 메인 키워드", placeholder="예: 영화 ㅇㅇㅇ 후기")
    with col2:
        sub_k1 = st.text_input("🔍 서브 키워드 1", placeholder="예: 초등학생 영화")
        
    col3, col4 = st.columns(2)
    with col3:
        sub_k2 = st.text_input("🔍 서브 키워드 2", placeholder="예: 아이랑 넷플릭스")
    with col4:
        sub_k3 = st.text_input("🔍 서브 키워드 3", placeholder="예: 기타 등등")

    st.subheader("📸 나의 실제 경험 (흐름 적기)")
    user_experience = st.text_area(
        "블로그에 꼭 넣고 싶은 내용이나 흐름을 자유롭게 적어주세요.",
        placeholder="예: 아들이랑 봤는데 너무 재밌어함, 재난 가방 싸야겠다고 난리법석 등",
        height=150
    )

    st.subheader("🖼️ 필요한 이미지 목록")
    image_requests = st.text_input(
        "이미지 주제들을 적어주세요.",
        placeholder="예: 30대 부모와 아이가 영화보는 모습 등"
    )

# --- 상단에는 '전체 생성' 버튼만 배치 ---
if st.button("✨ 원고 & 이미지 전체 생성", use_container_width=True):
    if not api_key or not main_k:
        st.warning("API 키와 메인 키워드를 입력해주세요.")
    else:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")

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
                "5. 이모티콘: 리스트 중 5~6개 필수 사용 (!(•̀ᴗ•́)و ̑̑ , (*ᴗ͈ˬᴗ͈)ꕤ*.ﾟ , (୨୧ ❛ᴗ❛)✧ , (୨୧ •͈ᴗ•͈) , (•̆ꈊ•̆ ) , (ꈍᴗꈍ)♡ , ̗̀ෆ(˶'ᵕ'˶)ෆ ̖·- , ٩(*•̀ᴗ•́*)و /, ٩( ᐢ-ᐢ ), / ٩(๑❛ᴗ❛๑)۶♡ , ٩(◕ᗜ◕)و , ദ്디( ¯꒳¯ ) , ☆٩(｡•ω<｡)﻿و , :) , :D , >_< , +ㅂ+ 등).\n"
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
                    st.session_state.blog_script, raw_img = res_text.split(SPLIT_TAG)
                    st.session_state.image_prompts = [line.strip() for line in raw_img.strip().split('\n') if len(line) > 10]
                else:
                    st.session_state.blog_script = res_text
                    st.session_state.image_prompts = []
        except Exception as e:
            st.error(f"오류가 발생했습니다: {str(e)}")

# --- 결과 출력 영역 ---
if st.session_state.blog_script:
    st.divider()
    st.subheader("📋 생성된 블로그 원고")
    clean_blog = st.session_state.blog_script.split("**[이미지")[0].split("Image Prompt")[0].strip()
    st.text_area("전체 원고", value=clean_blog, height=450)
    
    # 1. 원고 전체 복사 버튼
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

    # 2. 💡 [위치 이동] 이미지만 추가/교체 생성 버튼 (원고 하단에 배치)
    if st.button("🖼️ 이미지 추가 생성", use_container_width=True):
        if not api_key or not image_requests:
            st.warning("API 키와 이미지 주제를 입력해주세요.")
        else:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-1.5-flash")
                img_prompt = f"'{image_requests}'에 대해 Bing Image Creator용 상세 영어 프롬프트를 3개 작성해줘. 서론 없이 프롬프트만."
                with st.spinner("이미지 프롬프트 생성 중..."):
                    res = model.generate_content(img_prompt).text
                    st.session_state.image_prompts = [line.strip() for line in res.strip().split('\n') if len(line) > 10]
                    st.toast("프롬프트가 업데이트되었습니다! 하단을 확인하세요.")
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
        
        st.text_input(f"이미지 {i+1} 영문 프롬프트", value=p_clean, key=f"input_{i}")
        c1, c2 = st.columns(2)
        with c1:
            st.components.v1.html(f"""
                <script>
                function copyPrompt{i}() {{
                    const el = document.createElement('textarea');
                    el.value = `{p_clean}`;
                    document.body.appendChild(el);
                    el.select();
                    document.execCommand('copy');
                    document.body.removeChild(el);
                    alert('{i+1}번 프롬프트 복사 완료!');
                }}
                </script>
                <button onclick="copyPrompt{i}()" style="width:100%; height:35px; background-color:#007BFF; color:white; border:none; border-radius:5px; cursor:pointer;">📝 프롬프트 복사</button>
            """, height=40)
        with c2:
            st.link_button("🎨 Bing 생성", url="https://www.bing.com/images/create")
