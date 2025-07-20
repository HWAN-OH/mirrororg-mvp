# analyzer.py
# 역할: OpenAI API를 호출하여 채팅 기록으로부터 구조화된 JSON 데이터를 추출합니다.

import openai
import json
import streamlit as st
import re  # ✅ [필수] JSON 추출용 정규표현식 사용을 위해 필요함

# API 클라이언트는 앱 시작 시 한 번만 초기화합니다.
# Streamlit Secrets에서 API 키를 안전하게 불러옵니다.
try:
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error(f"OpenAI API 키를 설정하는 중 오류가 발생했습니다: {e}")
    client = None

# --- 프롬프트 정의 ---

PROMPT_FATIGUE_JSON = """ 
# 지시사항
아래 팀 대화 데이터를 분석하여, 각 팀원별 날짜별 피로도(1~5점)를 시계열 데이터로 추출하세요.

# 규칙
- 피로도는 말투, 감정 표현, 불만 등을 기준으로 추정합니다.
- 피로도 추정이 불가능하면, 기본값 3점으로 설정하세요.
- 응답은 반드시 아래 예시와 동일한 JSON 형식이어야 하며, 다른 어떤 텍스트도 포함해서는 안 됩니다.

# 출력 형식 예시
```json
[
  {"name": "현진", "fatigue_timeline": [{"date": "2025-07-01", "score": 2}, {"date": "2025-07-02", "score": 3}]},
  {"name": "유미", "fatigue_timeline": [{"date": "2025-07-01", "score": 1}, {"date": "2025-07-02", "score": 1}]}
]
```
---
# 분석 대상 대화
{chat_log}
"""

PROMPT_NETWORK_JSON = """
# 지시사항
아래 팀 대화 데이터를 분석하여, 팀원 간의 관계를 'support'(지지/긍정) 또는 'conflict'(갈등/부정)로 분류하고, 그 관계의 강도(0.1~1.0)를 추정하세요.

# 규칙
- 모든 관계는 반드시 'support' 또는 'conflict' 중 하나로만 분류해야 합니다. (중립/모호함 불허)
- 응답은 반드시 아래 예시와 동일한 JSON 형식이어야 하며, 다른 어떤 텍스트도 포함해서는 안 됩니다.

# 출력 형식 예시
```json
[
  {"source": "현진", "target": "유미", "strength": 0.8, "type": "conflict"},
  {"source": "유미", "target": "소피아", "strength": 0.5, "type": "support"}
]
```
---
# 분석 대상 대화
{chat_log}
"""

def call_openai_api(prompt: str, model="gpt-3.5-turbo", max_tokens=2048) -> str | None:
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

        return json.loads(json_text)
    except (json.JSONDecodeError, TypeError):
        return {"error": "Failed to decode JSON from LLM response.", "raw_response": result_text}