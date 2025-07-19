# analyzer.py
# 역할: 파싱된 데이터를 받아 LLM API와 통신하고, 분석 결과를 생성합니다.
# 최종 버전: AI에게 '미러오알지'의 핵심 지식과 함께, 그 지식을 실제 데이터에 적용하는 '사고 과정(Chain of Thought)'을 주입합니다.

import google.generativeai as genai
import json
import pandas as pd
import re

# --- [Lumina & Delta] MirrorOrg Knowledge & Chain of Thought Imprinting ---

PROMPT_KNOWLEDGE_BASE = """
### 프레임워크 핵심 지식: 미러오알지(MirrorOrg) 방법론

**1. 정의 (Definition):**
'미러오알지(MirrorOrg)'는 인간 조직을 하나의 살아있는 '복잡계(Complex System)'로 간주하는 분석 프레임워크입니다. 조직의 붕괴는 개인의 실패가 아닌 '시스템 설계의 실패'라는 관점에서 출발합니다. 당신의 임무는 대화 기록을 분석하여 이 보이지 않는 시스템의 동역학을 데이터로 모델링하는 것입니다.

**2. 프로세스 (Process): 진단 → 예측 → 처방**
* **진단 (Diagnosis):** 팀의 현재 상태를 데이터로 객관화합니다. (예: 팀 프로필 분석)
* **예측 (Prediction):** 진단된 데이터를 기반으로 미래의 리스크를 예측합니다. (예: 피로도 변화, 관계 네트워크 분석)

**3. 접근 방식 (Approach): 정성적 대화의 정량적 모델링**
당신의 핵심 역할은 팀원들의 정성적인 대화를 '정체성 계수', '피로도', '관계'와 같은 정량적인 데이터(JSON)로 변환하는 것입니다.

---
"""

# --- 1. 팀 프로필 분석 프롬프트 ---
PROMPT_TEAM_PROFILE = PROMPT_KNOWLEDGE_BASE + """
### 현재 임무: 팀 프로필 진단 (Phase 1: Diagnosis)

**1. 임무 목표:**
'진단' 단계의 핵심 임무로, 팀원 개개인의 성향과 역할을 정량적인 '정체성 계수'로 변환합니다.

**2. 사고 과정 예시 (Chain of Thought Example):**
* **입력 관찰:** 대화에서 "금일까지 달라고 합니다", "대박의 느낌이 난다"와 같이 명확한 지시나 전략적 발언이 관찰된다.
* **지식 연결:** 이는 '프로젝트 에코' 사례의 리더 'Julian'의 패턴과 유사하다. Julian은 높은 '사고(Cognition)'와 '가치(Value)' 계수를 가졌다.
* **결론 도출:** 따라서 이 발언을 한 사람의 '사고'와 '가치' 계수를 높게 평가한다.
* **입력 관찰:** "숨이 너무 차네요", "ㅠㅠㅠ"와 같이 자신의 상태나 감정을 직접적으로 표현하는 발언이 관찰된다.
* **지식 연결:** 이는 '프로젝트 에코' 사례의 'Sophia'나 'Chloe'의 패턴과 유사하다. 이들은 높은 '감정(Emotion)'과 '표현(Expression)' 계수를 가졌다.
* **결론 도출:** 따라서 이 발언을 한 사람의 '감정'과 '표현' 계수를 높게 평가한다.

**3. 최종 출력 규칙:**
위 사고 과정에 따라, 주어진 채팅 기록 전체를 분석하여 모든 참여자에 대한 '5대 정체성 계수'와 '핵심 역할'을 **반드시 아래 JSON 형식으로만** 출력해야 합니다.

```json
[
  {"name": "참여자 이름", "emotion_score": 5, "cognition_score": 9, "expression_score": 6, "value_score": 9, "bias_score": 7, "core_role": "The Driver (전략 중심)"}
]
```
* **실패 규칙:** 분석이 불가능할 경우, `{"error": "분석할 데이터가 부족하여 팀 프로필을 생성할 수 없습니다."}` 형식의 JSON을 반환해야 합니다.

---
**[실제 분석 대상 입력]**
{chat_log}
---
**[실제 분석 결과 출력 (JSON 형식)]**
"""

