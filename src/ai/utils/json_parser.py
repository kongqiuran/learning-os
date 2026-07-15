import json
import re


class LLMJSONParseError(ValueError):
    pass


def parse_llm_json(response_text):
    if not isinstance(response_text, str) or not response_text.strip():
        raise LLMJSONParseError("The LLM response is empty or is not text.")

    candidate = _extract_json_candidate(response_text)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError as initial_error:
        repaired = _repair_json(candidate)
        try:
            return json.loads(repaired)
        except json.JSONDecodeError as repaired_error:
            raise LLMJSONParseError(
                "Unable to parse the LLM response as JSON after lightweight repair. "
                f"Initial error: {initial_error.msg}; repaired error: {repaired_error.msg}."
            ) from repaired_error


def _extract_json_candidate(response_text):
    text = response_text.strip().lstrip("\ufeff")
    fenced_blocks = re.findall(
        r"```(?:json)?\s*(.*?)```",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    for block in fenced_blocks:
        if "{" in block or "[" in block:
            text = block.strip()
            break

    object_start = text.find("{")
    array_start = text.find("[")
    if object_start < 0 and array_start < 0:
        raise LLMJSONParseError("No JSON object or array was found in the LLM response.")

    # All current AI contracts return objects. Prefer an object when prose contains
    # bracketed notes before the actual JSON, while still supporting root arrays.
    start = object_start if object_start >= 0 else array_start
    extracted = _extract_balanced_value(text, start)
    return extracted.strip()


def _extract_balanced_value(text, start):
    opening = text[start]
    closing = "}" if opening == "{" else "]"
    stack = [closing]
    in_string = False
    escaped = False

    for index in range(start + 1, len(text)):
        character = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue

        if character == '"':
            in_string = True
        elif character == "{":
            stack.append("}")
        elif character == "[":
            stack.append("]")
        elif character in "}]":
            if stack and character == stack[-1]:
                stack.pop()
                if not stack:
                    return text[start : index + 1]

    return text[start:]


def _repair_json(candidate):
    repaired = _escape_control_characters_in_strings(candidate)
    repaired = _close_unterminated_json(repaired)
    return re.sub(r",\s*([}\]])", r"\1", repaired)


def _escape_control_characters_in_strings(text):
    replacements = {
        "\b": "\\b",
        "\f": "\\f",
        "\n": "\\n",
        "\r": "\\r",
        "\t": "\\t",
    }
    output = []
    in_string = False
    escaped = False

    for character in text:
        if in_string:
            if escaped:
                output.append(character)
                escaped = False
                continue
            if character == "\\":
                output.append(character)
                escaped = True
                continue
            if character == '"':
                output.append(character)
                in_string = False
                continue
            if ord(character) < 0x20:
                output.append(replacements.get(character, f"\\u{ord(character):04x}"))
                continue
        elif character == '"':
            in_string = True
        output.append(character)
    return "".join(output)


def _close_unterminated_json(text):
    stack = []
    in_string = False
    escaped = False
    for character in text:
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character == "{":
            stack.append("}")
        elif character == "[":
            stack.append("]")
        elif character in "}]" and stack and character == stack[-1]:
            stack.pop()

    suffix = '"' if in_string else ""
    return text.rstrip() + suffix + "".join(reversed(stack))
