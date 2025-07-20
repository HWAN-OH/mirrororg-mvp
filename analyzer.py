# analyzer.py
# 역할: 보고서의 텍스트 부분과 시각화를 위한 구조화된 데이터를 별도로 생성합니다.
# 최종 버전: 텍스트 생성과 데이터 추출 임무를 분리하여 안정성과 결과물의 질을 극대화합니다.

import google.generativeai as genai
import json
import pandas as pd
import re

# --- [Delta] Prompt 1: For Generating Structured Data for Visualizations ---
PROMPT_GRAPH_DATA = """
### TASK
Analyze the provided raw chat log and extract structured data for three specific visualizations: Team Profile, Fatigue Timeline, and Relationship Network. You MUST respond with a single, valid JSON object containing three keys: "profile_data", "timeline_data", and "network_data". Adhere strictly to the format described below.

### OUTPUT JSON STRUCTURE
```json
{
  "profile_data": [
    {"name": "Participant Name", "emotion_score": 5, "cognition_score": 8, "expression_score": 7, "value_score": 9, "bias_score": 4, "core_role": "The Driver"}
  ],
  "timeline_data": {
    "YYYY-MM-DD": {
      "Participant Name": 5
    }
  },
  "network_data": {
    "nodes": [
      {"id": "Participant Name", "label": "Participant Name"}
    ],
    "edges": [
      {"from": "Participant Name 1", "to": "Participant Name 2", "type": "stable"}
    ]
  }
}
```

### CHAT LOG TO ANALYZE
{chat_log}
---
### JSON OUTPUT
"""

# --- [Delta] Prompt 2: For Generating the Narrative Report Text ---
PROMPT_REPORT_TEXT_KO = """
### 페르소나 및 미션
당신은 '미러오알지(MirrorOrg)' 프레임워크를 실행하는 AI 조직 분석가입니다. 당신의 임무는 주어진 채팅 기록을 분석하여, **보고서의 텍스트 부분만** 한국어로 작성하는 것입니다. 데이터 테이블과 그래프는 외부에서 별도로 생성되므로, 당신은 오직 서사와 통찰력에만 집중해야 합니다.

### 최종 보고서 텍스트 출력 형식 (Markdown, 한국어)

# MirrorOrg 종합 분석 보고서

## 1. 분석 개요
* **분석 기간:** [채팅 기록의 시작 날짜] ~ [채팅 기록의 마지막 날짜]
* **분석 대상:** [채팅 기록에 참여한 주요 인물 목록]
* **핵심 요약:** (분석 결과에 대한 2~3 문장의 핵심 요약. 예: "이 팀은 A의 강력한 리더십을 바탕으로 높은 성과를 보이지만, B와 C에게 '정서적 부채'가 누적되어 번아웃 위기가 예측됩니다.")

---

## 2. Phase 1: 진단 (Diagnosis)
### 2.1. 정체성 계수 맵 (Identity Coefficient Map)
(팀의 전체적인 구성과 각 팀원의 역할에 대한 통찰을 1~2 문단으로 서술합니다. 데이터 테이블은 외부에서 생성되므로 여기에 포함하지 마십시오.)

---

## 3. Phase 2: 예측 (Prediction)
### 3.1. 피로도 변화 (Fatigue Trajectory)
* **주요 관찰 사항:** (그래프에서 나타날 피로도 변화의 핵심 패턴을 텍스트로 설명합니다. 예: X월 말, 특정 팀원의 피로도가 급증하는 패턴이 관찰되었습니다.)
* **리스크 분석:** (관찰된 패턴이 의미하는 시스템적 리스크를 분석합니다. 예: 이러한 피로도 증가는 팀의 번아웃 리스크를 높입니다.)

### 3.2. 관계 네트워크 (Relationship Network)
* **주요 관찰 사항:** (그래프에서 나타날 관계의 핵심 패턴을 텍스트로 설명합니다. 예: 리더 A와 팀원 B 사이에 반복적인 의견 충돌이 관찰되었습니다.)
* **리스크 분석:** (관찰된 패턴이 의미하는 시스템적 리스크를 분석합니다. 예: 이는 개인의 문제가 아닌, '구조적 긴장'이며 중재 메커니즘 부재 시 갈등으로 발전할 수 있습니다.)

---

## 4. 종합 결론 및 제언
(분석 내용을 종합하여, 이 팀의 가장 큰 시스템적 강점과 리스크는 무엇인지 2~3 문장으로 요약하고, 개선을 위한 간단한 제언을 덧붙입니다.)

---
### [분석 대상 채팅 기록]
{chat_log}
---
### [분석 보고서 (텍스트 전용, Markdown, 한국어)]
"""

