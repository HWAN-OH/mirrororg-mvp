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

# ✅ 미러마인드 프레임 기반 프롬프트 헤더
MIRRORMIND_HEADER = """
당신은 'MirrorMind AI 진단 프레임워크'에 최적화된 분석가입니다. 인간 간의 상호작용을 다음의 5가지 파라미터 기반으로 분석하십시오:

- 감정 (emotion): 감정 표현 및 정서적 반응성
- 사고 (cognition): 논리적 사고 및 문제 해결 능력
- 표현 (expression): 커뮤니케이션의 명료성 및 영향력
- 가치 (value): 내재된 신념과 동기 부여
- 편향 (bias): 인식 왜곡, 선호 경향성

이 기준을 활용하여 인물 간의 역학, 위험, 역할을 평가하세요.
"""

# ✅ MirrorMind 방식 프롬프트 (중괄호 이스케이프 처리)
PROMPT_NETWORK_JSON = MIRRORMIND_HEADER + '''

아래 대화를 읽고 다음을 분석하십시오:
1. 인물별 정체성 계수 (emotion, cognition, expression, value, bias)
2. 인물별 조직 내 핵심 역할 요약
3. 인물 간 갈등 구조 및 리스크 평가
4. 시스템 리스크 총평 (표 형태로 위험지수 요약)
5. 회복탄력성 증진을 위한 제언
    4.1 역할 재배치 시뮬레이션
    4.2 커뮤니케이션 프로토콜 개선
6. 결론 (현재 상태에 대한 종합 판단 및 향후 경과 예측)

출력은 아래 JSON 형식으로 구성하십시오:
```json
{{
  "identities": [
    {{"name": "오승환", "emotion": 0.6, "cognition": 0.7, "expression": 0.5, "value": 0.9, "bias": 0.4,
     "role": "핵심 의사결정자 및 전략가"}}
  ],
  "conflict_analysis": "표현방식의 차이에 기인한 잠재 갈등이 존재.",
  "risk_summary": [
    {{"risk_factor": "표현 불일치", "severity": "중간"}}
  ],
  "prescriptions": {{
    "role_realignment": "조율자 역할 확대 필요.",
    "protocol_update": "감정 공유를 포함한 프로토콜 개선 필요."
  }},
  "conclusion": "구조는 안정적이나, 소통 방식 개선이 장기적 리스크 완화에 기여할 수 있음."
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

lang = st.radio("언어 선택 / Language", options=["한국어", "English"], index=0)

uploaded_file = st.file_uploader("분석할 .txt 파일을 업로드하세요 / Upload .txt file for analysis", type="txt")
if not uploaded_file:
    st.stop()

file_content = uploaded_file.getvalue().decode("utf-8")
st.success(f"'{uploaded_file.name}' 파일 업로드 완료 / File uploaded")

def get_short_content(content, max_lines=1000, max_chars=16000):
    lines = content.splitlines()
    short = "\n".join(lines[-max_lines:])
    return short[-max_chars:] if len(short) > max_chars else short

def render_identity_table(data):
    if not isinstance(data, list):
        st.warning("데이터 형식 오류: 'identities' 항목이 리스트가 아님")
        return
    df = pd.DataFrame(data)
    if "name" not in df.columns:
        st.warning("데이터 오류: 'name' 필드 없음")
        return

    df.index = df["name"]
    df = df.drop(columns=["name"], errors="ignore")

    df = df.rename(columns={
        "emotion": "감정",
        "cognition": "사고",
        "expression": "표현",
        "value": "가치",
        "bias": "편향",
        "role": "핵심 역할"
    })

    numeric_cols = [col for col in ["감정", "사고", "표현", "가치", "편향"] if col in df.columns]
    st.subheader("📊 인물별 정체성 계수표 및 역할")
    st.dataframe(df.style.format({col: "{:.1f}" for col in numeric_cols}))

def render_risk_table(risks):
    df = pd.DataFrame(risks)
    df = df.rename(columns={"risk_factor": "위험 요인", "severity": "심각도"})
    st.subheader("⚠️ 시스템 리스크 총평")
    st.table(df)

def render_summary(data):
    st.subheader("🔍 갈등 분석")
    st.markdown(f"- {data.get('conflict_analysis', '분석 없음')}")

    st.subheader("🧪 회복탄력성 제언")
    st.markdown(f"**4.1 역할 재배치 시뮬레이션:** {data.get('prescriptions', {}).get('role_realignment', '')}")
    st.markdown(f"**4.2 프로토콜 개선:** {data.get('prescriptions', {}).get('protocol_update', '')}")

    st.subheader("📌 결론")
    st.markdown(data.get("conclusion", "결론 없음"))

if st.button("진단 실행 / Run Diagnosis", use_container_width=True):
    with st.spinner("분석 중 / Analyzing..."):
        short_content = get_short_content(file_content)
        result = analyze_network_json(short_content)

    if "data" in result and isinstance(result["data"], dict):
        data = result["data"]
        if "identities" in data:
            render_identity_table(data["identities"])
        if "risk_summary" in data:
            render_risk_table(data["risk_summary"])
        render_summary(data)
    elif "error" in result:
        st.error("❌ 분석 실패: JSON 파싱 실패 또는 응답 오류")
        st.text(result.get("raw_response", "응답 없음 / No response"))
