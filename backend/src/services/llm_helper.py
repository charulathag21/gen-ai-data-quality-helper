# backend/src/services/llm_helper.py
import os
import json
import re
from typing import List, Dict, Any, Optional, Tuple

# NOTE: adjust imports if your langchain_groq package differs
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

# ----------------- Logging helper -----------------
def _log(*args):
    # simple wrapper so we can control logging from one place
    print(*args)


# ----------------- JSON extraction helpers -----------------
def extract_balanced_json(text: str) -> Optional[str]:
    """
    Find the first balanced JSON array or object in text.
    Handles nested brackets/braces and common wrappers like ```json ... ```
    Returns the substring (including outer [] or {}) or None.
    """
    if not text:
        return None

    # remove common triple-backtick blocks but keep inner text
    # e.g. ```json\n{...}\n```
    cleaned = text.strip()
    # if code fences exist, prefer content inside them
    fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, flags=re.S | re.I)
    if fence_match:
        candidate = fence_match.group(1).strip()
        # try to parse candidate directly later
        cleaned = candidate

    # find first '[' or '{' and then match balanced block
    first_open = None
    for i, ch in enumerate(cleaned):
        if ch == "[" or ch == "{":
            first_open = i
            open_ch = ch
            close_ch = "]" if ch == "[" else "}"
            break

    if first_open is None:
        return None

    depth = 0
    for j in range(first_open, len(cleaned)):
        c = cleaned[j]
        if c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                # return the balanced block
                return cleaned[first_open:j + 1]

    return None


def parse_json_safe(raw_text: str) -> Optional[Any]:
    """
    Try json.loads normally. If that fails, try to extract a balanced JSON block.
    Returns parsed object or None.
    """
    if raw_text is None:
        return None

    txt = raw_text.strip()
    # quick attempt
    try:
        return json.loads(txt)
    except Exception:
        pass

    # attempt to remove surrounding code fences
    fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", txt, flags=re.S | re.I)
    if fence_match:
        txt = fence_match.group(1).strip()
        try:
            return json.loads(txt)
        except Exception:
            pass

    # find first balanced JSON block and parse it
    jblock = extract_balanced_json(txt)
    if jblock:
        try:
            return json.loads(jblock)
        except Exception as e:
            _log("parse_json_safe: json.loads failed on extracted block:", e, "BLOCK:", jblock[:200])
            return None

    # try to salvage by finding first { ... } or [ ... ] groups with regex fallback
    obj_match = re.search(r"(\{[\s\S]*\})", txt)
    if obj_match:
        try:
            return json.loads(obj_match.group(1))
        except Exception:
            pass

    arr_match = re.search(r"(\[[\s\S]*\])", txt)
    if arr_match:
        try:
            return json.loads(arr_match.group(1))
        except Exception:
            pass

    # give up
    return None


# ----------------- LLM (Groq) initialization -----------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    _log("⚠️ GROQ_API_KEY not set in environment variables. LLM calls will likely fail.")

LLM_MODEL = "llama-3.1-8b-instant"

# Create a single client instance with API key if available
try:
    if GROQ_API_KEY:
        llm = ChatGroq(temperature=0.2, model_name=LLM_MODEL, api_key=GROQ_API_KEY)
    else:
        # still create client without api_key (will error at call)
        llm = ChatGroq(temperature=0.2, model_name=LLM_MODEL)
except Exception as e:
    llm = None
    _log("Failed to create ChatGroq client:", e)


