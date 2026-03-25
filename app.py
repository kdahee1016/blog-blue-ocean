import streamlit as st
import google.generativeai as genai
import webbrowser # 브라우저 탭을 열기 위한 라이브러리 (기본 내장)
import urllib.parse # 영문 프롬프트를 URL 형식으로 변환

# 페이지 설정
st.set_page_config(page_title="오키랑의 블로그 메이커", layout="centered")

st.title("📝 내 경험과 이미지가 담긴 블로그 초안 생성기")
st.caption("직접 겪은 에피소드와 필요한 이미지를 적어주시면, 감성으로 맛있게 버무려 드리고 Bing 이미지 생성 탭까지 띄워드려요! ✨")

# 사이드바: 설정
with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input("Gemini API Key를 입력하세요", type="password")
    st.info("API 키가 작동하지 않으면 새로 발급받아 1분 뒤 시도하세요.")

# 메인 화면: 입력 폼
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        main_k = st.text_input("📍 메인 키워드 (4회 반복)", placeholder="예: ㅇㅇ역 맛집")
    with col2:
        sub_k1 = st.text_input("🔍 서브 키워드 1", placeholder="예: 서울 아이랑")
        
    col3, col4 = st.columns(2)
    with col3:
        sub_k2 = st.text_input("🔍 서브 키워드 2", placeholder="예: 무한리필")
    with col4:
        sub_k3 = st.text_input("🔍 서브 키워드 3", placeholder="예: 내돈내산")

    st.subheader("📸 나의 실제 경험 (흐름 적기)")
    user_experience = st.text_area(
        "블로그에 꼭 넣고 싶은 내용이나 흐름을 자유롭게 적어주세요.",
        placeholder="예: 우리 아들이 ㅇㅇ를 평소 안 먹는데 여기서 3인분 먹음 / 주차장이 넓어서 편했음 등",
        height=150
    )

    # ⭐ 새로 추가된 이미지 입력란
    st.subheader("🖼️ 필요한 이미지 목록 (Gemini가 프롬프트 작성)")
    image_requests = st.text_input(
        "블로그에 넣을 이미지 주제들을 쉼표(,)로 구분해서 적어주세요.",
        placeholder="예: 치킨, 피자, 야구 등 더욱 자세한 표현이면 좋아요."
    )

