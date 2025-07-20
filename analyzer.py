import openai
import json
import streamlit as st

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ▶ 공란/X 불허, 예시·강제 포함한 종합 분석 프롬프트
PROMPT_COMPREHENSIVE_REPORT_KO = """
# MirrorOrg 종합 분석 보고서 (테스트용)
## 1. 분석 개요
* 분석 기간: (시작~끝)
* 분석 대상: (참여 인물)
* 핵심 요약: (2~3줄)
## 2. Phase 1: 진단 (Diagnosis)
### 2.1. 정체성 계수 맵
아래 표를 반드시 **모든 칸을 추정값(숫자/특성/역할 등)으로 채워서** 작성하세요. **X/공란/비움 불허.**  
대화 데이터에 근거가 불충분하더라도, 각 인물의 메시지 스타일·주요 발언·행동에서 유추하여 가장 유력한 수치/특성을 입력하세요.

#### 예시:
| 이름 | 감정 | 사고 | 표현 | 가치 | 편향 | 역할 |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| 김재용 | 3(안정) | 4(분석적) | 2(직설) | 5(협력) | 1(중립) | 조율자 |
| 오승환 | 2(민감) | 3(균형) | 4(외향) | 4(경쟁) | 2(낙관) | 촉진자 |
각 항목은 아래 기준을 참고해 수치/특성/역할로 반드시 채워서 작성하세요:
- 감정/사고/표현/가치/편향: 1~5 점수(숫자) + 간단한 특성명 (예: 3(분석적), 5(외향), 2(협력), ...)
- 역할: 한글 단어로 예시(조율자/촉진자/중재자/분석가/실행가 등)
#### 만약 근거가 불확실할 경우, 가장 가능성 높은 값을 입력하세요. X/공란/비움/불명 불허!

| 이름 | 감정 | 사고 | 표현 | 가치 | 편향 | 역할 |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
(여기에 분석 결과 채우기)
- 각 인물별 주요 메시지/행동 근거도 1줄씩 표 아래에 작성.

---
## 3. Phase 2: 예측 (Prediction)
### 3.1. 피로도 변화
- 피로도 변화 및 리스크 요약, 반드시 “수치/시계열 근거” 포함
### 3.2. 관계 네트워크
- 반드시 각 관계를 'support'(지지) 또는 'conflict'(갈등)으로만 명확하게 분류(중립/모호 불허), 근거를 1줄씩 명시.
## 4. 결론 및 제언
- (2~3줄 요약)
- 반드시 **구체적 실행방안·조직개선 대안**을 bullet point로 2가지 이상 제시. 
- 대안은 실제 조직에서 바로 실행 가능한 액션이어야 함.
- 분석 결과의 한계/면책(예: “이 결과는 실제 인격이 아니라 행동 데이터 기반 임시 진단”임을 명확히 명시)
---
본 결과는 테스트 목적이며, 실사용 전 전문가 검증이 필요합니다.
분석 대상 채팅 기록:
{chat_log}
"""

PROMPT_COMPREHENSIVE_REPORT_KO_SAMPLE = PROMPT_COMPREHENSIVE_REPORT_KO.replace(
    "전체를 분석하여", "최근 2개월(2000줄 이내) 기준으로 분석하여"
)

PROMPT_COMPREHENSIVE_REPORT_EN = """
# MirrorOrg Comprehensive Analysis Report (Test version)
## 1. Overview
* Period: (start~end)
* Participants: (...)
* Executive Summary: (2~3 lines)
## 2. Phase 1: Diagnosis
### 2.1. Identity Coefficient Map
| Name | Emotion | Cognition | Expression | Value | Bias | Role |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| (A) | | | | | | |
- Write at least 1 line of evidence/basis for each person.
---
## 3. Phase 2: Prediction
### 3.1. Fatigue Trajectory
- Summarize fatigue trends/risks with explicit timeline/numerical evidence.
### 3.2. Relationship Network
- Force all relationships to be classified as 'support' or 'conflict' only (no neutral/unknown); include 1 line of evidence for each.
## 4. Conclusion & Recommendations
- 2~3 lines summary.
- Bullet point at least 2 **actionable recommendations** (must be concrete and practical).
- Clearly state that the analysis is test/prototype, behavior-based, and not a personality/character judgment.
---
This result is for testing only and needs further expert validation before real use.
Chat log:
{chat_log}
"""

# ▶ 피로도 분석 JSON 프롬프트 (꼭 포함!)
PROMPT_FATIGUE_JSON = """
아래 팀 대화 데이터를 분석하여, 각 팀원별 날짜별 피로도(1~5, 날짜별 시계열)를 아래 JSON 형식으로 출력하세요.
[예시]
[
  {"name": "현진", "fatigue_timeline": [{"date": "2025-07-01", "score": 2}, ...]},
  {"name": "유미", "fatigue_timeline": [{"date": "2025-07-01", "score": 1}, ...]}
]
피로도 추정이 불가능하면 각 팀원별로 'score': 3(중립값)로 채워 반드시 반환하세요. 설명문, 오류만 반환 금지.
---
{chat_log}
"""

# ▶ 관계 네트워크 분석 JSON 프롬프트 (꼭 포함!)
PROMPT_NETWORK_JSON = """
아래 팀 대화 데이터를 분석하여, 반드시 각 관계를 'support'(지지/긍정) 또는 'conflict'(갈등/부정) 중 하나로 강제 분류해 아래 JSON 형식으로 출력하세요.
[예시]
[
  {"source": "현진", "target": "유미", "strength": 0.8, "type": "conflict"},
  {"source": "유미", "target": "소피아", "strength": 0.5, "type": "support"}
]
type은 반드시 'support' 또는 'conflict'로만 작성(unknown/neutral 불허). 각 링크에 간단 근거(1줄) 포함.
---
{chat_log}
"""

def call_openai_api(prompt: str, model="gpt-3.5-turbo", max_tokens=2048) -> str:
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.5,
        )
        return response.choices[0].message.content
    except Exception as e:
        return json.dumps({"error": f"API 오류: {e}"})

def analyze_fatigue_json(chat_log: str, lang: str = 'ko'):
    prompt = PROMPT_FATIGUE_JSON.format(chat_log=chat_log)
    result = call_openai_api(prompt)
    try:
        return json.loads(result)
    except Exception:
        return {"error": "json.loads 실패", "raw_response": result}

def analyze_network_json(chat_log: str, lang: str = 'ko'):
    prompt = PROMPT_NETWORK_JSON.format(chat_log=chat_log)
    result = call_openai_api(prompt)
    try:
        return json.loads(result)
    except Exception:
        return {"error": "json.loads 실패", "raw_response": result}

def generate_report(raw_chat_content: str, lang: str = 'ko', sample_mode=False) -> str:
    if lang == 'ko':
        prompt = PROMPT_COMPREHENSIVE_REPORT_KO_SAMPLE if sample_mode else PROMPT_COMPREHENSIVE_REPORT_KO
    else:
        prompt = PROMPT_COMPREHENSIVE_REPORT_EN
    result = call_openai_api(prompt.format(chat_log=raw_chat_content), max_tokens=2048)
    return result
