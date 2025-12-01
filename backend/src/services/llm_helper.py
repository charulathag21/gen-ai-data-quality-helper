# backend/src/services/llm_helper.py
import os
import json
from typing import List, Dict, Any, Optional, Tuple

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

# Config / LLM client
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("⚠️ GROQ_API_KEY not found in environment variables!")

LLM_MODEL = "llama-3.1-8b-instant"

# Create a default llm instance; pass api_key if available
llm_kwargs = {"temperature": 0.2, "model_name": LLM_MODEL}
if GROQ_API_KEY:
    llm_kwargs["api_key"] = GROQ_API_KEY

llm = ChatGroq(**llm_kwargs)


# Helpers for JSON extraction
def _extract_first_balanced(text: str, open_ch: str, close_ch: str) -> Optional[str]:
    """
    Find the first balanced substring starting with open_ch and ending
    with its matching close_ch. Returns the substring including brackets/braces,
    or None if not found.
    This correctly handles nested braces/brackets.
    """
    start = text.find(open_ch)
    if start == -1:
        return None

    depth = 0
    for i in range(start, len(text)):
        ch = text[i]
        if ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1

        # When depth hits zero we've found the matching closing char
        if depth == 0:
            return text[start : i + 1]
    return None


def _extract_json_array(text: str) -> Optional[str]:
    # Try to extract a JSON array ([...] )
    return _extract_first_balanced(text, "[", "]")


def _extract_json_object(text: str) -> Optional[str]:
    # Try to extract a JSON object ({...})
    return _extract_first_balanced(text, "{", "}")


def _safe_json_load(s: str) -> Any:
    """Try json.loads and raise original exception for caller to handle."""
    return json.loads(s)


# Main function: corrections for email/date/phone
def get_llm_corrections(issues: List[Dict[str, Any]]):
    # If no issues, skip LLM entirely (prevents '"id"' errors)
    if not issues or len(issues) == 0:
        return {"email": {}, "date": {}, "phone": {}}


    limited = issues[:50]

    # SAFE GUARD:
    if len(limited) == 0:
        return {"email": {}, "date": {}, "phone": {}}

    issues_json = json.dumps(limited, ensure_ascii=False)

    # STRONGER SYSTEM MESSAGE TO FORCE CLEAN JSON ARRAY
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You output ONLY valid JSON array (no text, no explanations, no markdown). "
            "If no corrections are needed, return an empty array: []. "
            "Do not include ```json or any non-JSON characters."
        ),
        (
            "user",
    f"""
    Here is the list of issues:

    {issues_json}

    Return STRICT JSON array only, shaped like:

    [
    {{
        "id": <id>,
        "suggestion": "<corrected_value>",
        "confidence": "high|medium|low",
        "reason": "<short explanation>"
    }}
    ]

    RULES:
    - Emails: fix typos only.
    - Dates: convert to YYYY-MM-DD.
    - Phone numbers: convert to +international format.
    - DO NOT output anything outside the JSON array.
    """
            )
        ])

    # CALL LLM
    try:
        response = llm.invoke(prompt.format_messages())
        raw_text = getattr(response, "content", str(response)).strip()
    except Exception as e:
        print("LLM call failed (corrections):", e)
        return {"email": {}, "date": {}, "phone": {}}

    # 1st extraction: array-level extraction
    arr = _extract_json_array(raw_text)

    # 2nd fallback: try to wrap single objects into array
    if not arr:
        # maybe the model returned `{ "id": ... }`
        obj = _extract_json_object(raw_text)
        if obj:
            arr = f"[{obj}]"

    if not arr:
        print("Corrections JSON parse error: No JSON found. RAW:", raw_text)
        return {"email": {}, "date": {}, "phone": {}}

    # PARSE JSON
    try:
        parsed = json.loads(arr)
        if not isinstance(parsed, list):
            parsed = [parsed]
    except Exception as e:
        print("Corrections JSON decode error:", e, "RAW:", raw_text)
        return {"email": {}, "date": {}, "phone": {}}

    # BUILD FINAL STRUCTURE
    by_type = {"email": {}, "date": {}, "phone": {}}
    orig_map = {item["id"]: item for item in limited}

    for item in parsed:
        try:
            issue_id = item.get("id")
            orig = orig_map.get(issue_id)
            if not orig:
                continue

            category = orig["issue_type"]
            row = orig["row_index"]
            entry = {
                "original": orig["value"],
                "suggestion": item.get("suggestion", ""),
                "confidence": item.get("confidence", "medium"),
                "reason": item.get("reason", "")
            }

            if category == "invalid_email":
                by_type["email"][row] = entry
            elif category == "invalid_date":
                by_type["date"][row] = entry
            elif category == "invalid_phone":
                by_type["phone"][row] = entry

        except Exception as e:
            print("Corrections mapping error:", e, item)

    return by_type



# Category inconsistency helper
def get_category_corrections(col_name: str, unique_values: List[str]):
    if not unique_values:
        return {"valid": [], "invalid": []}

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("⚠️ GROQ_API_KEY not set – skipping category LLM.")
        return {"valid": [], "invalid": []}

    # Use a dedicated LLM instance using explicit api_key to avoid confusion
    cat_llm = ChatGroq(model="llama-3.1-8b-instant", api_key=api_key, temperature=0.2)

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
        col_name=col_name, values_json=json.dumps(unique_values, ensure_ascii=False)
    )

    try:
        resp = cat_llm.invoke(messages)
        raw = getattr(resp, "content", str(resp))

        # Extract the first JSON object from the response robustly
        obj_text = _extract_json_object(raw)
        if not obj_text:
            raise ValueError("No JSON object found in category LLM output")

        data = _safe_json_load(obj_text)

        # Validate shape
        valid = data.get("valid", [])
        invalid = data.get("invalid", [])
        if not isinstance(valid, list):
            valid = []
        if not isinstance(invalid, list):
            invalid = []

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
                print("Category invalid item error:", e, item)

        return {"valid": valid, "invalid": cleaned_invalid}

    except Exception as e:
        # Log the full LLM text for debugging
        print("Category LLM call failed:", e)
        try:
            print("Raw LLM output (truncated):", raw[:2000])
        except Exception:
            pass
        return {"valid": [], "invalid": []}
