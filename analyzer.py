import openai
import json
import streamlit as st

# 1. OpenAI 최신 방식: 인스턴스 생성 (api_key는 streamlit secrets.toml에 저장)
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 2. 프롬프트 (필요시 언어별 분기 가능)
PROMPT_FATIGUE_JSON = """
아래 팀 대화 데이터를 분석하여, 각 팀원별 날짜별 피로도(1~5, 날짜별 시계열)를 아래 JSON 형식으로 출력하세요.
[예시]
[
  {{"name": "현진", "fatigue_timeline": [{{"date": "2025-07-01", "score": 2}}, ...]}},
  {{"name": "유미", "fatigue_timeline": [{{"date": "2025-07-01", "score": 1}}, ...]}}
]
피로도 추정이 불가능하면 각 팀원별로 'score': 3(중립값)로 채워 반드시 반환하세요. 설명문, 오류만 반환 금지.
---
{chat_log}
"""

PROMPT_NETWORK_JSON = """
아래 팀 대화 데이터를 분석하여, 팀원 간 관계 네트워크를 아래 JSON 형식으로 출력하세요.
[예시]
[
  {{"source": "현진", "target": "유미", "strength": 0.8, "type": "conflict"}},
  {{"source": "유미", "target": "소피아", "strength": 0.5, "type": "support"}}
]
실제 3회 이상 상호작용이 있는 인물 쌍만 포함. 없으면 빈 배열([]) 반환. 설명문/오류만 반환 금지.
---
{chat_log}
"""

PROMPT_COMPREHENSIVE_REPORT_KO = """
당신은 '미러오알지(MirrorOrg)' 프레임워크를 실행하는 최고 수준의 AI 조직 분석가입니다.
주어진 팀 채팅 기록을 분석하여, 아래 템플릿의 **종합 분석 보고서**를 반드시 마크다운으로 출력하세요.
# MirrorOrg 종합 분석 보고서

## 1. 분석 개요
* 분석 기간: (시작~끝)
* 분석 대상: (참여 인물)
* 핵심 요약: (2~3줄)

## 2. Phase 1: 진단 (Diagnosis)
### 2.1. 정체성 계수 맵
| 이름 | 감정 | 사고 | 표현 | 가치 | 편향 | 역할 |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| (A) | | | | | | |
분석 근거:
* A: (채팅 예시 근거)
---

## 3. Phase 2: 예측 (Prediction)
### 3.1. 피로도 변화
- 피로도 주요 변화/리스크 요약

### 3.2. 관계 네트워크
- 관계 변화/갈등 요약

## 4. 결론 및 제언
(2~3줄 요약 및 개선 제언)
---
분석 대상 채팅 기록:
{chat_log}
"""

PROMPT_COMPREHENSIVE_REPORT_EN = """
You are an expert analyst running the 'MirrorOrg' framework. Analyze the given team's chat log and output the below **comprehensive report** in markdown.
# MirrorOrg Comprehensive Analysis Report

## 1. Overview
* Period: (start~end)
* Participants: (...)
* Executive Summary: (2~3 lines)

## 2. Phase 1: Diagnosis
### 2.1. Identity Coefficient Map
| Name | Emotion | Cognition | Expression | Value | Bias | Role |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| (A) | | | | | | |
Basis:
* A: (evidence from chat)
---

## 3. Phase 2: Prediction
### 3.1. Fatigue Trajectory
- Fatigue trends/risks summary

### 3.2. Relationship Network
- Key relationship/conflict summary

## 4. Conclusion & Recommendations
(2~3 lines of summary and improvement advice)
---
Chat log:
{chat_log}
"""

# 3. LLM 호출 함수 (최신 방식)
def call_openai_api(prompt: str, model="gpt-3.5-turbo", max_tokens=2048) -> str:
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.2,
        )
        return response.choices[0].message.content
    except Exception as e:
        return json.dumps({"error": f"API 오류: {e}"})

# 4. 피로도 곡선 분석
def analyze_fatigue_json(chat_log: str, lang: str = 'ko'):
    prompt = PROMPT_FATIGUE_JSON.format(chat_log=chat_log)
    result = call_openai_api(prompt)
    try:
        return json.loads(result)
    except Exception:
        return {"error": "json.loads 실패", "raw_response": result}

# 5. 관계 네트워크 분석
def analyze_network_json(chat_log: str, lang: str = 'ko'):
    prompt = PROMPT_NETWORK_JSON.format(chat_log=chat_log)
    result = call_openai_api(prompt)
    try:
        return json.loads(result)
    except Exception:
        return {"error": "json.loads 실패", "raw_response": result}

# 6. 종합 보고서 생성 (마크다운)
def generate_report(raw_chat_content: str, lang: str = 'ko') -> str:
    if lang == 'ko':
        prompt = PROMPT_COMPREHENSIVE_REPORT_KO
    else:
        prompt = PROMPT_COMPREHENSIVE_REPORT_EN
    result = call_openai_api(prompt.format(chat_log=raw_chat_content), max_tokens=2048)
    return result
