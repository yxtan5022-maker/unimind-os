import sys

_EMOJI_SAFE: bool | None = None


def _check_emoji_safe() -> bool:
    global _EMOJI_SAFE
    if _EMOJI_SAFE is not None:
        return _EMOJI_SAFE
    try:
        "\U0001f310".encode(sys.stdout.encoding or "utf-8")
        _EMOJI_SAFE = True
    except (UnicodeEncodeError, UnicodeDecodeError):
        _EMOJI_SAFE = False
    return _EMOJI_SAFE


_EMOJI_MAP = {
    "\U0001f310": "[world]",
    "\U0001f517": "[link]",
    "\U0001f4e1": "[antenna]",
    "\U0001f680": "[rocket]",
    "\U0001f9e0": "[brain]",
    "\U0001f4a1": "[bulb]",
    "\U0001f525": "[fire]",
    "\U0001f504": "[sync]",
    "\u2705": "[OK]",
    "\U0001f7e2": "[green]",
    "\u26a1": "[zap]",
    "\U0001f50b": "[battery]",
    "\U0001f50d": "[search]",
    "\U0001f4ca": "[chart]",
    "\U0001f6e0": "[tools]",
    "\U0001f30c": "[galaxy]",
    "\U0001f52c": "[microscope]",
    "\U0001f4cc": "[pin]",
    "\U0001f4d6": "[book]",
    "\U0001f4c4": "[doc]",
    "\U0001f511": "[key]",
    "\U0001f6a9": "[flag]",
    "\U0001f3af": "[target]",
    "\u2795": "[+]",
    "\u2796": "[-]",
    "\u2709\ufe0f": "[mail]",
    "\u2600\ufe0f": "[sun]",
    "\u26a0\ufe0f": "[warning]",
    "\u2139\ufe0f": "[info]",
    "\U0001f6a8": "[alarm]",
    "\U0001f4a5": "[boom]",
    "\U0001f4ad": "[thought]",
    "\U0001f4ac": "[speech]",
    "\U0001f4bb": "[pc]",
    "\U0001f4f1": "[phone]",
    "\U0001f4ca": "[chart]",
    "\U0001f3b2": "[dice]",
    "\U0001f4a0": "[symbol]",
    "\u25b6": "[play]",
    "\U0001f53c": "[up]",
    "\U0001f53d": "[down]",
    "\U0001f3c6": "[trophy]",
    "\U0001f44b": "[wave]",
    "\U0001f91d": "[handshake]",
}


def safe_print(*args, **kwargs):
    if _check_emoji_safe():
        print(*args, **kwargs)
        return
    cleaned = []
    for a in args:
        s = str(a)
        for emoji, repl in _EMOJI_MAP.items():
            s = s.replace(emoji, repl)
        cleaned.append(s)
    print(*cleaned, **kwargs)
