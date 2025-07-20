import google.generativeai as genai
import json

# 1. 피로도 곡선 분석 프롬프트 (JSON)
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

# 2. 관계 네트워크 분석 프롬프트 (JSON)
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

# 3. 종합 분석 보고서 (한글)
PROMPT_COMPREHENSIVE_REPORT_KO = """
### 페르소나 및 미션 (Persona & Mission)
당신은 '미러오알지(MirrorOrg)' 프레임워크를 실행하는 최고 수준의 AI 조직 분석가입니다.
당신의 유일한 임무는 주어진 팀의 채팅 기록을 분석하여, 팀의 붕괴를 막고 성장을 돕기 위한 **'종합 분석 보고서'**를 작성하는 것입니다.
보고서는 반드시 아래의 모든 지시사항과 출력 템플릿을 엄격하게 준수하여 Markdown 형식으로 작성해야 합니다.

# MirrorOrg 종합 분석 보고서

## 1. 분석 개요
* **분석 기간:** (채팅 기록의 시작 날짜) ~ (채팅 기록의 마지막 날짜)
* **분석 대상:** (채팅 기록에 참여한 주요 인물 목록)
* **핵심 요약:** (분석 결과에 대한 2~3 문장의 핵심 요약)

---

## 2. Phase 1: 진단 (Diagnosis)
### 2.1. 정체성 계수 맵 (Identity Coefficient Map)
* **분석 목적:** 이 분석은 팀원 개개인의 고유한 성향과 역할을 정량화하여, 팀의 전체적인 구성과 강점, 약점을 파악하기 위함입니다.

| 이름 (가명) | 감정 | 사고 | 표현 | 가치 | 편향 | 핵심 역할 |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| (참여자 A) | (점수) | (점수) | (점수) | (점수) | (점수) | (역할) |
| (참여자 B) | (점수) | (점수) | (점수) | (점수) | (점수) | (역할) |

**분석 근거:**
* **[참여자 A 이름]:** (해당 참여자의 계수가 왜 그렇게 판단되었는지, 채팅 내용의 구체적인 예시를 들어 1~2 문장으로 서술)
* **[참여자 B 이름]:** (분석 근거 서술)

---

## 3. Phase 2: 예측 (Prediction)
### 3.1. 피로도 변화 (Fatigue Trajectory)
* **분석 목적:** 이 분석은 시간의 흐름에 따른 팀의 에너지 변화, 즉 '피로도'를 추적하여 잠재적인 번아웃 위기를 미리 예측하고 대비하기 위함입니다.
* **분석 기준:** '피로도'는 업무 부담, 스트레스, 부정적 감정 표현("피곤하다", "ㅠㅠ") 등을 종합하여 판단합니다.

* **주요 관찰 사항:** (예: 프로젝트 마감일이 임박한 X월 말, 특정 팀원(들)의 피로도가 급증하는 패턴이 관찰되었습니다. 이는 '정서적 부채'가 누적되고 있음을 시사합니다.)
* **리스크 분석:** (예: 이러한 피로도 증가는 팀의 번아웃 리스크를 높이며, 특히 감정 계수가 높은 팀원에게 부담이 집중될 수 있습니다.)

### 3.2. 관계 네트워크 (Relationship Network)
* **분석 목적:** 이 분석은 팀원 간 상호작용의 질을 분석하여, 눈에 보이지 않는 잠재적 갈등과 핵심적인 협력 관계를 예측하기 위함입니다.
* **분석 기준:** '갈등'은 명백한 의견 충돌이나 비난 뿐만 아니라, 소통 방식의 차이에서 오는 '구조적 긴장'까지 포함하여 판단합니다.

* **주요 관찰 사항:** (예: 리더인 A의 결과 중심적 소통과, 팀원 B의 상태 표현 중심적 소통 사이에 반복적인 의견 충돌이 관찰되었습니다.)
* **리스크 분석:** (예: 이는 개인의 문제가 아닌, 역할과 소통 방식의 차이에서 오는 '구조적 긴장'입니다. 이 긴장을 중재할 메커니즘이 없다면, 잠재적 갈등으로 발전할 수 있습니다.)

---

## 4. 종합 결론 및 제언
(분석 내용을 종합하여, 이 팀의 가장 큰 시스템적 강점과 리스크는 무엇인지 2~3 문장으로 요약하고, 개선을 위한 간단한 제언을 덧붙입니다.)

### [분석 대상 채팅 기록]
{chat_log}
---
### [종합 분석 보고서 (Markdown 형식)]
"""

# 4. 종합 분석 보고서 (영문, 필요시 사용)
PROMPT_COMPREHENSIVE_REPORT_EN = """
### Persona & Mission
You are a top-level organizational analyst running the 'MirrorOrg' framework. Your mission is to analyze the given team's chat history and generate a **Comprehensive Analysis Report** to prevent collapse and help growth. You MUST strictly follow the below Markdown structure and output template.

# MirrorOrg Comprehensive Analysis Report

## 1. Overview
* **Analysis Period:** (Start date of chat log) ~ (End date)
* **Participants:** (List of key personas)
* **Executive Summary:** (2-3 lines summary)

--- (이하 한국어 프롬프트와 같은 구조, 영어로 출력)

### [Chat Log to Analyze]
{chat_log}
---
### [Comprehensive Analysis Report (Markdown)]
"""

# LLM 호출 함수
def call_gemini_api(prompt: str) -> str:
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        safety_settings = [{"category": f"HARM_CATEGORY_{cat}", "threshold": "BLOCK_NONE"} for cat in ["HARASSMENT", "HATE_SPEECH", "SEXUALLY_EXPLICIT", "DANGEROUS_CONTENT"]]
        response = model.generate_content(prompt, safety_settings=safety_settings)
        return response.text
    except Exception as e:
        return json.dumps({"error": f"API 오류: {e}"})

# 5. 피로도 곡선 챕터 분석 함수 (디버깅: 원본 응답도 반환)
def analyze_fatigue_json(chat_log: str, lang: str = 'ko'):
    lang_header = "[언어: 한국어]" if lang == 'ko' else "[Language: English]"
    prompt = PROMPT_FATIGUE_JSON.format(chat_log=chat_log, lang_header=lang_header)
    result = call_gemini_api(prompt)
    try:
        return json.loads(result)
    except Exception:
        return {"error": "json.loads 실패", "raw_response": result}

# 6. 관계 네트워크 챕터 분석 함수 (디버깅: 원본 응답도 반환)
def analyze_network_json(chat_log: str, lang: str = 'ko'):
    lang_header = "[언어: 한국어]" if lang == 'ko' else "[Language: English]"
    prompt = PROMPT_NETWORK_JSON.format(chat_log=chat_log, lang_header=lang_header)
    result = call_gemini_api(prompt)
    try:
        return json.loads(result)
    except Exception:
        return {"error": "json.loads 실패", "raw_response": result}

# 7. 종합 분석 보고서 (마크다운)
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
    if lang == 'ko':
        prompt = PROMPT_COMPREHENSIVE_REPORT_KO
    else:
        prompt = PROMPT_COMPREHENSIVE_REPORT_EN
    return call_gemini_api_markdown(prompt, raw_chat_content)
