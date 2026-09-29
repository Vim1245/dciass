from prompts.system_prompts import BUSINESS_ASSISTANT_PROMPT
from prompts.few_shot import FEW_SHOT_EXAMPLES


def build_prompt(
    user_message: str,
    context: str = ""
) -> str:

    prompt = f"""
{BUSINESS_ASSISTANT_PROMPT}

{FEW_SHOT_EXAMPLES}

Additional Context:
{context if context else "No additional context provided."}

User Request:
{user_message}

Answer the user request based on the instructions above.
"""

    return prompt