# analyzer.py
import google.generativeai as genai
import json

# (필요 시) API Key 설정은 app.py에서 진행됨

# ----- LLM 프롬프트 -----

PROMPT_FATIGUE_JSON = """
아래 팀 대화 데이터를 분석하여, 각 팀원별 날짜별 피로도(1~5, 날짜별 시계열)를 아래 JSON 형식으로 출력하세요.

[예시]
[
  {"name": "현진", "fatigue_timeline": [{"date": "2025-07-01", "score": 2}, ...]},
  {"name": "유미", "fatigue_timeline": [{"date": "2025-07-01", "score": 1}, ...]}
]

반드시 JSON만 출력하세요. 실패 시 {"error": "..."} 형태로 반환하세요.

---
{chat_log}
"""

PROMPT_NETWORK_JSON = """
아래 팀 대화 데이터를 분석하여, 팀원 간 관계 네트워크를 아래 JSON 형식으로 출력하세요.

[예시]
[
  {"source": "현진", "target": "유미", "strength": 0.8, "type": "conflict"},
  {"source": "유미", "target": "소피아", "strength": 0.5, "type": "support"}
]

반드시 JSON만 출력하세요. 실패 시 {"error": "..."} 형태로 반환하세요.

---
{chat_log}
"""

# --- 종합 분석 마크다운 보고서 프롬프트 (기존) ---
PROMPT_COMPREHENSIVE_REPORT = """
### 페르소나 및 미션 (Persona & Mission)
당신은 '미러오알지(MirrorOrg)' 프레임워크를 실행하는 최고 수준의 AI 조직 분석가입니다.
당신의 유일한 임무는 주어진 팀의 채팅 기록을 분석하여, 팀의 붕괴를 막고 성장을 돕기 위한 **'종합 분석 보고서'**를 작성하는 것입니다.
보고서는 반드시 아래의 모든 지시사항과 출력 템플릿을 엄격하게 준수하여 Markdown 형식으로 작성해야 합니다.
... (중략, 기존 프롬프트 그대로 유지) ...
### [분석 대상 채팅 기록]
{chat_log}
---
### [종합 분석 보고서 (Markdown 형식)]
"""

def call_gemini_api(prompt: str) -> str:
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        safety_settings = [{"category": f"HARM_CATEGORY_{cat}", "threshold": "BLOCK_NONE"} for cat in ["HARASSMENT", "HATE_SPEECH", "SEXUALLY_EXPLICIT", "DANGEROUS_CONTENT"]]
        response = model.generate_content(prompt, safety_settings=safety_settings)
        return response.text
    except Exception as e:
        return json.dumps({"error": f"API 오류: {e}"})

def analyze_fatigue_json(chat_log: str):
    prompt = PROMPT_FATIGUE_JSON.format(chat_log=chat_log)
    result = call_gemini_api(prompt)
    try:
        return json.loads(result)
    except Exception:
        return None

def analyze_network_json(chat_log: str):
    prompt = PROMPT_NETWORK_JSON.format(chat_log=chat_log)
    result = call_gemini_api(prompt)
    try:
        return json.loads(result)
    except Exception:
        return None

def call_gemini_api_markdown(prompt: str, chat_log: str) -> str:
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        safety_settings = [{"category": f"HARM_CATEGORY_{cat}", "threshold": "BLOCK_NONE"} for cat in ["HARASSMENT", "HATE_SPEECH", "SEXUALLY_EXPLICIT", "DANGEROUS_CONTENT"]]
        full_prompt = prompt.format(chat_log=chat_log)
        response = model.generate_content(full_prompt, safety_settings=safety_settings)
        return response.text
    except Exception as e:
        return f"## 분석 실패\n\nAPI 오류: {e}"

def generate_report(raw_chat_content: str, lang: str = 'ko') -> str:
    prompt = PROMPT_COMPREHENSIVE_REPORT
    return call_gemini_api_markdown(prompt, raw_chat_content)
