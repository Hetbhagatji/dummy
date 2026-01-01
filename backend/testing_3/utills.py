def clean_llm_json(content: str) -> str:
    """
    Cleans LLM output by removing markdown code fences and extra whitespace.
    Ensures the string is ready for JSON parsing.
    """
    if not content:
        return ""

    # Strip leading/trailing whitespace
    content = content.strip()

    # Remove Markdown-style code fences
    if content.startswith("```"):
        # Remove ```json or ``` markers
        content = content.lstrip("```json").lstrip("```").strip()

    # Remove trailing ``` if any remain
    if content.endswith("```"):
        content = content.rstrip("```").strip()

    return content
