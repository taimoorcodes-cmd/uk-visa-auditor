"""Student uploads a screenshot of a confusing form field. The AI explains it in easy words."""
import base64
from io import BytesIO

from . import config, llm

SYSTEM = (
    "You help students who are filling in the UK Student visa online form. "
    "Explain the field or question in the screenshot in very easy English: what it means, "
    "what kind of answer is needed, and where to find the information (for example CAS, passport, bank). "
    "Rules: Do not guess personal data. Do not tell the student to hide or change facts. "
    "If you are not sure, say so and tell them to check the official page on gov.uk/student-visa. "
    "Never promise visa results. Use short sentences. Maximum 150 words."
)


def _prepare(image_bytes: bytes) -> str:
    """Shrink the picture (faster, cheaper) and return a data URL."""
    from PIL import Image

    with Image.open(BytesIO(image_bytes)) as img:
        img = img.convert("RGB")
        img.thumbnail((1400, 1400))
        out = BytesIO()
        img.save(out, format="JPEG", quality=80)
    return "data:image/jpeg;base64," + base64.b64encode(out.getvalue()).decode()


def explain_screenshot(image_bytes: bytes, question: str = "", language: str = "en"):
    """Returns (ok, text)."""
    if not config.VISION_MODEL:
        return False, ("Screenshot help is not set up. Add VISION_MODEL=<a model that accepts images> "
                       "to your .env file (see openrouter.ai/models).")
    try:
        data_url = _prepare(image_bytes)
    except Exception:
        return False, "We could not open this picture. Please upload a PNG or JPG file."
    lang = "Write the answer in simple Urdu." if language == "ur" else "Write the answer in very easy English."
    text_part = (question.strip() or "Explain this field and tell me what to write.") + " " + lang
    answer = llm.chat(
        [{"role": "system", "content": SYSTEM},
         {"role": "user", "content": [{"type": "text", "text": text_part},
                                      {"type": "image_url", "image_url": {"url": data_url}}]}],
        max_tokens=450, temperature=0.2, model=config.VISION_MODEL,
    )
    if not answer:
        return False, "The AI could not read this picture right now. Please try again, or check the official gov.uk page."
    return True, answer