import streamlit as st
import pandas as pd
import openai
import re
import json

# ---------------------------
# GPT API 설정 (OPENAI)
# ---------------------------
openai.api_key = st.secrets["OPENAI_API_KEY"]

# ---------------------------
# 언어 설정
# ---------------------------
lang = st.radio("언어를 선택하세요 / Select Language", ["한국어", "English"])

# ---------------------------
# 사이드바 안내
# ---------------------------
st.sidebar.title("MirrorOrg Analyzer")
st.sidebar.markdown("""
© 2025 MirrorMind Project  
본 분석은 평가 목적이 아닌, **성향의 차이를 이해하기 위한 참고 자료**입니다.  
해석에는 주의가 필요하며 실제 상황과는 다를 수 있습니다.
""")

# ---------------------------
# 의미 있는 대화 추출 함수
# ---------------------------
def extract_meaningful_lines(chat_text, min_length=15):
    lines = chat_text.split("\n")
    meaningful = []
    for line in lines:
        line = line.strip()
        if len(line) >= min_length and not re.search(r"^[0-9]{4}.*사진|이모티콘|ㅋㅋ|ㅎㅎ|\b(확인|넵|ㅇㅇ)\b", line):
            meaningful.append(line)
    return meaningful[:800]  # token 수 제한 대비 줄 수 제한

# ---------------------------
# GPT 프롬프트 (조직 진단)
# ---------------------------
ORG_DIAG_PROMPT = """
You are DR. Aiden Rhee, a senior analyst at MirrorOrg.

Analyze the following multi-person chat log and extract key indicators for organizational diagnosis. 
Use the MirrorMind framework, focusing on:
1. Individual identity factors (emotion, cognition, expression, value, bias)
2. Conflict structure between participants
3. Systemic risk assessment (in table form)
4. Suggestions for resilience recovery: 4.1 Role realignment / 4.2 Protocol improvement
5. Conclusion

Response in JSON with keys: identities, conflicts, systemic_risk, suggestions, conclusion

Chat log:
"""

# ---------------------------
# GPT 프롬프트 (역할 분석)
# ---------------------------
ROLE_ANALYSIS_PROMPT = """
You are DR. Aiden Rhee, a dialogue analyst.

Analyze the following group chat log and classify each participant into roles such as:
- Initiator
- Mediator
- Supporter
- Observer
- Challenger

Explain the reason for each classification.

Return as JSON in the format:
{
  "role_analysis": [
    {"name": "홍길동", "role": "Initiator", "reason": "Suggests direction repeatedly and dominates decisions."},
    ...
  ]
}

Chat log:
"""

# ---------------------------
# GPT 호출 함수
# ---------------------------
def query_gpt(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )
    return response.choices[0].message['content']

# ---------------------------
# 사용자 입력
# ---------------------------
uploaded_file = st.file_uploader("📁 분석할 카카오톡 파일을 업로드하세요", type="txt")
if uploaded_file:
    content = uploaded_file.read().decode("utf-8")
    short_content = "\n".join(extract_meaningful_lines(content))

    with st.spinner("🔍 조직 진단 중..."):
        try:
            org_prompt = ORG_DIAG_PROMPT + short_content
            org_raw = query_gpt(org_prompt)
            result = json.loads(org_raw)
            analysis_type = "조직 진단"
        except Exception:
            try:
                role_prompt = ROLE_ANALYSIS_PROMPT + short_content
                role_raw = query_gpt(role_prompt)
                result = json.loads(role_raw)
                analysis_type = "역할 기반 분석"
            except Exception:
                result = None
                analysis_type = None

    if result:
        st.success(f"✅ 분석 유형: {analysis_type}")

        if analysis_type == "조직 진단":
            st.subheader("🧠 정체성 계수표")
            st.json(result.get("identities", "❗ 정보 없음"))

            st.subheader("🔍 갈등 구조")
            st.json(result.get("conflicts", "❗ 갈등 분석 없음"))

            st.subheader("📉 시스템 리스크")
            st.json(result.get("systemic_risk", "❗ 리스크 정보 없음"))

            st.subheader("🧪 회복탄력성 제언")
            st.json(result.get("suggestions", "❗ 제언 없음"))

            st.subheader("📌 결론")
            st.write(result.get("conclusion", "❗ 결론 없음"))

        elif analysis_type == "역할 기반 분석":
            st.subheader("🎭 참여자 역할 분석")
            st.json(result.get("role_analysis", "❗ 역할 분석 없음"))

    else:
        st.error("분석에 실패했습니다. 대화 내용이 충분히 풍부한지 확인해주세요.")