# ----------------- Main function: corrections for emails/dates/phones -----------------
def get_llm_corrections(issues: List[Dict[str, Any]]) -> Dict[str, Dict[int, Dict[str, Any]]]:
    """
    issues: list of dicts like:
      { "id": int, "issue_type": "invalid_email"|"invalid_date"|"invalid_phone",
        "column": str, "row_index": int, "value": str }

    returns:
      {
        "email": { row_index: { original, suggestion, confidence, reason } },
        "date":  { ... },
        "phone": { ... }
      }
    """

    default_out = {"email": {}, "date": {}, "phone": {}}
    if not issues:
        return default_out

    if llm is None:
        _log("LLM client not initialized; skipping corrections.")
        return default_out

    limited = issues[:50]
    issues_json = json.dumps(limited, ensure_ascii=False)

    # Build prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a strict JSON-only data cleaning assistant. You always output EXACT JSON (array only). No backticks, no explanations, no text outside JSON."),
        ("user", f"""
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
  }},
  ...
]

IMPORTANT:
- Emails: fix typos only (e.g. user[at]example.com -> user@example.com).
- Dates: convert to YYYY-MM-DD when possible.
- Phone: convert to +international format if you can infer country; otherwise leave suggestion empty.
- Output JSON array only. Do not return any explanatory text.
""")
    ])

    try:
        messages = prompt.format_messages()
        # format_messages may accept kwargs depending on version; we already injected issues_json into the user message above.
        response = llm.invoke(messages)
        raw_text = getattr(response, "content", str(response)).strip()
    except Exception as e:
        _log("LLM call failed:", e)
        return default_out

    parsed = parse_json_safe(raw_text)
    if parsed is None:
        _log("JSON parse error for LLM corrections. RAW:", raw_text[:1000])
        return default_out

    # Parsed expected to be list
    if not isinstance(parsed, list):
        _log("LLM returned JSON but not a list for corrections. TYPE:", type(parsed), "VALUE:", str(parsed)[:200])
        return default_out

    # build mapping from id -> original issue
    orig_map = {item["id"]: item for item in limited if "id" in item}

    out = {"email": {}, "date": {}, "phone": {}}
    for item in parsed:
        try:
            if not isinstance(item, dict):
                continue
            issue_id = item.get("id")
            if issue_id is None:
                continue
            orig = orig_map.get(issue_id)
            if not orig:
                continue

            suggestion = item.get("suggestion", "").strip()
            confidence = str(item.get("confidence", "medium")).lower()
            reason = str(item.get("reason", "")).strip()

            entry = {
                "original": orig.get("value"),
                "suggestion": suggestion,
                "confidence": confidence,
                "reason": reason
            }

            cat = orig.get("issue_type")
            if cat == "invalid_email":
                out["email"][orig.get("row_index")] = entry
            elif cat == "invalid_date":
                out["date"][orig.get("row_index")] = entry
            elif cat == "invalid_phone":
                out["phone"][orig.get("row_index")] = entry

        except Exception as e:
            _log("Error processing LLM item:", e, "ITEM:", item)

    return out


# ----------------- Category inconsistency helper -----------------
def get_category_corrections(col_name: str, unique_values: List[str]) -> Dict[str, Any]:
    """
    Returns:
    {
      "valid": [list of canonical values],
      "invalid": [
         { "original": "...", "suggestion": "...", "confidence": "high|medium|low", "reason": "..." },
         ...
      ]
    }
    """
    if not unique_values:
        return {"valid": [], "invalid": []}

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        _log("⚠ GROQ_API_KEY not set – skipping category LLM.")
        return {"valid": [], "invalid": []}

    # create per-call client (safer) or reuse: using local client with API key
    try:
        client = ChatGroq(model=LLM_MODEL, api_key=api_key, temperature=0.2)
    except Exception as e:
        _log("Failed to create ChatGroq client in category helper:", e)
        return {"valid": [], "invalid": []}

    values_json = json.dumps(unique_values, ensure_ascii=False)

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

{
  "valid": ["category1", "category2", ...],
  "invalid": [
    {
      "original": "raw value",
      "suggestion": "cleaned category",
      "confidence": "high",
      "reason": "why this was changed"
    }
    ...
  ]
}
        """.strip()
    )

    try:
        messages = prompt.format_messages(col_name=col_name, values_json=values_json)
        resp = client.invoke(messages)
        raw_text = getattr(resp, "content", str(resp)).strip()
    except Exception as e:
        _log("Category LLM call failed:", e)
        return {"valid": [], "invalid": []}

    parsed = parse_json_safe(raw_text)
    if parsed is None or not isinstance(parsed, dict):
        _log("Category JSON error: could not parse JSON. RAW:", raw_text[:1000])
        return {"valid": [], "invalid": []}

    # Normalize results
    valid = parsed.get("valid", [])
    invalid = parsed.get("invalid", [])

    if not isinstance(valid, list):
        valid = []
    if not isinstance(invalid, list):
        invalid = []

    cleaned_invalid = []
    for it in invalid:
        try:
            if not isinstance(it, dict):
                continue
            original = str(it.get("original", "")).strip()
            if not original:
                continue
            suggestion = str(it.get("suggestion", "")).strip()
            confidence = str(it.get("confidence", "medium")).lower()
            if confidence not in ("high", "medium", "low"):
                confidence = "medium"
            reason = str(it.get("reason", "")).strip()
            cleaned_invalid.append({
                "original": original,
                "suggestion": suggestion,
                "confidence": confidence,
                "reason": reason
            })
        except Exception as e:
            _log("Category invalid item error:", e, it)

    return {"valid": valid, "invalid": cleaned_invalid}
