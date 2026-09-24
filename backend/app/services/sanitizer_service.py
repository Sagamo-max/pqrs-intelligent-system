import re
import spacy

nlp = spacy.load("es_core_news_sm")

def mask_regex_patterns(text: str) -> str:

    text = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '[MASKED_EMAIL]', text)

    text = re.sub(r'\b3\d{9}\b', '[MASKED_PHONE]', text)

    text = re.sub(r'(?i)(cédula|cedula|cc|c\.c\.|documento|id)\s*(?:es|nro|número|numero|#|:)?\s*\d{7,10}', r'\g<1> [MASKED_DOCUMENT]', text)
    
    return text

def mask_ner_patterns(text: str) -> str:
    doc = nlp(text)
    masked_text = text
    
    for ent in doc.ents:
        if ent.label_ == "PER":
            masked_text = masked_text.replace(ent.text, "[MASKED_NAME]")
            
    return masked_text

def sanitize_text(text: str) -> str:
    regex_masked = mask_regex_patterns(text)
    fully_masked = mask_ner_patterns(regex_masked)
    return fully_masked