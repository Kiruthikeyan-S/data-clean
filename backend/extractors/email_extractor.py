import email
from email import policy
from email.parser import BytesParser
from typing import Dict, Any, List

def extract_email(file_bytes: bytes) -> Dict[str, Any]:
    """
    Parses .eml or email messages and extracts From, To, Subject, Date, and text Body.
    """
    msg = BytesParser(policy=policy.default).parsebytes(file_bytes)
    
    sender = msg.get("from", "")
    to = msg.get("to", "")
    subject = msg.get("subject", "")
    date_str = msg.get("date", "")
    
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get("Content-Disposition"))
            
            # Skip attachments
            if "attachment" in cdispo:
                continue
            if ctype == "text/plain":
                body = part.get_content()
                break
            elif ctype == "text/html" and not body:
                # Fallback to html stripped if no plain text
                import re
                html_content = part.get_content()
                body = re.sub(r"<[^>]+>", " ", html_content)
    else:
        body = msg.get_content()
        
    formatted_parts: List[str] = []
    if sender:
        formatted_parts.append(f"From: {sender}")
    if to:
        formatted_parts.append(f"To: {to}")
    if subject:
        formatted_parts.append(f"Subject: {subject}")
    if date_str:
        formatted_parts.append(f"Date: {date_str}")
    if body:
        formatted_parts.append("\n" + body.strip())
        
    full_text = "\n".join(formatted_parts)
    
    return {
        "text": full_text,
        "headers": {
            "from": sender,
            "to": to,
            "subject": subject,
            "date": date_str
        },
        "confidence": 1.0,
        "extraction_method": "email_parser"
    }