# 원고 및 프롬프트 생성 로직
if st.button("✨ 내 경험 반영해서 원고 & 이미지 프롬프트 만들기"):
    if not api_key:
        st.error("API 키를 입력해주세요!")
    elif not main_k:
        st.warning("메인 키워드는 필수입니다.")
    else:
        try:
            genai.configure(api_key=api_key)
            
            # 사용 가능한 모델 리스트 확보 및 선택
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            priority_list = ["models/gemini-1.5-flash", "models/gemini-flash-latest"]
            
            target_model_name = None
            for m_name in priority_list:
                if m_name in available_models:
                    target_model_name = m_name
                    break
            
            if not target_model_name:
                st.error("사용 가능한 모델을 찾을 수 없습니다.")
                st.stop()
            
            model = genai.GenerativeModel(target_model_name)

            # --- [핵심!] 원고와 이미지 프롬프트를 동시에 요청하는 프롬프트 ---
            prompt = f"""
            주제: {main_k} (서브: {sub_k1}, {sub_k2}, {sub_k3})
            [블로거의 실제 경험 내용]
            {user_experience}

            위 내용을 반드시 포함해서 네이버 블로그 원고를 작성해줘. 아래 조건을 엄격히 준수할 것:

            1. 키워드: '{main_k}' 4회, '{sub_k1}', '{sub_k2}', '{sub_k3}' 각 1회 자연스럽게 포함.
            2. 제목: 클릭율 높이는 제목 3개 추천.
            3. 말투: 30대 여성의 일기체 (~했음, ~했다, 혼잣말). 친근하고 편안하게.
            4. 가독성: 한 줄에 공백포함 최대 60-70byte 내외로 끊어서 작성(모바일 최적화).
            5. 이모티콘: 리스트 중 5~6개 필수 사용 !(•̀ᴗ•́)و ̑̑ , (*ᴗ͈ˬᴗ͈)ꕤ*.ﾟ , (୨୧ ❛ᴗ❛)✧ , (୨୧ •͈ᴗ•͈) , (•̆ꈊ•̆ ) , (ꈍᴗꈍ)♡ ,  ̗̀ෆ(˶'ᵕ'˶)ෆ ̖́- , ٩(*•̀ᴗ•́*)و /,٩( ᐢ-ᐢ ), / ٩(๑❛ᴗ❛๑)۶♡ , ٩(◕ᗜ◕)و , ദ്ദി( ¯꒳¯ ) , ☆٩(｡•ω<｡)﻿و , :) , :D , >_< , +ㅂ+ 등).
            6. 이모지: 문맥에 맞는 그림 이모지 8개 내외 활용.
            7. AI가 쓴 것 같지 않도록 작성하되 중복문서 걸리지 않게 이중검토
            8. 분량: 한글 기준 약 3,500자 내외로 아주 상세하게.
            9. 상위노출SEO 반영해서 내용 작성
            10. 흐름에 맞춰 소제목 넣기 (이모지1개+소제목)
            11. 요약문: 최상단에 240~280byte 요약문 포함.

            ---

            [이미지 프롬프트 생성 요청]
            아래 주제들에 대해, Bing Image Creator에서 고퀄리티 이미지를 얻을 수 있는 영어 상세 묘사(프롬프트)를 각 1개씩 작성해줘.
            주제 목록: {image_requests}
            
            조건: Hyper-realistic, 8k, photorealistic, cinematic lighting, rustic style, bokeh background 같은 수식어를 적절히 활용하여 미적으로 훌륭한 결과가 나오도록 할 것.
            """
            
            with st.spinner(f"[{target_model_name}] 모델로 원고와 프롬프트를 짓는 중입니다..."):
                response = model.generate_content(prompt)
                full_text = response.text
                
                # 원고와 프롬프트 분리 (약속된 구분선 '---' 기준)
                parts = full_text.split('---')
                blog_script = parts[0].strip()
                image_prompts_raw = parts[1].strip() if len(parts) > 1 else ""

                st.success("🎉 작성이 완료되었습니다!")
                st.divider()
                
                # --- 원고 결과창 및 복사 버튼 ---
                st.subheader("📋 생성된 블로그 원고")
                st.text_area("원고 내용", value=blog_script, height=400, key="result_text")
                
                # 원고 전체 복사 버튼 (HTML/JS 사용)
                st.components.v1.html(f"""
                    <button onclick="copyToClipboard()" style="
                        width: 100%;
                        height: 40px;
                        background-color: #4CAF50;
                        color: white;
                        border: none;
                        border-radius: 10px;
                        cursor: pointer;
                        font-weight: bold;
                    ">📋 원고 전체 복사하기</button>
                    
                    <script>
                    function copyToClipboard() {{
                        const text = `{blog_script.replace('`', '\\`').replace('$', '\\$')}`;
                        navigator.clipboard.writeText(text).then(function() {{
                            alert('원고가 클립보드에 복사되었습니다! 네이버 블로그에 붙여넣으세요.');
                        }}, function(err) {{
                            console.error('복사 실패:', err);
                        }});
                    }}
                    </script>
                """, height=60)
                
                st.divider()

                # --- [핵심!] 이미지 프롬프트 결과창 및 멀티 탭 열기 버튼 ---
                st.subheader("🖼️ 생성된 이미지 프롬프트 & Bing 생성창")
                
                # 프롬프트를 줄바꿈 기준으로 나누기
                image_prompts = [p.strip() for p in image_prompts_raw.split('\n') if p.strip()]
                
                # 각 프롬프트를 텍스트로 보여주기
                for i, p in enumerate(image_prompts):
                    st.text_area(f"{i+1}번 이미지 프롬프트 (영어)", value=p, height=80, key=f"prompt_{i}")

                # [모든 이미지 생성창 탭으로 열기] 버튼
                if st.button("🚀 모든 이미지 생성창 탭으로 열기"):
                    if not image_prompts:
                        st.warning("생성된 이미지 프롬프트가 없습니다.")
                    else:
                        base_url = "https://www.bing.com/images/create?q="
                        
                        # 각 프롬프트에 대해 탭을 하나씩 열기
                        for p in image_prompts:
                            # 영문 프롬프트를 URL에 넣을 수 있도록 인코딩 (공백 -> %20 등)
                            encoded_prompt = urllib.parse.quote(p)
                            final_url = base_url + encoded_prompt
                            
                            # 브라우저의 새 탭으로 URL 열기
                            webbrowser.open_new_tab(final_url)
                            
                        st.success(f"{len(image_prompts)}개의 이미지 생성창이 탭으로 열렸습니다! 각 탭에서 '만들기'를 눌러주세요.")

        except Exception as e:
            st.error(f"오류가 발생했습니다: {str(e)}")
