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

FALLBACK_TEMPLATE = '''{
  "role_analysis": [
    {"name": "%s", "role": "Observer", "reason": "Insufficient data, defaulted to passive role."}
  ]
}'''

def call_gpt(prompt: str) -> str:
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )
    return response.choices[0].message['content']

def analyze_chat(chat_text: str) -> dict:
    try:
        org_response = call_gpt(ORG_DIAG_PROMPT + chat_text)
        return json.loads(org_response)
    except Exception:
        try:
            role_response = call_gpt(ROLE_ANALYSIS_PROMPT + chat_text)
            return json.loads(role_response)
        except Exception:
            try:
                # fallback 추정 분석: 가장 많이 등장한 이름 추정
                names = re.findall(r"[가-힣]{2,4}|[A-Za-z_]+", chat_text)
                name_counts = {}
                for name in names:
                    if name not in name_counts:
                        name_counts[name] = 0
                    name_counts[name] += 1
                top_name = sorted(name_counts.items(), key=lambda x: x[1], reverse=True)[0][0]
                return json.loads(FALLBACK_TEMPLATE % top_name)
            except Exception as e:
                return {"error": "Fallback failed: " + str(e)}

