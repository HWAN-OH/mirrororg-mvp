import openai
import json
import streamlit as st
import re

try:
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error(f"OpenAI API 키 설정 오류: {e}")
    client = None

PROMPT_NETWORK_JSON = """
# 지시사항
아래 팀 대화 데이터를 분석하여, 팀원 간의 관계를 'support'(지지/긍정) 또는 'conflict'(갈등/부정)로 분류하고, 그 관계의 강도(0.1~1.0)를 추정하세요.

# 규칙
- 모든 관계는 반드시 'support' 또는 'conflict' 중 하나로만 분류해야 합니다.
- 중립/모호함은 허용되지 않습니다.
- 응답은 반드시 아래 예시와 동일한 JSON 형식이어야 하며, 다른 어떤 텍스트도 포함해서는 안 됩니다.

# 출력 형식 예시
```json
[
  {{ "source": "현진", "target": "유미", "strength": 0.8, "type": "conflict" }},
  {{ "source": "유미", "target": "소피아", "strength": 0.5, "type": "support" }}
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

        parsed = json.loads(json_text)
        return {
            "data": parsed,
            "raw_response": result_text,
            "prompt": prompt
        }
    except (json.JSONDecodeError, TypeError):
        return {
            "error": "Failed to decode JSON from LLM response.",
            "raw_response": result_text,
            "prompt": prompt
        }