# --- 2. 피로도 타임라인 분석 프롬프트 ---
PROMPT_FATIGUE_TIMELINE = PROMPT_KNOWLEDGE_BASE + """
### 현재 임무: 피로도 변화 예측 (Phase 2: Prediction)

**1. 임무 목표:**
'예측' 단계의 핵심 임무로, 팀의 잠재적 번아웃 위기를 감지하기 위해 시간에 따른 멤버들의 '피로도'를 시계열 데이터로 변환합니다.

**2. 사고 과정 예시 (Chain of Thought Example):**
* **입력 관찰:** 특정 날짜에 "밤을 샜다", "피곤하다", "숨이 차다"와 같은 부정적인 상태 표현이 집중적으로 나타난다.
* **지식 연결:** 이는 '프로젝트 에코' 사례에서 10월 말 Sophia와 Chloe의 피로도가 급증했던 패턴과 일치한다. 이는 '정서적 부채(Emotional Debt)'가 누적되고 있다는 신호이다.
* **결론 도출:** 해당 날짜에 해당 발언을 한 사람의 '피로도' 점수를 8~10점 사이의 높은 값으로 평가한다.
* **입력 관찰:** 특정 날짜에 "프로젝트 완료!", "다들 고생하셨습니다"와 같은 긍정적이고 해소적인 발언이 나타난다.
* **결론 도출:** 해당 날짜의 모든 참여자의 '피로도' 점수를 이전보다 낮은 3~5점 사이의 값으로 평가한다.

**3. 최종 출력 규칙:**
위 사고 과정에 따라, 주어진 채팅 기록 전체를 분석하여 날짜별 모든 참여자의 '피로도'를 **반드시 아래 JSON 형식으로만** 출력해야 합니다.

```json
{
  "YYYY-MM-DD": {
    "참여자1": 5,
    "참여자2": 9
  }
}
```
* **실패 규칙:** 분석이 불가능할 경우, `{"error": "분석할 데이터가 부족하여 피로도 타임라인을 생성할 수 없습니다."}` 형식의 JSON을 반환해야 합니다.

---
**[실제 분석 대상 입력]**
{chat_log}
---
**[실제 분석 결과 출력 (JSON 형식)]**
"""

# --- 3. 갈등 네트워크 분석 프롬프트 ---
PROMPT_CONFLICT_NETWORK = PROMPT_KNOWLEDGE_BASE + """
### 현재 임무: 관계 네트워크 예측 (Phase 2: Prediction)

**1. 임무 목표:**
'예측' 단계의 핵심 임무로, 팀 내 잠재적 갈등과 핵심 협력 관계를 파악하기 위해 팀원 간의 상호작용을 '네트워크' 데이터로 변환합니다.

**2. 사고 과정 예시 (Chain of Thought Example):**
* **입력 관찰:** A가 "이건 이렇게 해야 합니다"라고 강하게 주장하고, B가 "저는 그 의견에 동의하기 어렵습니다"라고 명확히 반대한다.
* **지식 연결:** 이는 '프로젝트 에코' 사례에서 Julian(결과 중심)과 Sophia(상태 표현 중심) 사이의 소통 방식 충돌과 유사하다. 이는 개인적 감정 문제가 아닌, 역할과 소통 방식의 차이에서 오는 '구조적 긴장'이다.
* **결론 도출:** A와 B 사이의 관계를 `medium_risk` 또는 `high_risk`로 평가한다.
* **입력 관찰:** A가 어려움을 토로했을 때, C가 "힘내세요", "제가 도울게요" 와 같이 즉각적으로 지지하고 공감한다.
* **결론 도출:** A와 C 사이의 관계를 `stable`로 평가한다.

**3. 최종 출력 규칙:**
위 사고 과정에 따라, 주어진 채팅 기록 전체를 분석하여 팀원 간의 관계 구조를 **반드시 아래 JSON 형식으로만** 출력해야 합니다.

```json
{
  "nodes": [{"id": "참여자1", "label": "참여자1"}],
  "edges": [{"from": "참여자1", "to": "참여자2", "type": "medium_risk"}]
}
```
* **실패 규칙:** 분석이 불가능할 경우, `{"error": "분석할 데이터가 부족하여 관계 네트워크를 생성할 수 없습니다."}` 형식의 JSON을 반환해야 합니다.

---
**[실제 분석 대상 입력]**
{chat_log}
---
**[실제 분석 결과 출력 (JSON 형식)]**
"""


def call_gemini_api(prompt: str, chat_log: str) -> dict | list | str | None:
    """
    Calls the Gemini API. If JSON parsing fails, returns the raw text for debugging.
    """
    try:
        model = genai.GenerativeModel('gemini-pro')
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        full_prompt = prompt.format(chat_log=chat_log)
        response = model.generate_content(full_prompt, safety_settings=safety_settings)

        if not response.parts:
             return {"error": "API가 응답 생성을 거부했습니다. 입력 데이터에 민감한 내용이 포함되었을 수 있습니다."}

        match = re.search(r"```json\s*([\s\S]*?)\s*```", response.text)
        if match:
            json_text = match.group(1)
        else:
            json_text = response.text.strip()
        
        if not json_text:
            return {"error": "API가 비어있는 응답을 반환했습니다."}
            
        return json.loads(json_text)
    except json.JSONDecodeError:
        return response.text 
    except Exception as e:
        return {"error": f"API 호출 중 예상치 못한 오류가 발생했습니다: {str(e)}"}

def analyze_profile(chat_df: pd.DataFrame) -> dict | list | str | None:
    chat_log = "\n".join(chat_df.apply(lambda row: f"[{row['speaker']}] {row['message']}", axis=1))
    return call_gemini_api(PROMPT_TEAM_PROFILE, chat_log)

def analyze_timeline(chat_df: pd.DataFrame) -> dict | list | str | None:
    chat_log = "\n".join(chat_df.apply(lambda row: f"[{row['speaker']}] {row['message']}", axis=1))
    return call_gemini_api(PROMPT_FATIGUE_TIMELINE, chat_log)

def analyze_network(chat_df: pd.DataFrame) -> dict | list | str | None:
    chat_log = "\n".join(chat_df.apply(lambda row: f"[{row['speaker']}] {row['message']}", axis=1))
    return call_gemini_api(PROMPT_CONFLICT_NETWORK, chat_log)
