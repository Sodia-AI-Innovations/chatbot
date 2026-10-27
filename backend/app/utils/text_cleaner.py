import re

def clean_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    if _one_word_per_line(text):
        # broken PDF layout: every word on its own line, so join them back
        text = " ".join(text.split())
    return text

def _one_word_per_line(text: str) -> bool:
    lines = [line for line in text.split("\n") if line.strip()]
    if len(lines) < 20 :
        return False
    return sum(len(line.split()) for line in lines) / len(lines) < 1.5