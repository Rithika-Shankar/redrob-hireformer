import json
from pathlib import Path
from docx import Document


def load_jsonl(path):
    path = Path(path)
    candidates = []

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                candidates.append(json.loads(line))

    return candidates


def load_docx_text(path):
    doc = Document(path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def load_sample_json(path):
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)