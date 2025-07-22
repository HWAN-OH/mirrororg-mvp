import openai
import json
import re
import streamlit as st

# ✅ OpenAI 클라이언트 초기화
try:
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error(f"OpenAI API 키 설정 오류: {e}")
    client = None

# ✅ 분석용 프롬프트 (정체성 계수 추출)
PROMPT_IDENTITY_ANALYSIS = '''
# MirrorMind 성향 분석 프로토콜

당신은 고급 심리 분석 AI입니다. 아래 대화를 읽고 인물별로 다음 다섯 가지 정체성 계수를 추정하십시오:
- emotion: 감정적 민감도
- cognition: 사고의 논리성/심화 정도
- expression: 표현의 직접성/강도
- value: 타인/조직 중심의 가치 성향
- bias: 고정관념, 편향의 강도 (높을수록 왜곡된 판단 경향)

출력은 아래 형식으로 작성하십시오:
```json
[
  {"name": "오승환", "emotion": 0.6, "cognition": 0.7, "expression": 0.5, "value": 0.9, "bias": 0.4},
  {"name": "설원준", "emotion": 0.3, "cognition": 0.8, "expression": 0.4, "value": 0.7, "bias": 0.2}
]
```

분석 대상 대화:
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

def analyze_identity_parameters(chat_log: str):
    prompt = PROMPT_IDENTITY_ANALYSIS.format(chat_log=chat_log)
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
            "error": f"Failed to decode JSON from LLM response: {e}"},
            "raw_response": result_text,
            "prompt": prompt
        }
