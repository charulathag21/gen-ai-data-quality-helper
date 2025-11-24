# backend/src/services/llm_helper.py

import os
import json
from typing import List, Dict, Any

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate


# Free model from Groq 
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print(" GROQ_API_KEY not found in environment variables!")

LLM_MODEL = "llama-3.1-8b-instant"

llm = ChatGroq(
    temperature=0.2,
    model_name=LLM_MODEL,
)



#  MAIN FUNCTION
def get_llm_corrections(issues: List[Dict[str, Any]]):
    """
    Takes list:
    [
        {
            "id": int,
            "issue_type": "invalid_email" | "invalid_date" | "invalid_phone",
            "column": str,
            "row_index": int,
            "value": str
        }
    ]

    Returns grouped corrections:
    {
        "email": { row_index: {...} },
        "date":  { row_index: {...} },
        "phone": { row_index: {...} }
    }
    """

    if not issues:
        return {"email": {}, "date": {}, "phone": {}}

    limited = issues[:50]
    issues_json = json.dumps(limited, ensure_ascii=False)

    # -------- Prompt Template --------
    prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a strict JSON-only data cleaning assistant. "
        "You always output EXACT JSON (array only). "
        "No backticks, no explanations, no text outside JSON."
    ),
    (
        "user",
        """
    You receive a list of issues:

    {issues_json}

    Each issue contains:
    - id
    - issue_type (invalid_email, invalid_date, invalid_phone)
    - column
    - row_index
    - value

    Return STRICT JSON array in this shape:

    [
    {{
        "id": <id>,
        "suggestion": "<corrected_value>",
        "confidence": "<high|medium|low>",
        "reason": "<short explanation>"
    }}
    ]

    IMPORTANT:
    - Double curly braces here are NOT variables — they are literal braces.
    - Emails: fix typos only.
    - Dates: convert to YYYY-MM-DD.
    - Phone: convert to +international format.

    DO NOT output anything outside JSON.
            """
        )
    ])

    try:
        response = llm.invoke(
            prompt.format_messages(issues_json=issues_json)
        )
        raw_text = response.content.strip()

    except Exception as e:
        print("LLM call failed: ", e)
        return {"email": {}, "date": {}, "phone": {}}

    
    # JSON EXTRACTION

    try:
        cleaned = raw_text.strip()

        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`").strip()
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()

        start = cleaned.find("[")
        end = cleaned.rfind("]")

        if start == -1 or end == -1:
            raise ValueError("No JSON list found in LLM output")

        json_block = cleaned[start:end + 1]

        parsed = json.loads(json_block)

    except Exception as e:
        print(" JSON parse error:", e, "RAW:", raw_text)
        return {"email": {}, "date": {}, "phone": {}}

    
    #  BUILD OUTPUT STRUCTURE

    by_type = {"email": {}, "date": {}, "phone": {}}
    orig_map = {item["id"]: item for item in limited}

    for item in parsed:
        try:
            issue_id = item["id"]
            suggestion = item.get("suggestion", "")
            confidence = item.get("confidence", "medium")
            reason = item.get("reason", "")

            original = orig_map.get(issue_id)
            if not original:
                continue

            category = original["issue_type"] 
            row_idx = original["row_index"]

            entry = {
                "original": original["value"],
                "suggestion": suggestion,
                "confidence": confidence,
                "reason": reason
            }

            if category == "invalid_email":
                by_type["email"][row_idx] = entry
            elif category == "invalid_date":
                by_type["date"][row_idx] = entry
            elif category == "invalid_phone":
                by_type["phone"][row_idx] = entry

        except Exception as e:
            print(" Error processing LLM item:", e)

    return by_type

# CATEGORY INCONSISTENCY HELPER

def get_category_corrections(col_name: str, unique_values: list[str]):
    """
    Takes a column name + its unique values.
    Uses LLM to:
      - choose valid categories
      - provide suggestion + confidence + reason for invalid values

    Returns dict:
    {
      "valid": [...],
      "invalid": [
        {
          "original": "...",
          "suggestion": "...",
          "confidence": "high|medium|low",
          "reason": "..."
        },
        ...
      ]
    }
    """
    if not unique_values:
        return {"valid": [], "invalid": []}

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("⚠ GROQ_API_KEY not set – skipping category LLM.")
        return {"valid": [], "invalid": []}

    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        api_key=api_key,
        temperature=0.2,
    )

    prompt = ChatPromptTemplate.from_template(
        """
        You are a data cleaning assistant.

        You are given:
        - A column name: "{col_name}"
        - A JSON array of unique values from this column: {values_json}

        1. Decide which values are valid categories (canonical / clean values).
        2. For the remaining values, mark them as invalid and propose:
        - suggestion: corrected category (string)
        - confidence: "high" | "medium" | "low"
        - reason: short explanation (<= 1 sentence)

        Return STRICTLY valid JSON with this shape:

        {{
        "valid": ["category1", "category2", ...],
        "invalid": [
            {{
            "original": "raw value",
            "suggestion": "cleaned category",
            "confidence": "high",
            "reason": "why this was changed"
            }},
            ...
        ]
        }}
                """.strip()
    )

    messages = prompt.format_messages(
        col_name=col_name,
        values_json=json.dumps(unique_values, ensure_ascii=False),
    )

    try:
        resp = llm.invoke(messages)
        text = resp.content if hasattr(resp, "content") else str(resp)

        # isolate JSON
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            text = text[start : end + 1]

        data = json.loads(text)

        # shape check
        valid = data.get("valid", [])
        invalid = data.get("invalid", [])

        if not isinstance(valid, list):
            valid = []
        if not isinstance(invalid, list):
            invalid = []

        # normalise invalid entries
        cleaned_invalid = []
        for item in invalid:
            try:
                original = str(item.get("original", "")).strip()
                if not original:
                    continue
                cleaned_invalid.append(
                    {
                        "original": original,
                        "suggestion": str(item.get("suggestion", "")).strip(),
                        "confidence": str(item.get("confidence", "medium")).lower(),
                        "reason": str(item.get("reason", "")).strip(),
                    }
                )
            except Exception as e:
                print(" Category invalid item error:", e, item)

        return {"valid": valid, "invalid": cleaned_invalid}

    except Exception as e:
        print(" Category LLM call failed:", e)
        return {"valid": [], "invalid": []}

