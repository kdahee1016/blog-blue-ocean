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
        sub_k1 = st.text_input("🔍 서브 키워드 1", placeholder="예: 아이랑 볼만한 영화")
        
    col3, col4 = st.columns(2)
    with col3:
        sub_k2 = st.text_input("🔍 서브 키워드 2", placeholder="예: 재난영화 추천")
    with col4:
        sub_k3 = st.text_input("🔍 서브 키워드 3", placeholder="예: 초등학생 영화")

    st.subheader("📸 나의 실제 경험 (흐름 적기)")
    user_experience = st.text_area(
        "블로그에 꼭 넣고 싶은 내용이나 흐름을 자유롭게 적어주세요.",
        placeholder="예: 아들이랑 봤는데 너무 재밌어함, 재난 가방 싸야겠다고 난리법석 등",
        height=150
    )

    st.subheader("🖼️ 필요한 이미지 목록")
    image_requests = st.text_input(
        "이미지 주제들을 적어주세요.",
        placeholder="예: 거대한 파도, 영화 보는 가족, 재난 가방"
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
            model = genai.GenerativeModel('models/gemini-1.5-flash')

            # 💡 구분선을 아주 확실한 텍스트로 지정합니다.
            prompt = f"""
            주제: {main_k} (서브: {sub_k1}, {sub_k2}, {sub_k3})
            내용: {user_experience}

            [지시사항]
            1. 아래 양식에 맞춰 네이버 블로그 원고를 작성해줘.
            2. 원고 작성이 끝나면 반드시 '==========IMAGE_PROMPTS=========='라는 문구를 쓰고, 그 아래에 이미지 프롬프트를 작성해.

            [원고 조건]
            1. 키워드: '{main_k}' 4회, '{sub_k1}', '{sub_k2}', '{sub_k3}' 각 1회 자연스럽게 포함.
            2. 제목: 클릭율 높이는 제목 3개 추천.
            3. 말투: 30대 여성의 일기체 (~했음, ~했다, 혼잣말). 친근하고 편안하게.
            4. 가독성: 한 줄에 공백포함 최대 60-70byte 내외로 끊어서 작성(모바일 최적화).
            5. 이모티콘: 리스트 중 5~6개 필수 사용 !(•̀ᴗ•́)و ̑̑ , (*ᴗ͈ˬᴗ͈)ꕤ*.ﾟ , (୨୧ ❛ᴗ❛)✧ , (୨୧ •͈ᴗ•͈) , (•̆ꈊ•̆ ) , (ꈍᴗꈍ)♡ ,  ̗̀ෆ(˶'ᵕ'˶)ෆ ̖́- , ٩(*•̀ᴗ•́*)و /,٩( ᐢ-ᐢ ), / ٩(๑❛ᴗ❛๑)۶♡ , ٩(◕ᗜ◕)و , ദ്ദി( ¯꒳¯ ) , ☆٩(｡•ω<｡)﻿و , :) , :D , >_< , +ㅂ+ 등).
            6. 이모지: 문맥에 맞는 그림 이모지 8개 내외 활용.
            7. AI가 쓴 것 같지 않도록 작성하되 중복문서 걸리지 않게 이중검토
            8. 분량: 한글 기준 약 3,500자 내외로 아주 상세하게.
            9. 상위노출SEO 반영해서 내용 작성
            10. 흐름에 맞춰 소제목 넣기
            11. 요약문: 최상단에 240~280byte 요약문 포함.

            [이미지 프롬프트 조건]
            - 주제: {image_requests}
            - 각 주제별로 Bing에서 쓸 영어 상세 묘사를 1줄씩 작성해줘.
            """
            
            with st.spinner("원고와 이미지를 정성껏 준비 중입니다..."):
                response = model.generate_content(prompt)
                full_result = response.text
                
                # 확실한 구분선으로 분리
                if "==========IMAGE_PROMPTS==========" in full_result:
                    blog_script, image_prompts_raw = full_result.split("==========IMAGE_PROMPTS==========")
                else:
                    blog_script = full_result
                    image_prompts_raw = ""

                st.success("🎉 작성이 완료되었습니다!")
                
                # --- 원고 출력 ---
                st.subheader("📋 생성된 블로그 원고")
                st.text_area("전체 원고", value=blog_script.strip(), height=450)
                
                # 복사 버튼 (HTML)
                st.components.v1.html(f"""
                    <button onclick="copyToClipboard()" style="width:100%; height:40px; background-color:#4CAF50; color:white; border:none; border-radius:10px; cursor:pointer; font-weight:bold;">📋 원고 전체 복사하기</button>
                    <script>
                    function copyToClipboard() {{
                        const text = `{blog_script.strip().replace('`', '\\`').replace('$', '\\$')}`;
                        navigator.clipboard.writeText(text).then(function() {{ alert('원고가 복사되었습니다!'); }});
                    }}
                    </script>
                """, height=60)

                st.divider()

                # --- 이미지 프롬프트 출력 ---
                st.subheader("🖼️ 이미지 생성 가이드")
                st.info("아래 버튼을 누르면 Bing 이미지 생성창으로 바로 연결됩니다.")
                
                prompts = [p.strip() for p in image_prompts_raw.strip().split('\n') if p.strip()]
                
                for i, p in enumerate(prompts):
                    # 프롬프트 앞에 번호가 붙어있으면 제거 (예: "1. Prompt" -> "Prompt")
                    clean_p = p.split('. ', 1)[-1] if '. ' in p[:5] else p
                    encoded_p = urllib.parse.quote(clean_p)
                    bing_url = f"https://www.bing.com/images/create?q={encoded_p}"
                    
                    col_p, col_btn = st.columns([3, 1])
                    with col_p:
                        st.text_input(f"이미지 {i+1} 프롬프트", value=clean_p, key=f"p_{i}")
                    with col_btn:
                        st.link_button(f"🎨 생성 {i+1}", url=bing_url)

        except Exception as e:
            st.error(f"오류가 발생했습니다: {str(e)}")
