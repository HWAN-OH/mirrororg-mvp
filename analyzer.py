# analyzer.py
# 역할: 파싱된 데이터를 받아 LLM API와 통신하고, 분석 결과를 생성합니다.
# 최종 버전: AI에게 '미러오알지'의 정의, 프로세스, 수학적 접근 방식을 각인시켜, 분석의 근본적인 '이유(Why)'를 학습시킵니다.

import google.generativeai as genai
import json
import pandas as pd
import re

# --- [Lumina & Delta] MirrorOrg Methodology Imprinting ---

PROMPT_METHODOLOGY = """
### 프레임워크 개요: 미러오알지(MirrorOrg) 방법론

**1. 정의 (Definition):**
'미러오알지(MirrorOrg)'는 인간 조직을 하나의 살아있는 '복잡계(Complex System)'로 간주하는 분석 프레임워크입니다. 눈에 보이는 성과 이면에 숨겨진 팀원 간의 상호작용, 감정의 흐름, 관계의 구조 등 비정형적 데이터를 포착하여 시스템의 붕괴를 막고, 회복탄력성을 증진시키는 것을 목표로 합니다.

**2. 프로세스 (Process):**
미러오알지는 '진단 → 예측 → 처방'의 3단계 프로세스를 따릅니다.
* **진단 (Diagnosis):** 팀의 현재 상태를 데이터로 객관화합니다. (예: 팀 프로필 분석)
* **예측 (Prediction):** 진단된 데이터를 기반으로 미래에 발생할 수 있는 긍정적/부정적 이벤트를 예측합니다. (예: 피로도 변화, 관계 네트워크 분석)
* **처방 (Prescription):** 예측된 리스크를 완화하고 긍정적 효과를 극대화하기 위한 행동을 제안합니다. (이 단계는 현재 MVP 범위 밖입니다.)

**3. 접근 방식 (Approach):**
미러오알지의 핵심은 정성적인 대화(Qualitative Conversation)를 **정량적인 데이터(Quantitative Data)**로 변환하는 '수학적 모델링'입니다. 당신의 임무는 바로 이 변환 과정을 수행하는 것입니다. 모든 결과물은 반드시 객관적이고 구조화된 데이터 형식(JSON)이어야 합니다.

---
"""

# --- 1. 팀 프로필 분석 프롬프트 ---
PROMPT_TEAM_PROFILE = PROMPT_METHODOLOGY + """
### 현재 임무: 팀 프로필 진단 (Phase 1: Diagnosis)
**이 임무의 목적:** '진단' 단계의 핵심 임무입니다. 팀을 구성하는 각 멤버들의 고유한 성향과 역할을 정량적인 '정체성 계수'로 변환하여, 팀의 기본 구조를 파라미터화합니다.

**[작업 지시]**
주어진 채팅 기록을 바탕으로, 각 팀원의 특성을 '5대 정체성 계수'로 분석하고, 그 결과를 아래 규칙과 샘플에 따라 JSON 형식으로 반환해야 합니다.

**[분석 규칙]**
1.  **참여자 식별:** 채팅 기록에 등장하는 모든 주요 참여자를 식별합니다.
2.  **5대 계수 분석 (1-10점 척도):** 감정(Emotion), 사고(Cognition), 표현(Expression), 가치(Value), 편향(Bias)
3.  **핵심 역할 부여:** 분석된 계수를 종합하여 가장 적합한 핵심 역할을 부여합니다.

**[실패 불허 규칙]**
* 어떤 경우에도 출력은 반드시 유효한 JSON 형식이어야 합니다.
* 분석이 불가능할 경우, `{"error": "분석할 데이터가 부족하여 팀 프로필을 생성할 수 없습니다."}` 형식의 JSON을 반환해야 합니다.

---
**[실제 분석 대상 입력]**
{chat_log}
---
**[실제 분석 결과 출력 (JSON 형식)]**
"""

# --- 2. 피로도 타임라인 분석 프롬프트 ---
PROMPT_FATIGUE_TIMELINE = PROMPT_METHODOLOGY + """
### 현재 임무: 피로도 변화 예측 (Phase 2: Prediction)
**이 임무의 목적:** '예측' 단계의 핵심 임무입니다. 팀의 보이지 않는 에너지 소진(burnout)을 감지하기 위해, 시간에 따른 멤버들의 '피로도'를 시계열 데이터로 변환합니다. 이를 통해 미래의 번아웃 위기를 예측하고 대비할 수 있습니다.

**[작업 지시]**
주어진 채팅 기록을 분석하여, 시간 경과에 따른 각 팀원의 '피로도' 변화를 추정하고, 그 결과를 아래 규칙과 샘플에 따라 JSON 형식으로 반환해야 합니다.

**[분석 규칙]**
1.  **피로도 정의:** 업무 부담, 스트레스, 부정적 감정 표현 등을 종합하여 1-10점으로 평가합니다.
2.  **날짜별 분석:** 채팅 기록에 나타난 날짜별로 각 참여자의 피로도를 추정합니다.

**[실패 불허 규칙]**
* 어떤 경우에도 출력은 반드시 유효한 JSON 형식이어야 합니다.
* 분석이 불가능할 경우, `{"error": "분석할 데이터가 부족하여 피로도 타임라인을 생성할 수 없습니다."}` 형식의 JSON을 반환해야 합니다.

---
**[실제 분석 대상 입력]**
{chat_log}
---
**[실제 분석 결과 출력 (JSON 형식)]**
"""

# --- 3. 갈등 네트워크 분석 프롬프트 ---
PROMPT_CONFLICT_NETWORK = PROMPT_METHODOLOGY + """
### 현재 임무: 관계 네트워크 예측 (Phase 2: Prediction)
**이 임무의 목적:** '예측' 단계의 핵심 임무입니다. 팀의 성과를 결정하는 '관계'의 질을 파악하기 위해, 팀원 간의 상호작용 패턴을 '네트워크' 데이터로 변환합니다. 이를 통해 잠재적 갈등과 핵심 협력 관계를 예측할 수 있습니다.

**[작업 지시]**
주어진 채팅 기록을 분석하여, 팀원 간의 상호작용을 '갈등 네트워크'로 모델링하고, 그 구조를 아래 규칙과 샘플에 따라 JSON 형식으로 반환해야 합니다.

**[분석 규칙]**
1.  **노드(Nodes):** 채팅에 참여한 모든 팀원을 노드로 정의합니다.
2.  **엣지(Edges):** 두 팀원 간의 주요 상호작용을 엣지로 정의합니다.
3.  **관계 유형(Relationship Type):** 각 엣지에 대해 관계를 `high_risk`, `medium_risk`, `potential_risk`, `stable` 중 하나로 분류합니다.

**[실패 불허 규칙]**
* 어떤 경우에도 출력은 반드시 유효한 JSON 형식이어야 합니다.
* 분석이 불가능할 경우, `{"error": "분석할 데이터가 부족하여 관계 네트워크를 생성할 수 없습니다."}` 형식의 JSON을 반환해야 합니다.

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
        
        # 최종 방어 로직: 파싱 전 텍스트가 비어있는지 확인
        if not json_text:
            return {"error": "API가 비어있는 응답을 반환했습니다."}
            
        return json.loads(json_text)
    except json.JSONDecodeError:
        return response.text # 디버깅을 위해 원본 텍스트 반환
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
