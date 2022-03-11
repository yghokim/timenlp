from datetime import datetime
from typing import Optional

from timenlp.types import RegexMatch

_named_numbers = (
    (1, r"an?|one"),
    (2, r"two"),
    (3, r"three"),
    (4, r"four"),
    (5, r"five"),
    (6, r"six"),
    (7, r"seven"),
    (8, r"eight"),
    (9, r"nine"),
    (10, r"ten"),
    (11, r"eleven"),
    (12, r"twelve"),
    (13, r"thirteen"),
    (14, r"fourteen"),
    (15, r"fifteen"),
    (16, r"sixteen"),
    (17, r"seventeen"),
    (18, r"eighteen"),
    (19, r"nineteen"),
    (20, r"twenty")
)

_tens = ["ten", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
_ones = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]

def _get_human_readable_number_regex_larger_than_20(n: int) -> Optional[str]:
    hundreds = n // 100
    tens = (n - hundreds * 100) // 10
    ones = (n - hundreds * 100 - tens * 10) % 10

    res = ""

    if hundreds >= 10:
        return None
    else:
        if hundreds > 0:
            res += _named_numbers[hundreds-1][1] + r"\s+hundreds?\s+(?:and\s+)?"
        if tens > 0:
            if ones == 0:
                res += _tens[tens-1]
            else:
                res += "{t}{o}|{t}-{o}|(?:{t} {o})".format(t=_tens[tens-1] ,o=_ones[ones-1]) 
        else:
            if ones > 0:
                res += _ones[ones-1]
        
        return res

_named_numbers += tuple((i, _get_human_readable_number_regex_larger_than_20(i)) for i in range(21, 60))

def make_rule_named_number(start_number: int=1, end_number: int=59, group_name_prefix="n_")->str:
    rule = "|".join(r"(?P<{}{}>{})".format(group_name_prefix, n, expr) for n, expr in _named_numbers[(start_number-1):end_number])
    return rule

def get_number_from_match(regex_match: RegexMatch, group_name_prefix="n_") -> Optional[int]:
    for n, _ in _named_numbers:
        match = regex_match.match.group(f"{group_name_prefix}{n}")
        if match:
            return n
    return None



_named_orders = [(i+1, re) for i, re in enumerate([
    "first",
    "second",
    "third",
    "fourth",
    "fifth",
    "sixth",
    "seventh",
    "eighth",
    "ninth",
    "tenth",
    "eleventh",
    "twelfth",
    "thirteenth",
    "fourteenth",
    "fifteenth",
    "sixteenth",
    "seventeenth",
    "eighteenth",
    "nineteenth",
    "twentieth",
    r"twenty-?first",
    r"twenty-?second",
    r"twenty-?third",
    r"twenty-?fourth",
    r"twenty-?fifth",
    r'twenty-?sixth',
    r"twenty-?seventh",
    r"twenty-?eighth",
    r"twenty-?ninth",
    r"thirtieth",
    r"thirty-?first"])]

def make_ordered_DOM_rule(group_name_prefix="dom_")->str:
    rule = "|".join(r"(?P<{}{}>{}\b)".format(group_name_prefix, n, re) for n, re in _named_orders)
    return rule

def get_DOM_from_match(regex_match: RegexMatch, group_name_prefix="dom_") -> Optional[int]:
    num = None
    for n, _ in _named_orders:
        match = regex_match.match.group(f"{group_name_prefix}{n}")
        if match:
            num = n
            continue
    return num