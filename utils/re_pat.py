import re

PHONE_RULE = '^1[3589]\d{9}$'
PHONE_PAT = re.compile(PHONE_RULE)
