# analyzer.py
# 역할: 파싱된 데이터를 받아 LLM API와 통신하고, 분석 결과를 생성합니다.
# 버전 4: '퓨샷 프롬프팅'을 적용하여 AI 응답의 안정성을 대폭 강화합니다.

import google.generativeai as genai
import json
import pandas as pd

# --- [Delta] Few-shot Prompting Applied ---

# --- 1. 팀 프로필 분석 프롬프트 ---
PROMPT_TEAM_PROFILE = """
당신은 조직 심리 분석가입니다. 주어진 채팅 기록을 분석하여, 각 팀원의 특성을 분석하고 결과를 JSON 형식으로 반환해야 합니다.
아래의 '샘플 입력'과 '샘플 출력'을 참고하여, 어떤 경우에도 '샘플 출력'과 동일한 JSON 구조를 유지해야 합니다.

**[분석 규칙]**
1.  **참여자 식별:** 채팅 기록에 등장하는 모든 주요 참여자를 식별합니다.
2.  **5대 계수 분석:** 각 참여자에 대해 다음 5가지 계수를 1-10점 척도로 평가합니다.
    * **감정(Emotion):** 감정 표현의 빈도와 강도.
    * **사고(Cognition):** 논리적, 분석적, 전략적 발언의 빈도.
    * **표현(Expression):** 의견, 상태, 아이디어 표현의 적극성.
    * **가치(Value):** 팀의 목표, 비전, 핵심 가치에 대한 언급.
    * **편향(Bias):** 특정 주제나 방식에 대한 선호/회피 경향.
3.  **핵심 역할 부여:** 각 참여자의 계수를 종합하여 'The Driver', 'The Coordinator' 등 가장 적합한 핵심 역할을 부여합니다.

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
  {
    "name": "라이언",
    "emotion_score": 3,
    "cognition_score": 8,
    "expression_score": 9,
    "value_score": 7,
    "bias_score": 6,
    "core_role": "The Driver (주도자)"
  },
  {
    "name": "어피치",
    "emotion_score": 8,
    "cognition_score": 4,
    "expression_score": 7,
    "value_score": 3,
    "bias_score": 5,
    "core_role": "The Empath (공감자)"
  },
  {
    "name": "무지",
    "emotion_score": 5,
    "cognition_score": 7,
    "expression_score": 6,
    "value_score": 6,
    "bias_score": 4,
    "core_role": "The Supporter (조력자)"
  }
]
```
---

**[실제 분석 대상 입력]**
{chat_log}
---
**[실제 분석 결과 출력]**
"""

# --- 2. 피로도 타임라인 분석 프롬프트 ---
PROMPT_FATIGUE_TIMELINE = """
당신은 조직 행동 분석가입니다. 주어진 채팅 기록을 분석하여, 시간 경과에 따른 각 팀원의 '피로도(Fatigue)' 변화를 추정하고, 그 결과를 날짜별 JSON 데이터로 반환해야 합니다.
아래의 '샘플 입력'과 '샘플 출력'을 참고하여, 어떤 경우에도 '샘플 출력'과 동일한 JSON 구조를 유지해야 합니다.

**[분석 규칙]**
1.  **피로도 정의:** 피로도는 업무 부담, 스트레스, 부정적 감정 표현, 반응 속도 저하 등을 종합하여 1-10점으로 평가합니다. (1: 매우 낮음, 10: 매우 높음/소진 임박)
2.  **날짜별 분석:** 채팅 기록에 나타난 날짜별로 각 참여자의 피로도를 추정합니다. 특정 날짜에 발언이 없으면 이전 상태를 유지하거나 주변 상황에 따라 추정합니다.

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
  "2025-07-20": {
    "라이언": 5,
    "어피치": 9
  },
  "2025-07-21": {
    "라이언": 3,
    "어피치": 4
  }
}
```
---

**[실제 분석 대상 입력]**
{chat_log}
---
**[실제 분석 결과 출력]**
"""

# --- 3. 갈등 네트워크 분석 프롬프트 ---
PROMPT_CONFLICT_NETWORK = """
당신은 관계 동역학 분석가입니다. 주어진 채팅 기록을 분석하여, 팀원 간의 상호작용을 '갈등 네트워크'로 모델링하고, 그 구조를 노드(node)와 엣지(edge) 형태의 JSON으로 반환해야 합니다.
아래의 '샘플 입력'과 '샘플 출력'을 참고하여, 어떤 경우에도 '샘플 출력'과 동일한 JSON 구조를 유지해야 합니다.

**[분석 규칙]**
1.  **노드(Nodes):** 채팅에 참여한 모든 팀원을 노드로 정의합니다.
2.  **엣지(Edges):** 두 팀원 간의 주요 상호작용을 엣지로 정의합니다.
3.  **관계 유형(Relationship Type):** 각 엣지에 대해 관계를 다음 4가지 유형 중 하나로 분류합니다.
    * `high_risk`: 의견 충돌, 비난, 무시 등 명백한 갈등.
    * `medium_risk`: 잦은 의견 불일치, 긴장감 있는 대화.
    * `potential_risk`: 잠재적 오해나 의견 차이가 있는 관계.
    * `stable`: 지지, 동의, 협력 등 안정적인 관계.

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

def call_gemini_api(prompt: str, chat_log: str) -> dict | list | None:
    """
    Calls the Gemini API and returns the parsed JSON response.
    Handles potential errors during the API call or JSON parsing.
    """
    try:
        model = genai.GenerativeModel('gemini-pro')
        # The prompt already contains the full structure, so we just format the chat log.
        full_prompt = prompt.format(chat_log=chat_log)
        response = model.generate_content(full_prompt)
        # A more robust way to extract JSON, even with surrounding text.
        match = re.search(r"```json\s*([\s\S]*?)\s*```", response.text)
        if match:
            json_text = match.group(1)
        else:
            # If no markdown block, assume the whole text is JSON.
            json_text = response.text

        return json.loads(json_text)
    except Exception:
        # Errors will be caught and handled in the main app file to show them in the UI.
        return None

def run_full_analysis(chat_df: pd.DataFrame) -> dict:
    """
    Runs the full analysis suite on the parsed chat data.
    """
    # Convert dataframe to a simple text log for the API
    chat_log_for_api = "\n".join(chat_df.apply(lambda row: f"{row['date']}\n[{row['speaker']}] {row['message']}", axis=1))

    results = {}
    results['profile'] = call_gemini_api(PROMPT_TEAM_PROFILE, chat_log_for_api)
    results['timeline'] = call_gemini_api(PROMPT_FATIGUE_TIMELINE, chat_log_for_api)
    results['network'] = call_gemini_api(PROMPT_CONFLICT_NETWORK, chat_log_for_api)
    
    return results
