# analyzer.py
# 역할: 어떤 형태의 원본 채팅 기록이든 직접 입력받아, 파싱과 분석을 한 번에 수행하여 최종 보고서를 생성합니다.
# 최종 버전: 'parsers.py'를 완전히 대체하는 통합 프롬프트를 사용합니다.

import google.generativeai as genai
import pandas as pd

# --- [Lumina & Delta] The Ultimate Unified Prompt (Parser + Analyzer) ---

PROMPT_UNIFIED_REPORT = """
### 페르소나 및 미션 (Persona & Mission)
당신은 '미러오알지(MirrorOrg)' 프레임워크를 실행하는 최고 수준의 AI 조직 분석가입니다.
당신의 유일한 임무는 **어떤 형식이든 상관없이 주어진 원본 채팅 기록(raw text log)을 직접 해석**하여, 팀의 붕괴를 막고 성장을 돕기 위한 **'종합 분석 보고서'**를 작성하는 것입니다.

### 프레임워크 핵심 지식: 미러오알지(MirrorOrg) 방법론
* **정의:** 조직을 '복잡계'로 보고, 정성적 대화를 정량적 데이터와 통찰력으로 변환하여 시스템의 숨겨진 역학을 진단하고 예측하는 프레임워크.
* **프로세스:** 진단 (팀 프로필 분석) → 예측 (피로도 변화, 관계 네트워크 분석)
* **사고 과정 (Chain of Thought):**
    1.  **파싱 및 정규화:** 먼저, 입력된 원본 텍스트에서 날짜, 발언자, 메시지 내용을 추출하여 내부적으로 시간 순서에 맞게 재구성합니다. (입력 형식은 카카오톡, 슬랙 등 다양할 수 있습니다.)
    2.  **패턴 인식:** 재구성된 대화 내용에서 '프로젝트 에코' 사례와 유사한 패턴(예: 전략적 발언, 감정적 호소, 의견 충돌 등)을 찾습니다.
    3.  **지식 연결:** 인식된 패턴을 '미러오알지'의 개념(정체성 계수, 정서적 부채, 구조적 긴장 등)과 연결하여 해석합니다.
    4.  **보고서 작성:** 해석된 내용을 바탕으로, 아래의 보고서 형식에 맞춰 각 섹션을 채워나갑니다.

---
### 최종 보고서 출력 형식 (Markdown)

# MirrorOrg 종합 분석 보고서

## 1. 분석 개요
* **분석 기간:** [채팅 기록의 시작 날짜] ~ [채팅 기록의 마지막 날짜]
* **분석 대상:** [채팅 기록에 참여한 주요 인물 목록]
* **핵심 요약:** (분석 결과에 대한 2~3 문장의 핵심 요약)

---

## 2. Phase 1: 진단 (Diagnosis)
### 2.1. 정체성 계수 맵 (Identity Coefficient Map)
팀원들의 성향과 역할을 파악하여 팀의 전체적인 구성을 진단합니다.

| 이름 (가명) | 감정 | 사고 | 표현 | 가치 | 편향 | 핵심 역할 |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| (참여자 A) | (점수) | (점수) | (점수) | (점수) | (점수) | (역할) |
| (참여자 B) | (점수) | (점수) | (점수) | (점수) | (점수) | (역할) |

**분석 근거:**
* **[참여자 A 이름]:** (해당 참여자의 계수가 왜 그렇게 판단되었는지, 채팅 내용의 구체적인 예시를 들어 1~2 문장으로 서술)

---

## 3. Phase 2: 예측 (Prediction)
### 3.1. 피로도 변화 (Fatigue Trajectory)
* **주요 관찰 사항:** (예: X월 말, 특정 팀원의 피로도가 급증하는 패턴이 관찰되었습니다. 이는 '정서적 부채' 누적을 시사합니다.)
* **리스크 분석:** (예: 이러한 피로도 증가는 팀의 번아웃 리스크를 높입니다.)

### 3.2. 관계 네트워크 (Relationship Network)
* **주요 관찰 사항:** (예: 리더 A와 팀원 B 사이에 반복적인 의견 충돌이 관찰되었습니다.)
* **리스크 분석:** (예: 이는 개인의 문제가 아닌, '구조적 긴장'이며 중재 메커니즘 부재 시 갈등으로 발전할 수 있습니다.)

---

## 4. 종합 결론 및 제언
(분석 내용을 종합하여, 이 팀의 가장 큰 시스템적 강점과 리스크는 무엇인지 2~3 문장으로 요약하고, 개선을 위한 간단한 제언을 덧붙입니다.)

---
### [분석 대상 원본 채팅 기록]
{chat_log}
---
### [종합 분석 보고서 (Markdown 형식)]
"""

def call_gemini_api(prompt: str, chat_log: str) -> str | None:
    """
    Calls the Gemini API and returns the raw text response.
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        safety_settings = [{"category": f"HARM_CATEGORY_{cat}", "threshold": "BLOCK_NONE"} for cat in ["HARASSMENT", "HATE_SPEECH", "SEXUALLY_EXPLICIT", "DANGEROUS_CONTENT"]]
        
        full_prompt = prompt.format(chat_log=chat_log)
        response = model.generate_content(full_prompt, safety_settings=safety_settings)

        if not response.parts:
            return "## 분석 실패\n\nAPI가 응답 생성을 거부했습니다. 입력 데이터에 민감한 내용이 포함되었을 수 있습니다."

        return response.text
    except Exception as e:
        return f"## 분석 실패\n\nAPI 호출 중 예상치 못한 오류가 발생했습니다:\n\n```\n{str(e)}\n```"

def generate_report(raw_chat_content: str, lang: str = 'ko') -> str | None:
    """
    Generates a single comprehensive report directly from the raw chat content.
    The language parameter is kept for future prompt localization if needed.
    """
    # For now, we use one powerful prompt that understands Korean context.
    # If English reports are needed, a separate PROMPT_EN would be used here.
    prompt = PROMPT_UNIFIED_REPORT
    return call_gemini_api(prompt, raw_chat_content)
