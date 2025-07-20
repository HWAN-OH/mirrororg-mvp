# analyzer.py
# 역할: 파싱된 데이터를 받아 LLM API와 통신하고, 분석 결과를 생성합니다.
# 최종 버전: API 호출 모델을 최신 버전인 'gemini-1.5-flash'로 변경하여 근본적인 통신 오류를 해결합니다.

import google.generativeai as genai
import json
import pandas as pd
import re

# --- 프롬프트는 이전 버전과 동일하게 유지합니다. (생략) ---
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


def call_gemini_api(prompt: str, text_input: str, is_json_output: bool = True) -> dict | list | str | None:
    """
    Calls the Gemini API using the latest model. Handles both JSON and text outputs.
    """
    try:
        # --- [Delta] FINAL FIX: Changed model name to the latest version ---
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        safety_settings = [{"category": f"HARM_CATEGORY_{cat}", "threshold": "BLOCK_NONE"} for cat in ["HARASSMENT", "HATE_SPEECH", "SEXUALLY_EXPLICIT", "DANGEROUS_CONTENT"]]
        
        # Use a generic key 'text_input' for both summary and chat_log
        full_prompt = prompt.format(text_input=text_input)
        response = model.generate_content(full_prompt, safety_settings=safety_settings)

        if not response.parts:
            return {"error": "API response was blocked."} if is_json_output else "API response was blocked."

        raw_text = response.text
        if not is_json_output:
            return raw_text # For summarization

        match = re.search(r"```json\s*([\s\S]*?)\s*```", raw_text)
        json_text = match.group(1) if match else raw_text.strip()
        
        if not json_text:
            return {"error": "API returned an empty response."}
            
        return json.loads(json_text)
    except json.JSONDecodeError:
        return raw_text # Return raw text for debugging
    except Exception as e:
        return {"error": f"An unexpected API error occurred: {str(e)}"}

def summarize_chat(chat_df: pd.DataFrame) -> str | None:
    chat_log = "\n".join(chat_df.apply(lambda row: f"[{row['speaker']}] {row['message']}", axis=1))
    # Pass the generic key 'text_input' to the prompt
    prompt = PROMPT_SUMMARIZE.replace("{chat_log}", "{text_input}")
    return call_gemini_api(prompt, chat_log, is_json_output=False)

def analyze_profile(summary: str) -> dict | list | str | None:
    prompt = PROMPT_TEAM_PROFILE.replace("{chat_log}", "{text_input}")
    return call_gemini_api(prompt, summary)

def analyze_timeline(summary: str) -> dict | list | str | None:
    prompt = PROMPT_FATIGUE_TIMELINE.replace("{chat_log}", "{text_input}")
    return call_gemini_api(prompt, summary)

def analyze_network(summary: str) -> dict | list | str | None:
    prompt = PROMPT_CONFLICT_NETWORK.replace("{chat_log}", "{text_input}")
    return call_gemini_api(prompt, summary)

# Redefine the summarization prompt with the generic key
PROMPT_SUMMARIZE = """
### 미션: 대화록 핵심 내용 추출 (Mission: Core Log Extraction)
당신은 최고의 회의록 서기입니다. 당신의 유일한 임무는 주어진 길고 복잡한 대화록에서, 이후 심층 분석에 필요한 핵심 정보만 간결하게 추출하여 요약하는 것입니다.

**[추출 규칙]**
1.  **핵심 사건:** 프로젝트의 시작, 주요 마일스톤, 위기 상황 등 중요한 사건들을 시간 순서대로 요약합니다.
2.  **감정 변화:** 팀의 전반적인 분위기가 긍정적이었던 시점, 부정적인 감정(피로, 스트레스, 불만)이 많이 표출된 시점을 명확히 짚어냅니다.
3.  **주요 갈등:** 팀원 간에 의견이 충돌했거나, 명백한 갈등이 있었던 대화 내용을 구체적으로 명시합니다.
4.  **참여자 목록:** 대화에 참여한 모든 사람의 이름을 나열합니다.

**[출력 형식]**
자유로운 텍스트 형식으로, 위 규칙에 따라 최대한 간결하게 요약된 보고서를 작성합니다.

---
**[분석 대상 대화록]**
{text_input}
---
**[핵심 내용 요약 보고서]**
"""
