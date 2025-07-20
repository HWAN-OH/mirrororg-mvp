# analyzer.py
# 역할: 원본 채팅 기록을 직접 분석하여, 각 시각화에 필요한 데이터를 개별적으로 생성합니다.
# 최종 버전: 사용자가 제안한 'Strong Prompt'와 새로운 JSON 템플릿을 적용하여 안정성을 극대화합니다.

import google.generativeai as genai
import json
import pandas as pd
import re

# --- [Lumina & Delta] Final User-Defined Strong Prompts ---

PROMPT_HEADER = """
### TASK
Your single task is to analyze the entire provided chat log and extract specific data.
You MUST respond with ONLY a valid JSON that strictly follows the template provided in the "OUTPUT FORMAT" section.
Do not include any other text, explanations, or markdown formatting. Analyze ALL participants and relationships found in the chat log; the example is only for demonstrating the format.

### CHAT LOG TO ANALYZE
{chat_log}
---
### JSON OUTPUT
"""

PROMPT_TEAM_PROFILE = PROMPT_HEADER + """
### TASK-SPECIFIC INSTRUCTIONS
- Analyze each participant's characteristics based on their messages.
- Score the 5 coefficients (emotion, cognition, expression, value, bias) on a scale of 1-10.
- Assign a concise Core Role.

### OUTPUT FORMAT
```json
[
  {
    "name": "Participant Name",
    "emotion_score": 5,
    "cognition_score": 9,
    "expression_score": 6,
    "value_score": 9,
    "bias_score": 7,
    "core_role": "The Driver"
  }
]
```
"""

PROMPT_FATIGUE_TIMELINE = PROMPT_HEADER + """
### TASK-SPECIFIC INSTRUCTIONS
- This task is to extract the fatigue score for each team member by date.
- **Fatigue Score:** Estimate on a scale of 1-5 based on tone, frequency of emotional expressions, complaints, etc.
- **Date Grouping:** Group the scores by the dates that appear in the chat log.

### OUTPUT FORMAT
```json
[
  {
    "name": "Participant A",
    "fatigue_timeline": [
      {"date": "YYYY-MM-DD", "score": 2},
      {"date": "YYYY-MM-DD", "score": 3}
    ]
  },
  {
    "name": "Participant B",
    "fatigue_timeline": [
      {"date": "YYYY-MM-DD", "score": 4},
      {"date": "YYYY-MM-DD", "score": 5}
    ]
  }
]
```
"""

PROMPT_CONFLICT_NETWORK = PROMPT_HEADER + """
### TASK-SPECIFIC INSTRUCTIONS
- This task is to extract the relationship network between team members.
- **Relationship Type:** Classify the relationship between two people as either "conflict" or "support".
- **Strength:** Estimate the strength of that relationship on a scale of 0.1 to 1.0.

### OUTPUT FORMAT
```json
[
  {"source": "Participant A", "target": "Participant B", "strength": 0.8, "type": "conflict"},
  {"source": "Participant B", "target": "Participant C", "strength": 0.4, "type": "support"}
]
```
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
