"""Simple integer, USD currency, and English month/day expansion."""
import re
from nepali_num2word import convert_to_words

_MONTHS = [
    ("January Jan", "जनवरी"), ("February Feb", "फेब्रुअरी"),
    ("March Mar", "मार्च"), ("April Apr", "अप्रिल"), ("May", "मे"),
    ("June Jun", "जुन"), ("July Jul", "जुलाई"), ("August Aug", "अगस्ट"),
    ("September Sept Sep", "सेप्टेम्बर"), ("October Oct", "अक्टोबर"),
    ("November Nov", "नोभेम्बर"), ("December Dec", "डिसेम्बर"),
]
MONTHS = {name.lower(): nepali for names, nepali in _MONTHS for name in names.split()}
DATE = re.compile(r"(?<!\w)(" + "|".join(sorted(MONTHS, key=len, reverse=True)) + r")\.?\s+(\d{1,2})(?!\w)", re.I)


def number_words(value):
    # Standardize the library spelling to the V1 pronunciation contract.
    return convert_to_words(int(value), lang="np").replace("पच्चिस", "पच्चीस")


def normalize_values(text, replace):
    def date(match):
        day = int(match[2])
        if not 1 <= day <= 31:
            raise ValueError("Day must be between 1 and 31")
        return f"{MONTHS[match[1].lower()]} {number_words(day)} तारिख"
    text = replace(DATE, date, text, "date")
    # V1 deliberately rejects fractional amounts instead of misreading them.
    if re.search(r"\d[.,]\d", text):
        raise ValueError("Decimals and grouped numbers are not supported in V1")
    text = replace(re.compile(r"\$\s*(\d+)(?!\w)"), lambda m: number_words(m[1]) + " अमेरिकी डलर", text, "currency")
    return replace(re.compile(r"(?<!\w)\d+(?!\w)"), lambda m: number_words(m[0]), text, "number")
