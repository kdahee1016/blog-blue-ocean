import streamlit as st
import google.generativeai as genai
import urllib.parse

# 페이지 설정
st.set_page_config(page_title="오키랑의 블로그 메이커", layout="centered")

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
        "이미지 주제들을 적어주세요. 설명이 자세하면 더 좋아요!",
        placeholder="예: 30대 아빠와 엄마 그리고 10살 아들이 영화보는 모습, 쓰나미가 몰아닥치는 도시 등"
    )

# 실행 버튼
if st.button("✨ 원고 & 이미지 프롬프트 생성"):
    if not api_key:
        st.error("API 키를 입력해주세요!")
    elif not main_k:
        st.warning("메인 키워드는 필수입니다.")
    else:
        try:
            genai.configure(api_key=api_key)
            
            # 사용 가능한 모델을 자동으로 찾는 로직
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            priority_list = [
                "models/gemini-1.5-flash-latest",
                "models/gemini-flash-latest",
                "models/gemini-1.5-flash",
                "models/gemini-2.0-flash"
            ]
            
            target_model_name = None
            for m_name in priority_list:
                if m_name in available_models:
                    target_model_name = m_name
                    break
            
            if not target_model_name and available_models:
                target_model_name = available_models[0]
            
            if not target_model_name:
                st.error("사용 가능한 모델을 찾을 수 없습니다.")
                st.stop()
                
            model = genai.GenerativeModel(target_model_name)

            # 이미지 요청 여부에 따른 지시사항 구성
            image_instruction = ""
            if image_requests.strip():
                image_instruction = f"원고 작성이 끝나면 반드시 '==========IMAGE_PROMPTS=========='라는 문구를 쓰고, 그 아래에 {image_requests}에 대한 Bing용 영어 상세 묘사를 1줄씩 작성해줘."

            # 💡 SyntaxError 방지를 위해 프롬프트를 변수로 안전하게 조합
            prompt_text = (
                f"주제: {main_k} (서브: {sub_k1}, {sub_k2}, {sub_k3})\n"
                f"내용: {user_experience}\n\n"
                "[지시사항]\n"
                "1. 아래 양식에 맞춰 네이버 블로그 원고를 작성해줘.\n"
                f"2. {image_instruction}\n\n"
                "[원고 조건]\n"
                f"1. 키워드: '{main_k}' 4회, '{sub_k1}', '{sub_k2}', '{sub_k3}' 각 1회 자연스럽게 포함.\n"
                "2. 제목: 상위노출 될 수 있는 제목 3개 추천.\n"
                "3. 말투: 30대 여성의 일기체 (~했음, ~했다, 혼잣말). 친근하고 편안하게.\n"
                "4. 가독성: 한 줄에 공백포함 최대 60-70byte 내외로 끊어서 작성(모바일 최적화).\n"
                "5. 이모티콘: 리스트 중 5~6개 필수 사용 (!(•̀ᴗ•́)و ̑̑ , (*ᴗ͈ˬᴗ͈)ꕤ*.ﾟ , (୨୧ ❛ᴗ❛)✧ , (୨୧ •͈ᴗ•͈) , (•̆ꈊ•̆ ) , (ꈍᴗꈍ)♡ , ̗̀ෆ(˶'ᵕ'˶)ෆ ̖́- , ٩(*•̀ᴗ•́*)و /, ٩( ᐢ-ᐢ ), / ٩(๑❛ᴗ❛๑)۶♡ , ٩(◕ᗜ◕)و , ദ്ദി( ¯꒳¯ ) , ☆٩(｡•ω<｡)﻿و , :) , :D , >_< , +ㅂ+ 등).\n"
                "6. 이모지: 문맥에 맞는 그림 이모지 10개 내외 활용.\n"
                "7. AI가 쓴 것 같지 않도록 작성하되 중복문서 걸리지 않게 이중검토\n"
                "8. 분량: 한글 기준 약 3,500자 내외로 아주 상세하게.\n"
                "9. 상위노출SEO 반영해서 소제목 및 본문 작성\n"
                "10. 흐름에 맞춰 소제목 넣기 (그림이모지1개+소제목)\n"
                "11. 요약문: 최상단에 240~280byte 요약문 포함.\n\n"
                "[이미지 프롬프트 조건]\n"
                f"- 주제: {image_requests}\n"
                "- 각 주제별로 Bing에서 쓸 영어 상세 묘사를 1줄씩 작성할 것."
            )
            
            with st.spinner("원고와 이미지를 정성껏 준비 중입니다!"):
                response = model.generate_content(prompt_text)
                full_result = response.text
                
                if "==========IMAGE_PROMPTS==========" in full_result:
                    blog_script, image_prompts_raw = full_result.split("==========IMAGE_PROMPTS==========")
                else:
                    blog_script = full_result
                    image_prompts_raw = ""

                # ⭐ [추가 수정] 원고 하단에 잔여 조건 문구가 남는 현상 방지
                blog_script = blog_script.split("[이미지 프롬프트 조건]")[0].strip()

                st.success("🎉 작성이 완료되었습니다!")
                
                st.subheader("📋 생성된 블로그 원고")
                st.text_area("전체 원고", value=blog_script, height=450)
                
                st.components.v1.html(f"""
                    <button onclick="copyToClipboard()" style="width:100%; height:40px; background-color:#4CAF50; color:white; border:none; border-radius:10px; cursor:pointer; font-weight:bold;">📋 원고 전체 복사하기</button>
                    <script>
                    function copyToClipboard() {{
                        const text = `{blog_script.replace('`', '\\`').replace('$', '\\$')}`;
                        navigator.clipboard.writeText(text).then(function() {{ alert('원고가 복사되었어요!'); }});
                    }}
                    </script>
                """, height=60)

                if image_requests.strip() and image_prompts_raw.strip():
                    st.divider()
                    st.subheader("🖼️ 이미지 생성 가이드")
                    st.info("프롬프트 [복사] 후 [생성] 버튼을 눌러 Bing에 붙여넣으세요!")
                    
                    # '조건' 문구가 포함된 경우를 대비해 필터링
                    prompts = [p.strip() for p in image_prompts_raw.strip().split('\n') 
                               if p.strip() and "[이미지 프롬프트 조건]" not in p and "Scene" in p or len(p) > 20]
                    
                    for i, p in enumerate(prompts[:10]): # 최대 10개까지 표시
                        clean_p = p.split('. ', 1)[-1] if '. ' in p[:5] else p
                        clean_p = clean_p.replace('"', '').replace("'", "")
                        
                        st.text_input(f"이미지 {i+1} 영문 프롬프트", value=clean_p, key=f"input_{i}")
                        
                        col_copy, col_link = st.columns(2)
                        with col_copy:
                            st.components.v1.html(f"""
                                <button onclick="copyP()" style="width:100%; height:35px; background-color:#007BFF; color:white; border:none; border-radius:5px; cursor:pointer;">📝 프롬프트 {i+1} 복사</button>
                                <script>
                                function copyP() {{
                                    navigator.clipboard.writeText(`{clean_p}`).then(() => alert('{i+1}번 프롬프트가 복사되었습니다!'));
                                }}
                                </script>
                            """, height=45)
                        with col_link:
                            st.link_button(f"🎨 Bing에서 생성하기", url="https://www.bing.com/images/create")
                            
        except Exception as e:
            st.error(f"오류가 발생했습니다: {str(e)}")
