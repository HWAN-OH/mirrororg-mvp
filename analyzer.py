# analyzer.py is now mostly embedded into app.py, but if you'd like to separate responsibilities, here’s an analyzer module that handles GPT interactions.

import openai
import json
import re

openai.api_key = "your-api-key"  # Replace with secure loading if needed

# GPT 프롬프트 선언
ORG_DIAG_PROMPT = """
You are DR. Aiden Rhee, a senior analyst at MirrorOrg.
Analyze the following multi-person chat log and extract key indicators for organizational diagnosis. 
Use the MirrorMind framework, focusing on:
1. Individual identity factors (emotion, cognition, expression, value, bias)
2. Conflict structure between participants
3. Systemic risk assessment (in table form)
4. Suggestions for resilience recovery: 4.1 Role realignment / 4.2 Protocol improvement
5. Conclusion
Return as JSON with keys: identities, conflicts, systemic_risk, suggestions, conclusion
Chat log:
"""

ROLE_ANALYSIS_PROMPT = """
You are DR. Aiden Rhee, a dialogue analyst.
Analyze the following group chat log and classify each participant into roles such as:
- Initiator
- Mediator
- Supporter
- Observer
- Challenger
Explain the reason for each classification.
Return as JSON in the format:
{
  "role_analysis": [
    {"name": "홍길동", "role": "Initiator", "reason": "Suggests direction repeatedly and dominates decisions."}
  ]
}
Chat log:
"""

def call_gpt(prompt: str) -> dict:
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )
    return json.loads(response.choices[0].message['content'])

def analyze_chat(chat_text: str) -> dict:
    try:
        return call_gpt(ORG_DIAG_PROMPT + chat_text)
    except Exception:
        try:
            return call_gpt(ROLE_ANALYSIS_PROMPT + chat_text)
        except Exception as e:
            return {"error": str(e)}

