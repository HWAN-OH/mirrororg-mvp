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

# ✅ MirrorMind 방식 프롬프트
PROMPT_NETWORK_JSON = '''
# MirrorMind 분석 프로토콜

당신은 고급 사회심리 모델 기반의 AI 분석가이며, 다음 대화 텍스트를 읽고 각 인물의 성향 계수를 추정하십시오.

## 분석 규칙
- 출력은 다음과 같은 구조의 JSON 리스트여야 합니다:
```json
[
  {{"name": "오승환", "emotion": 0.6, "cognition": 0.7, "expression": 0.5, "value": 0.9, "bias": 0.4}},
  ...
]
```
- emotion, cognition, expression, value, bias는 0~1 사이의 값이며, 소수점 첫째 자리까지 나타냅니다.
- JSON 이외의 설명은 포함하지 마십시오.

## 분석 대상 대화
{chat_log}
'''

def call_openai_api(prompt: str, model="gpt-3.5-turbo", max_tokens=2048) -> str:
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

def analyze_network_json(chat_log: str, lang: str = 'ko'):
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
    df.columns = ["감정", "사고", "표현", "가치", "편향"]
    st.subheader("📊 인물별 정체성 계수표")
    st.dataframe(df.style.format("{:.1f}"))

def generate_text_summary(data):
    names = [x["name"] for x in data]
    name_counts = Counter(names)
    top_people = [name for name, _ in name_counts.most_common(3)]
    summary = f"""
### 🧾 조직 진단 요약 (MirrorMind 기반)

- 📌 핵심 인물 / Key Figures: {', '.join(top_people)}

---

### 🔍 종합 제언 / Insights & Suggestions

- 각 인물의 편향과 감정 계수 차이를 고려하여 커뮤니케이션 방식을 조정해야 합니다.
- 정체성 계수는 고정된 특성이 아니며, 상호작용에 따라 변화할 수 있습니다.
- 대화 방식의 다양성을 인정하고 수용하는 태도가 조직 건강성에 기여합니다.
    """
    st.markdown(summary)

if st.button("진단 실행 (Run Diagnosis)", use_container_width=True):
    with st.spinner("분석 중..."):
        short_content = get_short_content(file_content)
        result = analyze_network_json(short_content)

    if "data" in result:
        render_identity_table(result["data"])
        generate_text_summary(result["data"])
    elif "error" in result:
        st.error("❌ 분석 실패: JSON 파싱 실패 또는 응답 오류")
        st.text(result.get("raw_response", "응답 없음"))
