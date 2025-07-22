import streamlit as st
import openai
import json
import re
from collections import Counter
import pandas as pd

# ✅ OpenAI 클라이언트 초기화
try:
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error(f"OpenAI API 키 설정 오류: {e}")
    client = None

# ✅ MirrorMind 방식 프롬프트 (중괄호 이스케이프 처리)
PROMPT_NETWORK_JSON = '''
# MirrorMind 분석 프로토콜

당신은 고급 사회심리 모델 기반의 AI 분석가이며, 다음 대화 텍스트를 읽고 각 인물의 성향 계수를 추정하고, 다음 분석을 수행하십시오:

1. 인물별 정체성 계수 (emotion, cognition, expression, value, bias)
2. 인물별 조직 내 핵심 역할 요약
3. 인물 간 갈등 구조 및 리스크 평가
4. 시스템 리스크 총평 (표 형태로 위험지수 요약)
5. 회복탄력성 증진을 위한 제언
    4.1 역할 재배치 시뮬레이션
    4.2 커뮤니케이션 프로토콜 개선
6. 결론 (현재 상태에 대한 종합 판단 및 향후 경과 예측)

출력은 아래 형식으로 구성하십시오:
```json
{{
  "identities": [
    {{"name": "오승환", "emotion": 0.6, "cognition": 0.7, "expression": 0.5, "value": 0.9, "bias": 0.4,
     "role": "핵심 의사결정자 및 전략가"}},
    {{"name": "설원준", "emotion": 0.3, "cognition": 0.8, "expression": 0.4, "value": 0.7, "bias": 0.2,
     "role": "지지자 및 완충자"}}
  ],
  "conflict_analysis": "갈등은 낮은 수준이나, 표현 방식 차이로 인한 잠재 긴장이 존재.",
  "risk_summary": [
    {{"risk_factor": "표현의 불일치", "severity": "중간"}},
    {{"risk_factor": "편향 축적", "severity": "낮음"}}
  ],
  "prescriptions": {{
    "role_realignment": "설원준에게 의사결정 보조 기능 부여, 홍준에게 중재자 역할 확대.",
    "protocol_update": "핵심 회의 시 감정 표현 단계 삽입 및 요약 반복 요청 프로토콜 적용."
  }},
  "conclusion": "현재 구조는 안정적이나, 고도화된 상호작용을 위해 프로토콜 개선이 필요함."
}}
```

분석 대상 대화:
{chat_log}
'''

def call_openai_api(prompt: str, model="gpt-3.5-turbo", max_tokens=3000) -> str:
    if not client:
        return json.dumps({"error": "OpenAI client is not initialized."})
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.2,
        )
        return response.choices[0].message.content
    except Exception as e:
        return json.dumps({"error": f"API call failed: {e}"})

def analyze_network_json(chat_log: str):
    prompt = PROMPT_NETWORK_JSON.format(chat_log=chat_log)
    result_text = call_openai_api(prompt)

    try:
        match = re.search(r"```json\s*([\s\S]*?)\s*```", result_text)
        if match:
            json_text = match.group(1)
        else:
            json_text = result_text
        parsed = json.loads(json_text)
        return {
            "data": parsed,
            "prompt": prompt
        }
    except (json.JSONDecodeError, TypeError) as e:
        return {
            "error": f"Failed to decode JSON from LLM response: {e}",
            "raw_response": result_text,
            "prompt": prompt
        }

# ------------------------------
# STREAMLIT UI STARTS HERE
# ------------------------------

st.set_page_config(page_title="MirrorOrg 조직 진단 요약", layout="wide")
st.title("🪞 MirrorOrg 조직 진단 요약")

with st.sidebar:
    st.markdown("""
    ### 📝 분석 목적
    이 분석은 평가 목적이 아닌, 성향의 차이를 파악하여 커뮤니케이션 개선을 돕기 위한 것입니다.
    
    ---
    ### ⚖️ 저작권 / Copyright
    © 2025 Sunghwan Oh. All rights reserved.
    """)

uploaded_file = st.file_uploader("분석할 .txt 파일을 업로드하세요", type="txt")
if not uploaded_file:
    st.stop()

file_content = uploaded_file.getvalue().decode("utf-8")
st.success(f"'{uploaded_file.name}' 파일 업로드 완료")

def get_short_content(content, max_lines=400, max_chars=10000):
    lines = content.splitlines()
    short = "\n".join(lines[-max_lines:])
    return short[-max_chars:] if len(short) > max_chars else short

def render_identity_table(data):
    df = pd.DataFrame(data)
    df.index = df["name"]
    df = df.drop(columns=["name"])
    df = df.rename(columns={
        "emotion": "감정",
        "cognition": "사고",
        "expression": "표현",
        "value": "가치",
        "bias": "편향",
        "role": "핵심 역할"
    })
    st.subheader("📊 인물별 정체성 계수표 및 역할")
    st.dataframe(df.style.format("{:.1f}"))

def render_risk_table(risks):
    df = pd.DataFrame(risks)
    df = df.rename(columns={"risk_factor": "위험 요인", "severity": "심각도"})
    st.subheader("⚠️ 시스템 리스크 총평")
    st.table(df)

def render_summary(data):
    st.subheader("🔍 갈등 분석")
    st.markdown(f"- {data['conflict_analysis']}")

    st.subheader("🧪 회복탄력성 제언")
    st.markdown(f"**4.1 역할 재배치 시뮬레이션:** {data['prescriptions']['role_realignment']}")
    st.markdown(f"**4.2 프로토콜 개선:** {data['prescriptions']['protocol_update']}")

    st.subheader("📌 결론")
    st.markdown(data["conclusion"])

if st.button("진단 실행 (Run Diagnosis)", use_container_width=True):
    with st.spinner("분석 중..."):
        short_content = get_short_content(file_content)
        result = analyze_network_json(short_content)

    if "data" in result:
        render_identity_table(result["data"]["identities"])
        render_risk_table(result["data"]["risk_summary"])
        render_summary(result["data"])
    elif "error" in result:
        st.error("❌ 분석 실패: JSON 파싱 실패 또는 응답 오류")
        st.text(result.get("raw_response", "응답 없음"))
