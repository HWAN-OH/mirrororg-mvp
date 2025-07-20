import google.generativeai as genai
import json

PROMPT_FATIGUE_JSON = """
{lang_header}
아래 팀 대화 데이터를 분석하여, 각 팀원별 날짜별 피로도(1~5, 날짜별 시계열)를 아래 JSON 형식으로 출력하세요.

[예시]
[
  {{"name": "현진", "fatigue_timeline": [{{"date": "2025-07-01", "score": 2}}, ...]}},
  {{"name": "유미", "fatigue_timeline": [{{"date": "2025-07-01", "score": 1}}, ...]}}
]

반드시 JSON만 출력하세요. 실패 시 {{"error": "..."}} 형태로 반환하세요.
---
{chat_log}
"""

PROMPT_NETWORK_JSON = """
{lang_header}
아래 팀 대화 데이터를 분석하여, 팀원 간 관계 네트워크를 아래 JSON 형식으로 출력하세요.

[예시]
[
  {{"source": "현진", "target": "유미", "strength": 0.8, "type": "conflict"}},
  {{"source": "유미", "target": "소피아", "strength": 0.5, "type": "support"}}
]

반드시 JSON만 출력하세요. 실패 시 {{"error": "..."}} 형태로 반환하세요.
---
{chat_log}
"""

def call_gemini_api(prompt: str) -> str:
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        safety_settings = [{"category": f"HARM_CATEGORY_{cat}", "threshold": "BLOCK_NONE"} for cat in ["HARASSMENT", "HATE_SPEECH", "SEXUALLY_EXPLICIT", "DANGEROUS_CONTENT"]]
        response = model.generate_content(prompt, safety_settings=safety_settings)
        return response.text
    except Exception as e:
        return json.dumps({"error": f"API 오류: {e}"})

def analyze_fatigue_json(chat_log: str, lang: str = 'ko'):
    lang_header = "[언어: 한국어]" if lang == 'ko' else "[Language: English]"
    prompt = PROMPT_FATIGUE_JSON.format(chat_log=chat_log, lang_header=lang_header)
    result = call_gemini_api(prompt)
    try:
        return json.loads(result)
    except Exception:
        # 디버깅용: 파싱 실패 시 원본 LLM 응답을 함께 반환
        return {"error": "json.loads 실패", "raw_response": result}

def analyze_network_json(chat_log: str, lang: str = 'ko'):
    lang_header = "[언어: 한국어]" if lang == 'ko' else "[Language: English]"
    prompt = PROMPT_NETWORK_JSON.format(chat_log=chat_log, lang_header=lang_header)
    result = call_gemini_api(prompt)
    try:
        return json.loads(result)
    except Exception:
        return {"error": "json.loads 실패", "raw_response": result}
