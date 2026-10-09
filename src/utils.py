"""
ClipMaster Utility Functions
Type detection, time formatting, and text helpers.
"""

import re
import time
from urllib.parse import urlparse

# URL regex
URL_REGEX = re.compile(
    r'^(?:http|ftp)s?://' # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain...
    r'localhost|' # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
    r'(?::\d+)?' # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE
)

# Color regex
HEX_COLOR_REGEX = re.compile(r'^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$')
RGB_COLOR_REGEX = re.compile(r'^rgba?\s*\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*(?:,\s*[\d.]+\s*)?\)$', re.IGNORECASE)
HSL_COLOR_REGEX = re.compile(r'^hsla?\s*\(\s*\d+\s*,\s*[\d.]+%?\s*,\s*[\d.]+%?\s*(?:,\s*[\d.]+\s*)?\)$', re.IGNORECASE)

# Code detection keywords & patterns
CODE_KEYWORDS = [
    r'\bdef\s+\w+\s*\(', r'\bfunction\s+\w*\s*\(', r'\bclass\s+\w+',
    r'\bimport\s+[\w\s,]+', r'\bfrom\s+\w+\s+import', r'#include\s*<',
    r'\bconst\s+\w+\s*=', r'\blet\s+\w+\s*=', r'\bvar\s+\w+\s*=',
    r'console\.log\(', r'print\(', r'SELECT\s+.*\s+FROM\s+', r'INSERT\s+INTO\s+',
    r'UPDATE\s+.*\s+SET\s+', r'<!DOCTYPE\s+html>', r'<\s*(?:div|span|p|a|script|html|body|table|button)\b',
    r'#!/bin/(?:bash|sh|zsh|python)', r'\bsudo\s+apt', r'\bgit\s+(?:commit|push|pull|status|checkout|branch)',
    r'\bdocker\s+(?:run|ps|build|compose)', r'\bnpm\s+(?:install|run|start|test)',
    r'curl\s+-', r'wget\s+', r'pip\s+install'
]
CODE_REGEX = re.compile('|'.join(CODE_KEYWORDS), re.IGNORECASE)


def detect_content_type(text: str) -> str:
    """
    Detect the type of copied text:
    - 'color'
    - 'url'
    - 'code'
    - 'text'
    """
    if not text:
        return 'text'
    
    clean_text = text.strip()
    
    # 1. Color
    if HEX_COLOR_REGEX.match(clean_text) or RGB_COLOR_REGEX.match(clean_text) or HSL_COLOR_REGEX.match(clean_text):
        return 'color'
    
    # 2. URL
    if URL_REGEX.match(clean_text) or (clean_text.startswith(('http://', 'https://')) and len(clean_text.splitlines()) == 1):
        return 'url'
    
    # 3. JSON
    if (clean_text.startswith('{') and clean_text.endswith('}')) or (clean_text.startswith('[') and clean_text.endswith(']')):
        if len(clean_text) > 10 and (':' in clean_text or ',' in clean_text):
            return 'code'
    
    # 4. Code detection
    if CODE_REGEX.search(clean_text):
        return 'code'
    
    # Indentation / syntax symbols check for multi-line code
    lines = clean_text.splitlines()
    if len(lines) >= 3:
        code_markers = sum(1 for line in lines if line.strip().endswith((';', '{', '}', ':', ')')) or line.startswith(('    ', '\t')))
        if code_markers / len(lines) > 0.4:
            return 'code'
    
    return 'text'


def extract_domain(url: str) -> str:
    """Extract domain name from URL for display."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except Exception:
        return "link"


def format_relative_time(timestamp: float, lang: str = "vi") -> str:
    """Format Unix timestamp into human-friendly localized relative time."""
    from .i18n import t
    diff = time.time() - timestamp
    if diff < 10:
        return t("time_just_now", lang)
    elif diff < 60:
        return t("time_secs_ago", lang, secs=int(diff))
    elif diff < 3600:
        minutes = max(1, int(diff / 60))
        return t("time_mins_ago", lang, mins=minutes)
    elif diff < 86400:
        hours = max(1, int(diff / 3600))
        return t("time_hours_ago", lang, hours=hours)
    elif diff < 172800:
        t_struct = time.localtime(timestamp)
        return t("time_yesterday", lang, time=f"{t_struct.tm_hour:02d}:{t_struct.tm_min:02d}")
    else:
        t_struct = time.localtime(timestamp)
        if lang == "en":
            return f"{t_struct.tm_year}-{t_struct.tm_mon:02d}-{t_struct.tm_mday:02d}"
        return f"{t_struct.tm_mday:02d}/{t_struct.tm_mon:02d}/{t_struct.tm_year}"


def truncate_text(text: str, max_chars: int = 160, max_lines: int = 1) -> str:
    """Truncate text for single-line or multi-line preview display."""
    if not text:
        return ""
    lines = text.strip().splitlines()
    if max_lines <= 1:
        first_line = lines[0] if lines else ""
        if len(lines) > 1:
            first_line += f" ... (+{len(lines)-1} dòng)"
        if len(first_line) > max_chars:
            return first_line[:max_chars].rstrip() + "..."
        return first_line
    else:
        selected_lines = lines[:max_lines]
        result = "\n".join(selected_lines)
        if len(lines) > max_lines:
            result += f"\n... (+{len(lines)-max_lines} dòng)"
        if len(result) > max_chars:
            return result[:max_chars].rstrip() + "..."
        return result
