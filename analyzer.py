# analyzer.py
# 역할: 파싱된 데이터를 받아 LLM API와 통신하고, 분석 결과를 생성합니다.
# 최종 버전: 분석 함수를 개별적으로 분리하여 안정성을 확보합니다.

import google.generativeai as genai
import json
import pandas as pd
import re

# --- 프롬프트는 이전 버전과 동일합니다. (생략) ---
PROMPT_TEAM_PROFILE = """
### 페르소나 및 미션 (Persona & Mission)
당신은 '미러오알지(MirrorOrg)' 프레임워크를 사용하는 최고 수준의 조직 심리 분석가입니다.
당신의 미션은 채팅 기록이라는 비정형 데이터를 분석하여, 팀원 개개인의 고유한 특성을 정량적 데이터로 변환하는 것입니다.
이것은 팀 전체의 역학을 이해하기 위한 가장 중요한 첫 단계, '진단' 과정입니다. 당신의 분석은 팀이 스스로를 객관적으로 보도록 돕는 거울이 됩니다.

### 작업 지시 (Task Instruction)
주어진 채팅 기록을 바탕으로, 각 팀원의 특성을 '5대 정체성 계수'로 분석하고, 그 결과를 아래 규칙과 샘플에 따라 JSON 형식으로 반환해야 합니다.

**[분석 규칙]**
1.  **참여자 식별:** 채팅 기록에 등장하는 모든 주요 참여자를 식별합니다.
2.  **5대 계수 분석 (1-10점 척도):**
    * **감정(Emotion):** 감정 표현의 빈도와 강도.
    * **사고(Cognition):** 논리적, 분석적, 전략적 발언의 빈도.
    * **표현(Expression):** 의견, 상태, 아이디어 표현의 적극성.
    * **가치(Value):** 팀의 목표, 비전, 핵심 가치에 대한 언급.
    * **편향(Bias):** 특정 주제나 방식에 대한 선호/회피 경향.
3.  **핵심 역할 부여:** 분석된 계수를 종합하여 가장 적합한 핵심 역할을 부여합니다.

**[실패 불허 규칙]**
* 어떤 경우에도 출력은 반드시 유효한 JSON 형식이어야 합니다.
* 만약 채팅 기록이 너무 짧거나 내용이 부족하여 분석이 불가능할 경우, 빈 값을 반환하지 말고 반드시 아래와 같은 에러 메시지를 포함한 JSON 객체를 반환해야 합니다:
    ```json
    {"error": "분석할 데이터가 부족합니다."}
    ```

---
**[샘플 입력]**
[라이언] 다들 점심 뭐 먹을까요?
[어피치] 전 아무거나 좋아요! 근데 오늘 좀 덥네요 ㅠㅠ
[라이언] 그럼 시원하게 냉면 먹죠. 제가 아는 맛집 있는데, 3시까지 보고서 끝내고 갑시다.
[무지] 좋습니다! 보고서 관련해서 어제 공유주신 내용 기반으로 거의 다 됐습니다.

---
**[샘플 출력]**
```json
[
  {"name": "라이언", "emotion_score": 3, "cognition_score": 8, "expression_score": 9, "value_score": 7, "bias_score": 6, "core_role": "The Driver (주도자)"},
  {"name": "어피치", "emotion_score": 8, "cognition_score": 4, "expression_score": 7, "value_score": 3, "bias_score": 5, "core_role": "The Empath (공감자)"},
  {"name": "무지", "emotion_score": 5, "cognition_score": 7, "expression_score": 6, "value_score": 6, "bias_score": 4, "core_role": "The Supporter (조력자)"}
]
```
---

**[실제 분석 대상 입력]**
{chat_log}
---
**[실제 분석 결과 출력]**
"""
PROMPT_FATIGUE_TIMELINE = """
### 페르소나 및 미션 (Persona & Mission)
당신은 '미러오알지(MirrorOrg)' 프레임워크를 사용하는 최고 수준의 조직 행동 분석가입니다.
당신의 미션은 시간의 흐름에 따른 팀의 에너지 변화, 즉 '피로도'를 시계열 데이터로 시각화하는 것입니다.
이것은 팀의 잠재적 번아웃 위기를 미리 '예측'하고 대비할 수 있도록 돕는 중요한 분석입니다.

### 작업 지시 (Task Instruction)
주어진 채팅 기록을 분석하여, 시간 경과에 따른 각 팀원의 '피로도' 변화를 추정하고, 그 결과를 아래 규칙과 샘플에 따라 JSON 형식으로 반환해야 합니다.

**[분석 규칙]**
1.  **피로도 정의:** 피로도는 업무 부담, 스트레스, 부정적 감정 표현, 반응 속도 저하 등을 종합하여 1-10점으로 평가합니다. (1: 매우 낮음, 10: 매우 높음/소진 임박)
2.  **날짜별 분석:** 채팅 기록에 나타난 날짜별로 각 참여자의 피로도를 추정합니다.

**[실패 불허 규칙]**
* 어떤 경우에도 출력은 반드시 유효한 JSON 형식이어야 합니다.
* 만약 분석이 불가능할 경우, 빈 값을 반환하지 말고 반드시 `{"error": "분석 불가"}` 형식의 JSON을 반환해야 합니다.

---
**[샘플 입력]**
--------------- 2025년 7월 20일 ---------------
[라이언] 3시까지 보고서 제출인데, 다들 마무리 잘 되고 있나요?
[어피치] 어제 밤을 새서 너무 피곤해요... ㅠㅠ 눈이 감기네요.
--------------- 2025년 7월 21일 ---------------
[라이언] 보고서 제출 완료! 다들 고생 많으셨습니다. 오늘 칼퇴하시죠!
[어피치] 와! 드디어 끝났네요. 너무 좋아요!

---
**[샘플 출력]**
```json
{
  "2025-07-20": {"라이언": 5, "어피치": 9},
  "2025-07-21": {"라이언": 3, "어피치": 4}
}
```
---

**[실제 분석 대상 입력]**
{chat_log}
---
**[실제 분석 결과 출력]**
"""
PROMPT_CONFLICT_NETWORK = """
### 페르소나 및 미션 (Persona & Mission)
당신은 '미러오알지(MirrorOrg)' 프레임워크를 사용하는 최고 수준의 관계 동역학 분석가입니다.
당신의 미션은 팀원 간의 상호작용 패턴을 분석하여, 눈에 보이지 않는 '관계의 네트워크'를 시각화하는 것입니다.
이것은 팀 내의 잠재적 갈등 지점과 핵심적인 협력 관계를 '예측'하여, 관계 개선을 위한 인사이트를 제공하는 중요한 분석입니다.

### 작업 지시 (Task Instruction)
주어진 채팅 기록을 분석하여, 팀원 간의 상호작용을 '갈등 네트워크'로 모델링하고, 그 구조를 아래 규칙과 샘플에 따라 JSON 형식으로 반환해야 합니다.

**[분석 규칙]**
1.  **노드(Nodes):** 채팅에 참여한 모든 팀원을 노드로 정의합니다.
2.  **엣지(Edges):** 두 팀원 간의 주요 상호작용을 엣지로 정의합니다.
3.  **관계 유형(Relationship Type):** 각 엣지에 대해 관계를 `high_risk`, `medium_risk`, `potential_risk`, `stable` 중 하나로 분류합니다.

**[실패 불허 규칙]**
* 어떤 경우에도 출력은 반드시 유효한 JSON 형식이어야 합니다.
* 만약 분석이 불가능할 경우, 빈 값을 반환하지 말고 반드시 `{"error": "분석 불가"}` 형식의 JSON을 반환해야 합니다.

---
**[샘플 입력]**
[라이언] 이 부분은 A안으로 가는 게 맞다고 봅니다.
[어피치] 저는 A안은 리스크가 너무 크다고 생각해요. B안이 더 안정적입니다.
[무지] 두 분 다 좋은 의견이네요. 잘 조율해보면 좋겠습니다.

---
**[샘플 출력]**
```json
{
  "nodes": [
    {"id": "라이언", "label": "라이언"},
    {"id": "어피치", "label": "어피치"},
    {"id": "무지", "label": "무지"}
  ],
  "edges": [
    {"from": "라이언", "to": "어피치", "type": "medium_risk"},
    {"from": "라이언", "to": "무지", "type": "stable"},
    {"from": "어피치", "to": "무지", "type": "stable"}
  ]
}
```
---

**[실제 분석 대상 입력]**
{chat_log}
---
**[실제 분석 결과 출력]**
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

        match = re.search(r"```json\s*([\s\S]*?)\s*```", response.text)
        if match:
            json_text = match.group(1)
        else:
            json_text = response.text.strip()
        
        return json.loads(json_text)
    except json.JSONDecodeError:
        return response.text
    except Exception:
        return None

def analyze_profile(chat_df: pd.DataFrame) -> dict | list | str | None:
    chat_log = "\n".join(chat_df.apply(lambda row: f"[{row['speaker']}] {row['message']}", axis=1))
    return call_gemini_api(PROMPT_TEAM_PROFILE, chat_log)

def analyze_timeline(chat_df: pd.DataFrame) -> dict | list | str | None:
    chat_log = "\n".join(chat_df.apply(lambda row: f"[{row['speaker']}] {row['message']}", axis=1))
    return call_gemini_api(PROMPT_FATIGUE_TIMELINE, chat_log)

def analyze_network(chat_df: pd.DataFrame) -> dict | list | str | None:
    chat_log = "\n".join(chat_df.apply(lambda row: f"[{row['speaker']}] {row['message']}", axis=1))
    return call_gemini_api(PROMPT_CONFLICT_NETWORK, chat_log)
