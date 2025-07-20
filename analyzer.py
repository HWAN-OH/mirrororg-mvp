# analyzer.py
# 역할: 원본 채팅 기록을 직접 분석하여, 각 시각화에 필요한 데이터를 개별적으로 생성합니다.
# 최종 버전: 각 프롬프트에 '강제 데이터 반환 템플릿'을 명시하여 AI 응답의 구조를 고정합니다.

import google.generativeai as genai
import json
import pandas as pd
import re

# --- [Lumina & Delta] Final Templated Prompts ---

PROMPT_HEADER = """
### 페르소나 및 미션 (Persona & Mission)
당신은 '미러오알지(MirrorOrg)' 프레임워크를 실행하는 AI 조직 분석가입니다. 당신의 유일한 임무는 주어진 원본 채팅 기록을 분석하여, 요청된 특정 데이터를 지정된 JSON 템플릿에 맞춰 정확하게 반환하는 것입니다.

### 사고 과정 (Chain of Thought)
1.  **입력 해석:** 먼저, 주어진 원본 채팅 기록 전체를 읽고 날짜, 발언자, 메시지 내용을 파악합니다.
2.  **핵심 패턴 인식:** '프로젝트 에코' 사례와 같은 핵심 패턴(전략적 발언, 감정적 호소, 의견 충돌 등)을 식별합니다.
3.  **데이터 추출:** 식별된 패턴을 바탕으로, 아래 요청된 데이터 형식에 맞는 값들을 추출합니다.
4.  **템플릿 적용:** 추출된 값들을 '데이터 반환 템플릿'에 정확히 맞춰 삽입하여 최종 JSON을 생성합니다.
---
"""

PROMPT_TEAM_PROFILE = PROMPT_HEADER + """
### 현재 임무: 팀 프로필 데이터 생성

**[작업 지시]**
채팅 기록을 분석하여, 각 팀원의 '5대 정체성 계수'와 '핵심 역할'을 추출하십시오.

**[데이터 반환 템플릿 (필수 준수)]**
* 당신은 반드시 아래와 동일한 구조의 JSON 배열(Array)만 반환해야 합니다.
* 다른 어떤 설명이나 텍스트도 포함해서는 안 됩니다.

```json
[
  {
    "name": "참여자 이름",
    "emotion_score": 5,
    "cognition_score": 9,
    "expression_score": 6,
    "value_score": 9,
    "bias_score": 7,
    "core_role": "The Driver (전략 중심)"
  }
]
```

---
**[분석 대상 원본 채팅 기록]**
{chat_log}
---
**[JSON 데이터 출력]**
"""

PROMPT_FATIGUE_TIMELINE = PROMPT_HEADER + """
### 현재 임무: 피로도 시계열 데이터 생성

**[작업 지시]**
채팅 기록을 분석하여, 날짜별 각 팀원의 '피로도'를 1-10점 척도로 추출하십시오.

**[데이터 반환 템플릿 (필수 준수)]**
* 당신은 반드시 아래와 동일한 구조의 JSON 객체(Object)만 반환해야 합니다.
* 키는 "YYYY-MM-DD" 형식의 날짜 문자열이어야 합니다.
* 다른 어떤 설명이나 텍스트도 포함해서는 안 됩니다.

```json
{
  "2023-10-20": {
    "참여자 A": 5,
    "참여자 B": 9
  },
  "2023-10-21": {
    "참여자 A": 3,
    "참여자 B": 4
  }
}
```

---
**[분석 대상 원본 채팅 기록]**
{chat_log}
---
**[JSON 데이터 출력]**
"""

PROMPT_CONFLICT_NETWORK = PROMPT_HEADER + """
### 현재 임무: 관계 네트워크 데이터 생성

**[작업 지시]**
채팅 기록을 분석하여, 팀원 간의 관계를 '노드(nodes)'와 '엣지(edges)' 데이터로 추출하십시오.

**[데이터 반환 템플릿 (필수 준수)]**
* 당신은 반드시 "nodes"와 "edges"라는 두 개의 키를 가진 JSON 객체(Object)만 반환해야 합니다.
* 엣지의 'type'은 반드시 `high_risk`, `medium_risk`, `potential_risk`, `stable` 중 하나여야 합니다.
* 다른 어떤 설명이나 텍스트도 포함해서는 안 됩니다.

```json
{
  "nodes": [
    {"id": "참여자 A", "label": "참여자 A"},
    {"id": "참여자 B", "label": "참여자 B"}
  ],
  "edges": [
    {"from": "참여자 A", "to": "참여자 B", "type": "medium_risk"}
  ]
}
```

---
**[분석 대상 원본 채팅 기록]**
{chat_log}
---
**[JSON 데이터 출력]**
"""

def call_gemini_api(prompt: str, chat_log: str) -> dict | list | str | None:
    """
    Calls the Gemini API. If JSON parsing fails, returns the raw text for debugging.
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        safety_settings = [{"category": f"HARM_CATEGORY_{cat}", "threshold": "BLOCK_NONE"} for cat in ["HARASSMENT", "HATE_SPEECH", "SEXUALLY_EXPLICIT", "DANGEROUS_CONTENT"]]
        
        full_prompt = prompt.format(chat_log=chat_log)
        response = model.generate_content(full_prompt, safety_settings=safety_settings)

        if not response.parts:
            return {"error": "API response was blocked or empty."}

        raw_text = response.text
        match = re.search(r"```json\s*([\s\S]*?)\s*```", raw_text)
        json_text = match.group(1) if match else raw_text.strip()
        
        if not json_text:
            return {"error": "API returned an empty response after cleaning."}
            
        return json.loads(json_text)
    except json.JSONDecodeError:
        return raw_text 
    except Exception as e:
        return {"error": f"An unexpected API error occurred: {str(e)}"}

def analyze_profile(raw_chat_content: str) -> dict | list | str | None:
    return call_gemini_api(PROMPT_TEAM_PROFILE, raw_chat_content)

def analyze_timeline(raw_chat_content: str) -> dict | list | str | None:
    return call_gemini_api(PROMPT_FATIGUE_TIMELINE, raw_chat_content)

def analyze_network(raw_chat_content: str) -> dict | list | str | None:
    return call_gemini_api(PROMPT_CONFLICT_NETWORK, raw_chat_content)
