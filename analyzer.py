# analyzer.py
# 역할: 파싱된 데이터를 받아 LLM API와 통신하고, 분석 결과를 생성합니다.

import google.generativeai as genai
import json
import pandas as pd

# Prompts are part of the analysis logic, so they belong here.
PROMPT_TEAM_PROFILE = """
당신은 조직 심리 분석가입니다. 주어진 채팅 기록을 바탕으로, '미러오알지 팀 분석 사례' 문서의 '정체성 계수 맵'과 같이 각 팀원의 특성을 분석하고 결과를 JSON 형식으로 반환하세요.

**분석 규칙:**
1.  **참여자 식별:** 채팅 기록에 등장하는 모든 주요 참여자를 식별합니다.
2.  **5대 계수 분석:** 각 참여자에 대해 다음 5가지 계수를 1-10점 척도로 평가합니다.
    * **감정(Emotion):** 감정 표현의 빈도와 강도.
    * **사고(Cognition):** 논리적, 분석적, 전략적 발언의 빈도.
    * **표현(Expression):** 의견, 상태, 아이디어 표현의 적극성.
    * **가치(Value):** 팀의 목표, 비전, 핵심 가치에 대한 언급.
    * **편향(Bias):** 특정 주제나 방식에 대한 선호/회피 경향.
3.  **핵심 역할 부여:** 각 참여자의 계수를 종합하여 'The Driver', 'The Coordinator' 등 가장 적합한 핵심 역할을 부여합니다.
4.  **JSON 형식 출력:** 아래와 같은 리스트 형태의 JSON으로만 응답하세요. 다른 설명은 추가하지 마세요.
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

**[입력 데이터: 채팅 기록]**
---
{chat_log}
---
"""

PROMPT_FATIGUE_TIMELINE = """
당신은 조직 행동 분석가입니다. 주어진 채팅 기록을 분석하여, 시간 경과에 따른 각 팀원의 '피로도(Fatigue)' 변화를 추정하고, 그 결과를 날짜별 JSON 데이터로 반환하세요.

**분석 규칙:**
1.  **피로도 정의:** 피로도는 업무 부담, 스트레스, 부정적 감정 표현, 반응 속도 저하 등을 종합하여 1-10점으로 평가합니다. (1: 매우 낮음, 10: 매우 높음/소진 임박)
2.  **날짜별 분석:** 채팅 기록에 나타난 날짜별로 각 참여자의 피로도를 추정합니다. 특정 날짜에 발언이 없으면 이전 상태를 유지하거나 주변 상황에 따라 추정합니다.
3.  **JSON 형식 출력:** 아래와 같은 날짜-사용자-점수 구조의 JSON으로만 응답하세요. 다른 설명은 추가하지 마세요.
    ```json
    {
      "YYYY-MM-DD": {
        "참여자1": 3,
        "참여자2": 5
      },
      "YYYY-MM-DD": {
        "참여자1": 4,
        "참여자2": 6
      }
    }
    ```

**[입력 데이터: 채팅 기록]**
---
{chat_log}
---
"""

PROMPT_CONFLICT_NETWORK = """
당신은 관계 동역학 분석가입니다. 주어진 채팅 기록을 분석하여, 팀원 간의 상호작용을 '갈등 네트워크'로 모델링하고, 그 구조를 노드(node)와 엣지(edge) 형태의 JSON으로 반환하세요.

**분석 규칙:**
1.  **노드(Nodes):** 채팅에 참여한 모든 팀원을 노드로 정의합니다.
2.  **엣지(Edges):** 두 팀원 간의 주요 상호작용을 엣지로 정의합니다.
3.  **관계 유형(Relationship Type):** 각 엣지에 대해 관계를 다음 4가지 유형 중 하나로 분류합니다.
    * `high_risk`: 의견 충돌, 비난, 무시 등 명백한 갈등.
    * `medium_risk`: 잦은 의견 불일치, 긴장감 있는 대화.
    * `potential_risk`: 잠재적 오해나 의견 차이가 있는 관계.
    * `stable`: 지지, 동의, 협력 등 안정적인 관계.
4.  **JSON 형식 출력:** 아래와 같은 노드와 엣지 리스트를 포함한 JSON 객체로만 응답하세요.
    ```json
    {
      "nodes": [
        {"id": "참여자1", "label": "참여자1"},
        {"id": "참여자2", "label": "참여자2"}
      ],
      "edges": [
        {"from": "참여자1", "to": "참여자2", "type": "high_risk"},
        {"from": "참여자1", "to": "참여자3", "type": "stable"}
      ]
    }
    ```

**[입력 데이터: 채팅 기록]**
---
{chat_log}
---
"""

def call_gemini_api(prompt: str, chat_log: str) -> dict | list | None:
    """
    Calls the Gemini API and returns the parsed JSON response.
    Handles potential errors during the API call or JSON parsing.
    """
    try:
        model = genai.GenerativeModel('gemini-pro')
        full_prompt = prompt.format(chat_log=chat_log)
        response = model.generate_content(full_prompt)
        cleaned_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(cleaned_text)
    except Exception:
        # Errors will be caught and handled in the main app file to show them in the UI.
        return None

def run_full_analysis(chat_df: pd.DataFrame) -> dict:
    """
    Runs the full analysis suite on the parsed chat data.
    """
    # Convert dataframe to a simple text log for the API
    chat_log_for_api = "\n".join(chat_df.apply(lambda row: f"[{row['speaker']}] {row['message']}", axis=1))

    results = {}
    results['profile'] = call_gemini_api(PROMPT_TEAM_PROFILE, chat_log_for_api)
    results['timeline'] = call_gemini_api(PROMPT_FATIGUE_TIMELINE, chat_log_for_api)
    results['network'] = call_gemini_api(PROMPT_CONFLICT_NETWORK, chat_log_for_api)
    
    return results