PROMPT_REPORT_TEXT_EN = """
### Persona & Mission
You are a world-class AI organizational analyst executing the 'MirrorOrg' framework. Your sole mission is to analyze the provided chat log and write **only the textual parts of the report** in English. Data tables and graphs will be generated externally, so you must focus exclusively on narrative and insight.

### Final Report Text Output Format (Markdown, English)

# MirrorOrg Comprehensive Analysis Report

## 1. Analysis Overview
* **Analysis Period:** [Start date of chat log] - [End date of chat log]
* **Participants:** [List of key participants]
* **Executive Summary:** (A 2-3 sentence summary of the key findings. e.g., "The team demonstrates high performance under A's strong leadership, but a burnout risk is predicted due to accumulating 'Emotional Debt' on members B and C.")

---

## 2. Phase 1: Diagnosis
### 2.1. Identity Coefficient Map
(Provide a 1-2 paragraph analysis of the team's composition and member roles. Do not include the data table here as it will be generated externally.)

---

## 3. Phase 2: Prediction
### 3.1. Fatigue Trajectory
* **Key Observation:** (Describe the key pattern of fatigue changes that will be shown in the graph. e.g., "A pattern of spiking fatigue was observed for certain members in late [Month].")
* **Risk Analysis:** (Analyze the systemic risk implied by the pattern. e.g., "This trend increases the team's risk of burnout.")

### 3.2. Relationship Network
* **Key Observation:** (Describe the key relationship patterns that will be shown in the graph. e.g., "Recurring disagreements were observed between leader A and member B.")
* **Risk Analysis:** (Analyze the systemic risk implied by the pattern. e.g., "This represents a 'structural tension' rather than a personal issue.")

---

## 4. Conclusion & Recommendations
(Summarize the team's greatest systemic strengths and risks and add brief recommendations for improvement.)

---
### [Chat Log for Analysis]
{chat_log}
---
### [Analysis Report (Text-Only, Markdown, English)]
"""


def call_gemini_api(prompt: str, chat_log: str, is_json_output: bool) -> dict | list | str | None:
    """
    Calls the Gemini API. Handles both JSON and text outputs.
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        safety_settings = [{"category": f"HARM_CATEGORY_{cat}", "threshold": "BLOCK_NONE"} for cat in ["HARASSMENT", "HATE_SPEECH", "SEXUALLY_EXPLICIT", "DANGEROUS_CONTENT"]]
        
        full_prompt = prompt.format(chat_log=chat_log)
        response = model.generate_content(full_prompt, safety_settings=safety_settings)

        if not response.parts:
            return {"error": "API response was blocked."} if is_json_output else "## 분석 실패\n\nAPI가 응답 생성을 거부했습니다."

        raw_text = response.text
        if not is_json_output:
            return raw_text

        match = re.search(r"```json\s*([\s\S]*?)\s*```", raw_text)
        json_text = match.group(1) if match else raw_text.strip()
        
        if not json_text:
            return {"error": "API returned an empty response."}
            
        return json.loads(json_text)
    except json.JSONDecodeError:
        return raw_text 
    except Exception as e:
        return {"error": f"An unexpected API error occurred: {str(e)}"}

def generate_graph_data(raw_chat_content: str) -> dict | str | None:
    """
    Generates structured JSON data for all visualizations.
    """
    return call_gemini_api(PROMPT_GRAPH_DATA, raw_chat_content, is_json_output=True)

def generate_report_text(raw_chat_content: str, lang: str = 'ko') -> str | None:
    """
    Generates the narrative part of the report in the specified language.
    """
    prompt = PROMPT_REPORT_TEXT_KO if lang == 'ko' else PROMPT_REPORT_TEXT_EN
    return call_gemini_api(prompt, raw_chat_content, is_json_output=False)
