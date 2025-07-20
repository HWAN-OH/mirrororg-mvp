# analyzer.py
# 역할: '분할 정복' 파이프라인을 실행합니다. 1) 참여자 식별, 2) 종합 보고서 생성을 순차적으로 수행합니다.
# 최종 버전: 복잡한 단일 과업을 두 개의 단순한 과업으로 분리하여 LLM의 연산 부담을 줄이고 안정성을 확보합니다.

import google.generativeai as genai
import json
import pandas as pd
import re

# --- [Delta] Stage 1: Participant Identification Prompt ---
PROMPT_GET_PARTICIPANTS = """
### TASK
Your single task is to read the entire chat log and identify all major participants.

### RULES
- List every unique person who speaks.
- You MUST respond with ONLY a valid JSON array of strings, with no other text.

### EXAMPLE OUTPUT
```json
["오승환", "김재용", "양석준", "김진관", "이철욱"]
```

### CHAT LOG TO ANALYZE
{chat_log}
---
### JSON OUTPUT
"""

# --- [Delta] Stage 2: Comprehensive Report Prompt ---
PROMPT_COMPREHENSIVE_REPORT = """
### 페르소나 및 미션 (Persona & Mission)
당신은 '미러오알지(MirrorOrg)' 프레임워크를 실행하는 최고 수준의 AI 조직 분석가입니다.
당신의 임무는 주어진 **'채팅 기록'**과 **'핵심 참여자 목록'**을 바탕으로, 팀의 붕괴를 막고 성장을 돕기 위한 **'종합 분석 보고서'**를 한국어로 작성하는 것입니다.

### 프레임워크 핵심 지식: 미러오알지(MirrorOrg) 방법론
* **정의:** 조직을 '복잡계'로 보고, 정성적 대화를 정량적 데이터와 통찰력으로 변환하여 시스템의 숨겨진 역학을 진단하고 예측하는 프레임워크.
* **프로세스:** 진단 (팀 프로필 분석) → 예측 (피로도 변화, 관계 네트워크 분석)
* **사고 과정 (Chain of Thought):**
    1.  **패턴 인식:** 채팅 기록에서 '프로젝트 에코' 사례와 유사한 패턴을 찾습니다. (예: 특정인의 전략적 발언, 다른 이의 감정적 호소, 의견 충돌 등)
    2.  **지식 연결:** 인식된 패턴을 '미러오알지'의 개념(정체성 계수, 정서적 부채, 구조적 긴장 등)과 연결하여 해석합니다.
    3.  **보고서 작성:** 해석된 내용을 바탕으로, 아래의 보고서 형식에 맞춰 각 섹션을 채워나갑니다.

---
### 최종 보고서 출력 형식 (Markdown)

# MirrorOrg 종합 분석 보고서

## 1. 분석 개요
* **분석 기간:** [채팅 기록의 시작 날짜] ~ [채팅 기록의 마지막 날짜]
* **분석 대상:** {participants_list}
* **핵심 요약:** (분석 결과에 대한 2~3 문장의 핵심 요약)

---

## 2. Phase 1: 진단 (Diagnosis)
### 2.1. 정체성 계수 맵 (Identity Coefficient Map)
| 이름 (가명) | 감정 | 사고 | 표현 | 가치 | 편향 | 핵심 역할 |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| (참여자 A) | (점수) | (점수) | (점수) | (점수) | (점수) | (역할) |

**분석 근거:**
* **[참여자 A 이름]:** (채팅 내용의 구체적인 예시를 들어 1~2 문장으로 서술)

---

## 3. Phase 2: 예측 (Prediction)
### 3.1. 피로도 변화 (Fatigue Trajectory)
* **주요 관찰 사항:** (예: X월 말, 특정 팀원의 피로도가 급증하는 패턴이 관찰되었습니다.)
* **리스크 분석:** (예: 이러한 피로도 증가는 팀의 번아웃 리스크를 높입니다.)

### 3.2. 관계 네트워크 (Relationship Network)
* **주요 관찰 사항:** (예: 리더 A와 팀원 B 사이에 반복적인 의견 충돌이 관찰되었습니다.)
* **리스크 분석:** (예: 이는 '구조적 긴장'이며, 중재 메커니즘 부재 시 갈등으로 발전할 수 있습니다.)

---

## 4. 종합 결론 및 제언
(분석 내용을 종합하여, 이 팀의 가장 큰 시스템적 강점과 리스크는 무엇인지 요약하고, 개선을 위한 제언을 덧붙입니다.)

---
### [분석 대상 채팅 기록]
{chat_log}
---
### [종합 분석 보고서 (Markdown 형식)]
"""

def call_gemini_api(prompt: str, is_json_output: bool, **kwargs) -> dict | list | str | None:
    """
    Calls the Gemini API. Dynamically formats the prompt with provided arguments.
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        safety_settings = [{"category": f"HARM_CATEGORY_{cat}", "threshold": "BLOCK_NONE"} for cat in ["HARASSMENT", "HATE_SPEECH", "SEXUALLY_EXPLICIT", "DANGEROUS_CONTENT"]]
        
        full_prompt = prompt.format(**kwargs)
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

def get_participants(raw_chat_content: str) -> list | str | None:
    """
    Step 1: Get a list of participants from the chat log.
    """
    return call_gemini_api(PROMPT_GET_PARTICIPANTS, is_json_output=True, chat_log=raw_chat_content)

def generate_report(raw_chat_content: str, participants: list, lang: str = 'ko') -> str | None:
    """
    Step 2: Generate the full report using the chat log and the list of participants.
    """
    # Convert list to a comma-separated string for the prompt
    participants_str = ", ".join(participants)
    return call_gemini_api(PROMPT_COMPREHENSIVE_REPORT, is_json_output=False, chat_log=raw_chat_content, participants_list=participants_str)
