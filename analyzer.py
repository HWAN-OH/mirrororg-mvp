# analyzer.py
# 역할: 파싱된 데이터를 받아 LLM API와 통신하고, 분석 결과를 생성합니다.
# 최종 버전: '요약 -> 분석' 2단계 프로세스를 도입하여 LLM의 과부하를 근본적으로 해결합니다.

import google.generativeai as genai
import json
import pandas as pd
import re

# --- [Delta] Stage 1: Summarization Prompt ---
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
{chat_log}
---
**[핵심 내용 요약 보고서]**
"""

# --- [Delta] Stage 2: Analysis Prompts (Now using the summary) ---
PROMPT_KNOWLEDGE_BASE = """
### 프레임워크 핵심 지식: 미러오알지(MirrorOrg) 방법론
'미러오알지'는 인간 조직을 '복잡계'로 보고, 정성적인 대화를 정량적인 데이터로 변환하여 시스템의 붕괴를 막는 것을 목표로 합니다. 당신의 임무는 이 방법론에 따라 주어진 '요약된' 대화 내용을 분석하는 것입니다.
---
"""

PROMPT_TEAM_PROFILE = PROMPT_KNOWLEDGE_BASE + """
### 현재 임무: 팀 프로필 진단
**목표:** 주어진 '요약 보고서'와 '원본 대화 일부'를 바탕으로, 팀원들의 '5대 정체성 계수'를 분석하여 JSON으로 출력합니다.
**사고 과정:** 요약 보고서에 나타난 각 개인의 행동 패턴(예: 'Julian은 주로 전략적 지시를 내림')을 '프로젝트 에코' 사례와 연결하여 계수를 판단합니다.
**출력 형식:** `[{"name": "이름", "emotion_score": 5, ...}]`

**[분석 대상 요약 보고서 및 원본 대화]**
{summary}
---
**[분석 결과 (JSON 형식)]**
"""

PROMPT_FATIGUE_TIMELINE = PROMPT_KNOWLEDGE_BASE + """
### 현재 임무: 피로도 변화 예측
**목표:** 주어진 '요약 보고서'와 '원본 대화 일부'를 바탕으로, 시간 경과에 따른 '피로도'를 시계열 JSON으로 출력합니다.
**사고 과정:** 요약 보고서에 '밤샘', '피로' 등의 키워드가 나타난 시점을 중심으로 피로도를 높게 평가합니다.
**출력 형식:** `{"YYYY-MM-DD": {"이름": 9, ...}}`

**[분석 대상 요약 보고서 및 원본 대화]**
{summary}
---
**[분석 결과 (JSON 형식)]**
"""

PROMPT_CONFLICT_NETWORK = PROMPT_KNOWLEDGE_BASE + """
### 현재 임무: 관계 네트워크 예측
**목표:** 주어진 '요약 보고서'와 '원본 대화 일부'를 바탕으로, 팀원 간의 관계를 네트워크 JSON으로 출력합니다.
**사고 과정:** 요약 보고서에 '의견 충돌'로 명시된 부분을 중심으로 관계를 `medium_risk` 이상으로 평가합니다.
**출력 형식:** `{"nodes": [...], "edges": [...]}`

**[분석 대상 요약 보고서 및 원본 대화]**
{summary}
---
**[분석 결과 (JSON 형식)]**
"""

def call_gemini_api(prompt: str, text_input: str, is_json_output: bool = True) -> dict | list | str | None:
    """
    Calls the Gemini API. Handles both JSON and text outputs.
    """
    try:
        model = genai.GenerativeModel('gemini-pro')
        safety_settings = [{"category": f"HARM_CATEGORY_{cat}", "threshold": "BLOCK_NONE"} for cat in ["HARASSMENT", "HATE_SPEECH", "SEXUALLY_EXPLICIT", "DANGEROUS_CONTENT"]]
        
        full_prompt = prompt.format(chat_log=text_input, summary=text_input) # Use a generic key
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
    return call_gemini_api(PROMPT_SUMMARIZE, chat_log, is_json_output=False)

def analyze_profile(summary: str) -> dict | list | str | None:
    return call_gemini_api(PROMPT_TEAM_PROFILE, summary)

def analyze_timeline(summary: str) -> dict | list | str | None:
    return call_gemini_api(PROMPT_FATIGUE_TIMELINE, summary)

def analyze_network(summary: str) -> dict | list | str | None:
    return call_gemini_api(PROMPT_CONFLICT_NETWORK, summary)
