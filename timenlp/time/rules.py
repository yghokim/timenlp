import re
from string import digits
from time import time
from typing import List, Optional, Any, Tuple, cast
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, MONTHLY
from timenlp.helpers import get_DOM_from_match, get_number_from_match, make_ordered_DOM_rule, make_rule_named_number

from timenlp.time.postprocess_latent import _latent_tod
from ..rule import rule, predicate, dimension, _regex_to_join
from ..types import Time, Duration, Interval, pod_hours, RegexMatch, DurationUnit


#Absorb###########################################################################

@rule(
    r"at|on|the|approximately|about|(?:in|of)(?: the)?|around",
    dimension(Time),
)
def ruleAbsorbOnTime(ts: datetime, _: RegexMatch, t: Time) -> Time:
    return t

@rule(
    r"approximately|about|around",
    dimension(Duration),
)
def ruleAbsorbOnDuration(ts: datetime, _: RegexMatch, t: Duration) -> Duration:
    return t

@rule(r"from|between", dimension(Interval))
def ruleAbsorbFromInterval(ts: datetime, _: Any, i: Interval) -> Interval:
    return i

##################################################################################

_dows = [
    ("mon", r"mondays?"),
    ("tue", r"tuesdays?"),
    ("wed", r"wednesdays?"),
    ("thu", r"thurstdays?"),
    ("fri", r"fridays?"),
    ("sat", r"saturdays?"),
    ("sun", r"sundays?"),
]
_rule_dows = r"|".join(r"(?P<{}>{})".format(dow, expr) for dow, expr in _dows)
_rule_dows = r"(?:{})\s*".format(_rule_dows)

@rule(_rule_dows)
def ruleNamedDOW(ts: datetime, m: RegexMatch) -> Optional[Time]:
    for i, (name, _) in enumerate(_dows):
        if m.match.group(name):
            return Time(DOW=i)
    return None


_months = [
    ("january", r"january?|jan\.?"),
    ("february", r"february?|feb\.?"),
    ("march", r"march|mar\.?"),
    ("april", r"april|apr\.?"),
    ("may", r"may\.?"),
    ("june", r"june|jun\.?"),
    ("july", r"july|jul\.?"),
    ("august", r"august|aug\.?"),
    ("september", r"september|sept?\.?"),
    ("october", r"october|oct\.?"),
    ("november", r"november|nov\.?"),
    ("december", r"december|dec\.?"),
]
_rule_months = "|".join(r"(?P<{}>{})".format(name, expr) for name, expr in _months)


@rule(_rule_months)
def ruleNamedMonth(ts: datetime, m: RegexMatch) -> Optional[Time]:
    match = m.match
    for i, (name, _) in enumerate(_months):
        if match.group(name):
            return Time(month=i + 1)
    return None


_named_ts = (
    (1, r"one"),
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
)
_rule_named_ts = "|".join(r"(?P<t_{}>{})".format(n, expr) for n, expr in _named_ts)
_rule_named_ts = r"(?:{})\s*".format(_rule_named_ts)

@rule( _rule_named_ts + r"(?:h|o\'?clock)?")
def ruleNamedHour(ts: datetime, m: RegexMatch) -> Optional[Time]:
    match = m.match
    for n, _, in _named_ts:
        if match.group("t_{}".format(n)):
            return Time(hour=n, minute=0, meridiemLatent=True)
    return None


@rule(r"midnight")
def ruleMidnight(ts: datetime, _: RegexMatch) -> Time:
    return Time(hour=0, minute=0)


def _pod_from_match(pod: str, m: RegexMatch) -> str:
    mod = ""
    if m.match.group("mod_early"):
        mod = "early"
    elif m.match.group("mod_late"):
        mod = "late"
    if m.match.group("mod_very"):
        mod = "very" + mod
    return mod + pod


@rule(
    r"(?P<mod_very>(sehr|very)\s+)?"
    "((?P<mod_early>früh(e(r|n|m))?|early)"
    "|(?P<mod_late>(spät(e(r|n|m))?|late)))",
    predicate("isPOD"),
)
def ruleEarlyLatePOD(ts: datetime, m: RegexMatch, p: Time) -> Time:
    return Time(POD=_pod_from_match(p.POD, m))


    """
    (
        "first",
        (
            r"(erster?|first|earliest|as early|frühe?st(ens?)?|so früh)"
            "( (as )?possible| (wie )?möglich(er?)?)?"
        ),
    ),
    (
        "last",
        (
            r"(letzter?|last|latest|as late as possible|spätest möglich(er?)?|"
            "so spät wie möglich(er?)?)"
        ),
    ),"""
_pods = [
    ("earlymorning", r"very early"),
    ("lateevening", r"very late"),
    ("morning", r"morning|early"),
    ("forenoon", r"forenoon"),
    ("afternoon", r"afternoon"),
    ("noon", r"noon"),
    ("evening", r"evening|tonight|late"),
    ("night", r"night"),
]

_rule_pods = "|".join("(?P<{}>{})".format(pod, expr) for pod, expr in _pods)


@rule(_rule_pods)
def rulePOD(ts: datetime, m: RegexMatch) -> Optional[Time]:
    for _, (pod, _) in enumerate(_pods):
        if m.match.group(pod):
            return Time(POD=pod)
    return None

@rule(r"(?<!\d|\.)(?P<day>(?&_day))\.?(?!\d)")
def ruleDOM1(ts: datetime, m: RegexMatch) -> Time:
    # Ordinal day "5."
    return Time(day=int(m.match.group("day")))


@rule(r"(?<!\d|\.)(?P<month>(?&_month))\.?(?!\d)")
def ruleMonthOrdinal(ts: datetime, m: RegexMatch) -> Time:
    # Ordinal day "5."
    return Time(month=int(m.match.group("month")))


@rule(r"(?:the\s+)?(?<!\d|\.)(?P<day>(?&_day))\s*(?:st|nd|rd|th)")
# a "[0-31]" followed by a th/st
def ruleDOM2(ts: datetime, m: RegexMatch) -> Time:
    return Time(day=int(m.match.group("day")))

@rule(r"{}".format(make_ordered_DOM_rule()))
def ruleDOMOrdered(ts: datetime, m: RegexMatch) -> Time:
    day = get_DOM_from_match(m)
    return Time(day=day)

@rule(r"(?<!\d|\.)(?P<year>(?&_year))(?!\d)")
def ruleYear(ts: datetime, m: RegexMatch) -> Optional[Time]:
    # Since we may have two-digits years, we have to make a call
    # on how to handle which century does the time refers to.
    # We are using a strategy inspired by excel. Reference:
    # https://github.com/comtravo/ctparse/issues/56
    # https://docs.microsoft.com/en-us/office/troubleshoot/excel/two-digit-year-numbers
    y = int(m.match.group("year"))
    SAME_CENTURY_THRESHOLD = 10

    # Let the reference year be ccyy (e.g. 1983 => cc=19, yy=83)
    cc = ts.year // 100
    yy = ts.year % 100
    # Check if year is two digits
    
    if y < 100:
        """
        # Then any two digit year between 0 and
        # yy+10 is interpreted to be within the
        #  century cc (e.g. 83 maps to 1983, 93 to 1993),
        # anything above maps to the previous century (e.g. 94 maps to 1894).
        if y < yy + SAME_CENTURY_THRESHOLD:
            return Time(year=cc * 100 + y)
        else:
            return Time(year=(cc - 1) * 100 + y)
        """
        #We suppose two-digit years are not supported.
        return None
    else:
        return Time(year=y)


@rule(
    r"todays?|(?:at this time)"
)
def ruleToday(ts: datetime, _: RegexMatch) -> Time:
    return Time(year=ts.year, month=ts.month, day=ts.day)


@rule(
    r"(?:(?:just|right)\s*)?now|immediately"
)
def ruleNow(ts: datetime, _: RegexMatch) -> Time:
    return Time(
        year=ts.year, month=ts.month, day=ts.day, hour=ts.hour, minute=ts.minute
    )


@rule(r"tomorrow")
def ruleTomorrow(ts: datetime, _: RegexMatch) -> Time:
    dm = ts + relativedelta(days=1)
    return Time(year=dm.year, month=dm.month, day=dm.day)

@rule(r"yesterdays?")
def ruleYesterday(ts: datetime, _: RegexMatch) -> Time:
    dm = ts + relativedelta(days=-1)
    return Time(year=dm.year, month=dm.month, day=dm.day)

@rule(r"(?:the )?(?:(?:(?:end)|(?:last day)) of)", predicate("isYearAndMonth"))
def ruleEOM(ts: datetime, _: RegexMatch, ym: Time) -> Time:
    dm = datetime(year = ym.year, month = ym.month, day=1) + relativedelta(day=1, months=1, days=-1)
    return Time(year=dm.year, month=dm.month, day=dm.day)

@rule(r"(?:the )?(?:(?:(?:end)|(?:last day)) of)", predicate("isYear"))
def ruleEOY(ts: datetime, _: RegexMatch, y: Time) -> Time:
    dm = datetime(year=y.year, month=1, day=1) + relativedelta(day=1, month=1, years=1, days=-1)
    return Time(year=dm.year, month=dm.month, day=dm.day)


_rule_dom = r"\b(?P<dom>\d\d?)(?:st|nd|rd|th)?\b"

@rule(_rule_dom, predicate("isMonth"))
def ruleDOMMonth(ts: datetime, d: RegexMatch, m: Time) -> Time:
    return Time(day=int(d.match.group("dom")), month=m.month)


@rule(_rule_dom + r"\s+of", predicate("isMonth"))
def ruleDOMMonth2(ts: datetime, d: RegexMatch, m: Time) -> Time:
    return Time(day=int(d.match.group("dom")), month=m.month)


@rule(predicate("isMonth"), _rule_dom)
def ruleMonthDOM(ts: datetime, m: Time, d: RegexMatch) -> Time:
    return Time(month=m.month, day=int(d.match.group("dom")))


@rule(predicate("isMonth"), predicate("isDOM"))
def ruleMonthDOMLiteral(ts: datetime, m: Time, d: Time) -> Time:
    return Time(month=m.month, day=d.day)


@rule(r"this", predicate("isDOW"))
def ruleAtDOW(ts: datetime, _: RegexMatch, dow: Time) -> Time:
    dm = ts + relativedelta(weekday=dow.DOW)
    if dm.date() == ts.date():
        dm += relativedelta(weeks=1)
    return Time(year=dm.year, month=dm.month, day=dm.day)


@rule(
   r"(?:(?:on |at )?(the )?(?:(?:next|following)(?: week)?))",
    predicate("isDOW"),
)
def ruleNextDOW(ts: datetime, _: RegexMatch, dow: Time) -> Time:
    dm = ts + relativedelta(weekday=dow.DOW, weeks=1)
    return Time(year=dm.year, month=dm.month, day=dm.day)


@rule(predicate("isDOW"), r"(?:(?:on|at|of)\s+)?(the )?(next|following) week")
def ruleDOWNextWeek(ts: datetime, dow: Time, _: RegexMatch) -> Time:
    dm = ts + relativedelta(weekday=dow.DOW, weeks=1)
    return Time(year=dm.year, month=dm.month, day=dm.day)


@rule(predicate("isDOY"), predicate("isYear"))
def ruleDOYYear(ts: datetime, doy: Time, y: Time) -> Time:
    return Time(year=y.year, month=doy.month, day=doy.day)


@rule(predicate("isDOY"), r"of|in", predicate("isYear"))
def ruleDOYOfYear(ts: datetime, doy: Time, _:RegexMatch, y: Time) -> Time:
    return Time(year=y.year, month=doy.month, day=doy.day)

@rule(predicate("isDOW"), predicate("isPOD"))
def ruleDOWPOD(ts: datetime, dow: Time, pod: Time) -> Time:
    return Time(DOW=dow.DOW, POD=pod.POD)


@rule(predicate("isDOW"), predicate("isDOM"))
def ruleDOWDOM(ts: datetime, dow: Time, dom: Time) -> Time:
    # Monday 5th
    # Find next date at this day of week and day of month
    dtstart = ts
    delta_unit = relativedelta(months = -1)
    dm: datetime = None
    while dm is None:
        dtstart += delta_unit
        dm_candidate = rrule(MONTHLY, dtstart=dtstart, byweekday=dow.DOW, bymonthday=dom.day, count=1)
        if dm_candidate[0] < ts + YEAR_LATENT_TOLERANCE_FUTURE:
            dm = dm_candidate[0]
    return Time(year=dm.year, month=dm.month, day=dm.day)


@rule(predicate("hasDOW"), predicate("isDate"))
def ruleDOWDate(ts: datetime, dow: Time, date: Time) -> Time:
    # Monday 5th December - ignore DOW, but carry over e.g. POD from dow
    return Time(date.year, date.month, date.day, POD=dow.POD)


@rule(predicate("isDate"), predicate("hasDOW"))
def ruleDateDOW(ts: datetime, date: Time, dow: Time) -> Time:
    # Monday 5th December - ignore DOW, but carry over e.g. POD from dow
    return Time(date.year, date.month, date.day, POD=dow.POD)

@rule(r"(?P<next_or_last>next|last) (?:(?P<year>years?)|(?P<month>months?))")
def ruleNextOrLastYearOrMonth(ts: datetime, m: RegexMatch) -> Optional[Time]:
    delta_amount = (1 if m.match.group("next_or_last") == "next" else -1)

    if m.match.group("year"):
        return Time(year=(ts + relativedelta(years = delta_amount)).year)
    elif m.match.group("month"):
        ym = (ts + relativedelta(months = delta_amount))
        return Time(year=ym.year, month=ym.month)
    else:
        return None


@rule(r"(?:this|the) (?:(?P<year>years?)|(?P<month>months?))")
def ruleThisYearOrMonth(ts: datetime, m: RegexMatch) -> Optional[Time]:
    if m.match.group("year"):
        return Time(year=ts.year)
    elif m.match.group("month"):
        return Time(year=ts.year, month=ts.month)
    else:
        return None

# LatentX: handle time entities that are not grounded to a date yet
###############################################################################################
# and assume the previous date+time in the past, considering the personal informatics context.

YEAR_LATENT_TOLERANCE_FUTURE = relativedelta(months = 1) #Tolerate one month future


@rule(predicate("isDOM"))
def ruleLatentDOM(ts: datetime, dom: Time) -> Time:
    dm = ts + relativedelta(day=dom.day)
    if dm >= ts:
        dm -= relativedelta(months=1)
    return Time(year=dm.year, month=dm.month, day=dm.day)

WEEK_LATENT_TOLERANCE_FUTURE = relativedelta(days = 1)

@rule(predicate("isDOW"))
def ruleLatentDOW(ts: datetime, dow: Time) -> Time:
    dm = ts + relativedelta(weekday=dow.DOW)
    if dm > ts + WEEK_LATENT_TOLERANCE_FUTURE:
        dm -= relativedelta(weeks=1)
    return Time(year=dm.year, month=dm.month, day=dm.day)

@rule(predicate("isMonth"))
def ruleLatentMonth(ts: datetime, month: Time) -> Time:
    dm = ts + relativedelta(month=month.month)
    if dm >= ts + YEAR_LATENT_TOLERANCE_FUTURE:
        dm -= relativedelta(years=1)
    elif dm + relativedelta(years=1) < ts + YEAR_LATENT_TOLERANCE_FUTURE:
        dm += relativedelta(years=1)

    return Time(year=dm.year, month=dm.month)

def _ruleLatentDOY(ts: datetime, doy: Time) -> Time:
    dm = ts + relativedelta(month=doy.month, day=doy.day)

    if dm > ts + YEAR_LATENT_TOLERANCE_FUTURE:
        dm -= relativedelta(years=1)
    elif dm + relativedelta(years=1) < ts + YEAR_LATENT_TOLERANCE_FUTURE:
        dm += relativedelta(years=1)
    return Time(year=dm.year, month=dm.month, day=dm.day)

@rule(predicate("isDOY"))
def ruleLatentDOY(ts: datetime, doy: Time) -> Time:
    return _ruleLatentDOY(ts, doy)


@rule(predicate("isPOD"))
def ruleLatentPOD(ts: datetime, pod: Time) -> Time:
    # Set the time to the pre-defined POD values, but keep the POD
    # information. The date is chosen based on what ever is the next
    # possible slot for these times
    h_from, h_to = pod_hours[pod.POD]
    t_from = ts + relativedelta(hour=h_from, minute=0)
    if t_from >= ts:
        t_from -= relativedelta(days=1)
    return Time(year=t_from.year, month=t_from.month, day=t_from.day, POD=pod.POD)

#######################################################################################################

# Comment out rules for structured date formats that are not likely to be spoken./
"""
@rule(
    r"(?<!\d|\.)(?P<day>(?&_day))[\./\-]"
    r"((?P<month>(?&_month))|(?P<named_month>({})))\.?"
    r"(?!\d|am|\s*pm)".format(_rule_months)
)
# do not allow dd.ddam, dd.ddpm, but allow dd.dd am - e.g. in the German
# "13.06 am Nachmittag"
def ruleDDMM(ts: datetime, m: RegexMatch) -> Time:
    if m.match.group("month"):
        month = int(m.match.group("month"))
    else:
        for i, (name, _) in enumerate(_months):
            if m.match.group(name):
                month = i + 1
    return Time(month=month, day=int(m.match.group("day")))
"""

@rule(
    r"(?<!\d|\.)((?P<month>(?&_month))|(?P<named_month>({})))[/\-]"
    r"(?P<day>(?&_day))"
    r"(?!\d|am|\s*pm)".format(_rule_months)
)
def ruleMMDD(ts: datetime, m: RegexMatch) -> Time:
    if m.match.group("month"):
        month = int(m.match.group("month"))
    else:
        for i, (name, _) in enumerate(_months):
            if m.match.group(name):
                month = i + 1
    return Time(month=month, day=int(m.match.group("day")))


@rule(
    r"(?<!\d|\.)(?P<day>(?&_day))[-/\.]"
    r"((?P<month>(?&_month))|(?P<named_month>({})))[-/\.]"
    r"(?P<year>(?&_year))(?!\d)".format(_rule_months)
)
def ruleDDMMYYYY(ts: datetime, m: RegexMatch) -> Time:
    y = int(m.match.group("year"))
    if y < 100:
        y += 2000
    if m.match.group("month"):
        month = int(m.match.group("month"))
    else:
        for i, (name, _) in enumerate(_months):
            if m.match.group(name):
                month = i + 1
    return Time(year=y, month=month, day=int(m.match.group("day")))



def _is_valid_military_time(ts: datetime, t: Time) -> bool:
    if t.hour is None or t.minute is None:
        return False

    t_year = t.hour * 100 + t.minute
    # Military times (i.e. no separator) are notriously difficult to
    # distinguish from yyyy; these are some heuristics to avoid an abundance
    # of false positives for hhmm
    #
    # If hhmm is the current year -> assume it is a year
    if t_year == ts.year:
        return False
    # If hhmm is the year in 3 month from now -> same, prefer year
    if t_year == (ts + relativedelta(months=3)).year:
        return False
    # If the minutes is not a multiple of 5 prefer year.
    # Since military times are typically used for flights,
    # and flight times are only multiples of 5, we use this heuristic as evidence
    # for military times.
    if t.minute % 5:
        return False
    return True


def _maybe_apply_am_pm(t: Time, ampm_match: str) -> Time:

    if not t.hour:
        return t
    if ampm_match is None:
        t.meridiemLatent = True
        return t
    if ampm_match.lower().startswith("a") and t.hour <= 12:
        t.meridiemLatent = False
        return t
    if ampm_match.lower().startswith("p") and t.hour < 12:
        return Time(hour=t.hour + 12, minute=t.minute, meridiemLatent=False)
    # the case ampm_match.startswith('a') and t.hour >
    # 12 (e.g. 13:30am) makes no sense, lets ignore the ampm
    # likewise if hour >= 12 no 'pm' action is needed
    return t


@rule(
    # match hhmm
    r"(?<!\d|\.)(?P<hour>(?:[01]\d)|(?:2[0-3]))(?P<minute>(?&_minute))"
    r"\s*(?P<clock>uhr|h)?"  # optional uhr
    r"\s*(?P<ampm>\s*[ap]\.?m\.?)?(?!\d)"  # optional am/pm
)
def ruleHHMMmilitary(ts: datetime, m: RegexMatch) -> Optional[Time]:
    t = Time(hour=int(m.match.group("hour")), minute=int(m.match.group("minute") or 0))
    if m.match.group("clock") or _is_valid_military_time(ts, t):
        return _maybe_apply_am_pm(t, m.match.group("ampm"))
    return None


@rule(
    r"(?<!\d|\.)"  # We don't start matching with another number, or a dot
    r"(?P<hour>(?&_hour))"  # We certainly match an hour
    # We try to match also the minute
    r"((?P<sep>:|uhr|h|\.)(?P<minute>(?&_minute)))?"
    r"\s*(?P<clock>uhr|h)?"  # We match uhr with no minute
    r"(?P<ampm>\s*[ap]\.?m\.?)?"  # AM PM
    r"(?!\d)"
)
def ruleHHMM(ts: datetime, m: RegexMatch) -> Time:
    # hh [am|pm]
    # hh:mm
    # hhmm
    t = Time(hour=int(m.match.group("hour")), minute=int(m.match.group("minute") or 0))
    return _maybe_apply_am_pm(t, m.match.group("ampm"))


@rule(r"(?<!\d|\.)(?P<hour>(?&_hour))\s*(?:h|o\'?clock)")
def ruleHHOClock(ts: datetime, m: RegexMatch) -> Time:
    return Time(hour=int(m.match.group("hour")), meridiemLatent=True)


@rule(r"(?:a |one )?quarter(?: to| till| before| of)|vie?rtel vor", predicate("isTOD"))
def ruleQuarterBeforeHH(ts: datetime, _: RegexMatch, t: Time) -> Optional[Time]:
    # no quarter past hh:mm where mm is not 0 or missing
    if t.minute:
        return None
    if t.hour > 0:
        return Time(hour=t.hour - 1, minute=45, meridiemLatent=t.meridiemLatent)
    else:
        return Time(hour=23, minute=45, meridiemLatent=t.meridiemLatent)


@rule(r"(?:(?:a |one )?quarter(?: after| past)|vie?rtel nach)", predicate("isTOD"))
def ruleQuarterAfterHH(ts: datetime, _: RegexMatch, t: Time) -> Optional[Time]:
    if t.minute:
        return None
    return Time(hour=t.hour, minute=15, meridiemLatent=t.meridiemLatent)


@rule(r"halfe?(?: to| till| before| of)?|halb( vor)?", predicate("isTOD"))
def ruleHalfBeforeHH(ts: datetime, _: RegexMatch, t: Time) -> Optional[Time]:
    if t.minute:
        return None
    if t.hour > 0:
        return Time(hour=t.hour - 1, minute=30, meridiemLatent=t.meridiemLatent)
    else:
        return Time(hour=23, minute=30, meridiemLatent=t.meridiemLatent)


@rule(r"halfe?(?: after| past)|halb nach", predicate("isTOD"))
def ruleHalfAfterHH(ts: datetime, _: RegexMatch, t: Time) -> Optional[Time]:
    if t.minute:
        return None
    return Time(hour=t.hour, minute=30, meridiemLatent=t.meridiemLatent)


@rule(predicate("isTOD"), predicate("isPOD"))
def ruleTODPOD(ts: datetime, tod: Time, pod: Time) -> Optional[Time]:
    # time of day may only be an hour as in "3 in the afternoon"; this
    # is only relevant for time <= 12
    if tod.hour < 12 and (
        "afternoon" in pod.POD
        or "evening" in pod.POD
        or "night" in pod.POD
        or "last" in pod.POD
    ):
        h = tod.hour + 12
    elif tod.hour > 12 and (
        "forenoon" in pod.POD or "morning" in pod.POD or "first" in pod.POD
    ):
        # 17Uhr morgen -> do not merge
        return None
    else:
        h = tod.hour
    return Time(hour=h, minute=tod.minute)


@rule(predicate("isPOD"), predicate("isTOD"))
def rulePODTOD(ts: datetime, pod: Time, tod: Time) -> Optional[Time]:
    return cast(Time, ruleTODPOD(ts, tod, pod))


@rule(predicate("isDate"), predicate("isTOD"))
def ruleDateTOD(ts: datetime, date: Time, tod: Time) -> Time:
    return Time(
        year=date.year, month=date.month, day=date.day, hour=tod.hour, minute=tod.minute
    )


@rule(predicate("isTOD"), predicate("isDate"))
def ruleTODDate(ts: datetime, tod: Time, date: Time) -> Time:
    return Time(
        year=date.year, month=date.month, day=date.day, hour=tod.hour, minute=tod.minute
    )

@rule(predicate("isDate"), predicate("isPOD"))
def ruleDatePOD(ts: datetime, d: Time, pod: Time) -> Time:
    return Time(year=d.year, month=d.month, day=d.day, POD=pod.POD)


@rule(predicate("isPOD"), predicate("isDate"))
def rulePODDate(ts: datetime, pod: Time, d: Time) -> Time:
    return Time(year=d.year, month=d.month, day=d.day, POD=pod.POD)



@rule(dimension(Duration), r"ago|before")
def ruleDurationAgo(ts: datetime, dur: Duration, _: RegexMatch) -> Time:
    # Example:
    # 5 days ago
    # 3 weeks before
    delta = _duration_to_relativedelta(dur)
    time = ts - delta
    return Time(year = time.year, month = time.month, day=time.day, hour=time.hour, minute=time.minute)


@rule(predicate("isTimeInterval"), predicate("isDate"))
def ruleIntervalWithDateCue(ts: datetime, i: Interval, d: Time) -> Time:

    dt_from = datetime(year=d.year, month=d.month, day=d.day, hour=i.t_from.hour, minute=i.t_from.minute)
    dt_to = datetime(year=d.year, month=d.month, day=d.day, hour=i.t_to.hour, minute=i.t_to.minute)

    # Handle reversed interval
    if dt_from > dt_to:
        if i.t_from.isMeridiemLatent == True and i.t_from.hour > 12:
            dt_from -= relativedelta(hours=12)
        elif i.t_to.isMeridiemLatent == True and i.t_to.hour < 12:
            dt_to += relativedelta(hours=12)

    return Interval(
        t_from = Time( year=dt_from.year, month = dt_from.month, day=dt_from.day, hour=dt_from.hour, minute=dt_from.minute),
        t_to = Time( year=dt_to.year, month = dt_to.month, day=dt_to.day, hour=dt_to.hour, minute=dt_to.minute)
    )

#Durations########################################################################################################

_rule_digit_and = r"(?P<additional_digit>(?:(?P<n_int>\d+)|{})\s+and)".format(make_rule_named_number(1,10))

def _get_integer_from_match_digit_and(m: RegexMatch, fallback = 0)->Optional[int]:
    integer = 0
    if m.match.group("additional_digit"):
        if m.match.group("n_int"):
            integer = int(m.match.group("n_int"))
        else:
            integer = get_number_from_match(m)
        
    integer = integer if integer is not None else fallback
    return integer

_durations = [
    (DurationUnit.DAYS, r"days?"),
    (DurationUnit.MINUTES, r"m(?:inutes?)?"),
    (DurationUnit.HOURS, r"h(?:ours?)?"),
    (DurationUnit.WEEKS, r"weeks?"),
    (DurationUnit.MONTHS, r"months?"),
]


_rule_durations = r"|".join(
    r"(?P<d_{}>{}\b)".format(dur.value, expr) for dur, expr in _durations
)
_rule_durations = r"(?:{})\s*".format(_rule_durations)


# Rules regarding durations
@rule(r"(?P<num>\d+)\s+" + _rule_durations)
def ruleDigitDuration(ts: datetime, m: RegexMatch) -> Optional[Duration]:
    # 1 day etc.
    num = m.match.group("num")
    if num:
        for n, _, in _durations:
            unit = m.match.group("d_" + n.value)
            if unit:
                return Duration(int(num), n)

    return None


@rule(r"({})\s+".format(make_rule_named_number()) + _rule_durations)
def ruleNamedNumberDuration(ts: datetime, m: RegexMatch) -> Optional[Duration]:
    # one day, thirty days etc.
    num = get_number_from_match(m)

    if num:
        for d, _, in _durations:
            unit = m.match.group("d_" + d.value)
            if unit:
                return Duration(num, d)

    return None


@rule(dimension(Duration), dimension(Duration))
def ruleDurationDuration(ts: datetime, dur1: Duration, dur2: Duration) -> Optional[Duration]:
    if dur1.unit == DurationUnit.DAYS and (dur2.unit == DurationUnit.HOURS or dur2.unit == DurationUnit.MINUTES):
        if dur2.unit == DurationUnit.HOURS:
            return Duration(dur1.value * 24 + dur2.value, DurationUnit.HOURS)
        elif dur2.unit == DurationUnit.MINUTES:
            return Duration(dur1.value * 24 * 60 + dur2.value, DurationUnit.MINUTES)
        else: return None
    elif dur1.unit == DurationUnit.HOURS and dur2.unit == DurationUnit.MINUTES:
        return Duration(dur1.value * 60 + dur2.value, DurationUnit.MINUTES)

@rule(dimension(Duration), r"\band\b", dimension(Duration))
def ruleDurationAndDuration(ts: datetime, dur1: Duration, _: RegexMatch, dur2: Duration) -> Optional[Duration]:
   return ruleDurationDuration(ts, dur1, dur2)

@rule(dimension(Duration), r"\band\s+(?:a\s+)?half\b")
def ruleDurationAndHalf(ts: datetime, dur1: Duration, _: RegexMatch) -> Optional[Duration]:
    if dur1.unit == DurationUnit.HOURS:
        return Duration(dur1.value * 60 + 30, DurationUnit.MINUTES)
    elif dur1.unit == DurationUnit.DAYS:
        return Duration(dur1.value * 24 + 12, DurationUnit.HOURS)
    else:
        return None

_rule_duration_fractions = r"(?P<frac_digit>\d+)|"+ make_rule_named_number(1, 4, "frac_c_")

_rule_duration_fractions = r"(({})\s+)?".format(_rule_duration_fractions)

_fractions = [(4, r"quarters?"), (2, r"hal(?:f|ves)"), (3, r"1/3|thirds?")]
_rule_fractions = "|".join(r"(?P<frac1_{}>{})".format(n, r) for n, r in _fractions)

_rule_duration_fractions += r"({})\s+".format(_rule_fractions) + r"(?:of\s+)?(?:an?\s+)?" + r"(?:{})\b".format(r"|".join(
    r"(?P<d_{}>{}\b)".format(dur.value, expr) for dur, expr in _durations)
)

@rule(r"(?P<left>\d+)(?P<separator>\.|\/)(?P<right>\d+)\s+" + r"(?:of\s+)?(?:an?\s+)?" + _rule_durations)
def ruleRatialDuration(ts: datetime, m: RegexMatch) -> Optional[Duration]:
    separator = m.match.group("separator")

    if separator == ".":
        # 1.5 day, 1.5 hours etc.
        digit = m.match.group("left")
        decimal = m.match.group("right")

        if digit:
            for n, _, in _durations:
                unit = m.match.group("d_" + n.value)
                if unit:
                    if decimal:
                        if n.value == "hours":
                            return Duration(round(int(digit) * 60 + float("0." +decimal) * 60), DurationUnit.MINUTES, tag={"fraction": digit +"." + decimal})
                        elif n.value == "days":
                            return Duration(round(int(digit) * 24 + float("0." +decimal) * 24), DurationUnit.HOURS, tag={"fraction": digit +"." + decimal})
                    else:
                        return Duration(int(digit), n)
    elif separator == "/":
         # 1/2 day, 1/4 hours etc.

        numerator = m.match.group("left")
        denominator = m.match.group("right")

        if numerator and denominator:
            for n, _, in _durations:
                unit = m.match.group("d_" + n.value)
                if unit:
                    ratio = int(numerator) / int(denominator)
                    if n.value == "hours":
                        return Duration(round(ratio * 60), DurationUnit.MINUTES, {"fraction": ratio})
                    elif n.value == "days":
                        return Duration(round(ratio * 24), DurationUnit.HOURS, {"fraction": ratio})
               
    return None


@rule(r"({}\s+)?".format(_rule_digit_and) + _rule_duration_fractions)
def ruleDurationFromNamedFraction(ts: datetime, m: RegexMatch) -> Optional[Duration]:
    # half day, half hour, 3 quarters of day

    fraction = None


    #Find base fraction
    for n, _, in _fractions:
        if m.match.group("frac1_" + str(n)):
            fraction = 1/n
            break    
    
    if fraction is None:
        return None

    #Find fraction multiples
    if m.match.group("frac_digit"):
        digit = m.match.group("frac_digit")
        fraction *= int(digit)
    else:
        for n in range(1,4):
            if m.match.group("frac_c_" + str(n)):
                fraction *= n
                break

    integer = _get_integer_from_match_digit_and(m)

    #Find duration unit
    for n, _, in _durations:
        unit = m.match.group("d_" + n.value)
        if unit:
            if n.value == "hours":
                return Duration(round((integer + fraction) * 60), DurationUnit.MINUTES, tag={"fraction": fraction})
            elif n.value == "days":
                return Duration(round((integer + fraction) * 24), DurationUnit.HOURS, tag={"fraction": fraction})

    return None


#Intervals##########################################################################################

"""
@rule(
    r"((?P<not>not |nicht )?(vor|before))|(bis )?spätestens( bis)?|bis|latest",
    dimension(Time),
)
def ruleBeforeTime(ts: datetime, r: RegexMatch, t: Time) -> Interval:
    if r.match.group("not"):
        return Interval(t_from=t, t_to=None)
    else:
        return Interval(t_from=None, t_to=t)


@rule(
    r"((?P<not>not |nicht )?(nach|after))|(ab )?frühe?stens( ab)?|ab|"
    "(from )?earliest( after)?|from",
    dimension(Time),
)
def ruleAfterTime(ts: datetime, r: RegexMatch, t: Time) -> Interval:
    if r.match.group("not"):
        return Interval(t_from=None, t_to=t)
    else:
        return Interval(t_from=t, t_to=None)
"""

"""
@rule(predicate("isMonth"), r"(?P<from>[123]?\d)(?:st|nd|rd|th)?\s+(?:to|through|between)\s+(?P<to>[123]?\d)(?:st|nd|rd|th)?\b")
def ruleDOYToDigit(ts: datetime, d: Time, m: RegexMatch) -> Optional[Interval]:
    # August 5 to 16
    day_from = int(m.match.group("from"))
    day_to = int(m.match.group("from"))
    if day_from < 31 and day_to < 31 and day_from <= day_to:
        return Interval(t_from=Time(month=d.month, day=day_from), t_to=Time(month=d.month, day=day_to))
    else: return None
"""

@rule(predicate("isDate"), _regex_to_join, predicate("isDate"))
def ruleDateDate(ts: datetime, d1: Time, _: RegexMatch, d2: Time) -> Optional[Interval]:
    if d1.year > d2.year:
        return None
    if d1.year == d2.year and d1.month > d2.month:
        return None
    if d1.year == d2.year and d1.month == d2.month and d1.day >= d2.day:
        return None
    return Interval(t_from=d1, t_to=d2)


@rule(predicate("isDOM"), _regex_to_join, predicate("isDate"))
def ruleDOMDate(ts: datetime, d1: Time, _: RegexMatch, d2: Time) -> Optional[Interval]:
    if d1.day >= d2.day:
        return None
    return Interval(t_from=Time(year=d2.year, month=d2.month, day=d1.day), t_to=d2)


@rule(predicate("isDate"), _regex_to_join, predicate("isDOM"))
def ruleDateDOM(ts: datetime, d1: Time, _: RegexMatch, d2: Time) -> Optional[Interval]:
    #January 15 to 24
    if d1.day >= d2.day:
        return None
    return Interval(t_from=d1, t_to=Time(year=d1.year, month=d1.month, day=d2.day))


#Added by Young-Ho
@rule(dimension(Time), _regex_to_join + r"\s+(?P<to>[123]?\d)(?:st|nd|rd|th)?\b")
def ruleDateAndDigit(ts: datetime, d1: Time, m: RegexMatch) -> Optional[Interval]:
    #January 15 to 24
    if d1.hasTime == False:
        day_to = int(m.match.group("to"))
        if d1.day >= day_to:
            return None
        return Interval(t_from=d1, t_to=Time(year=d1.year, month=d1.month, day=day_to))
    return None


@rule(predicate("isDOY"), _regex_to_join, predicate("isDate"))
def ruleDOYDate(ts: datetime, d1: Time, _: RegexMatch, d2: Time) -> Optional[Interval]:
    if d1.month > d2.month:
        return None
    elif d1.month == d2.month and d1.day >= d2.day:
        return None

    d1_latent_resolved = _ruleLatentDOY(ts, d1)

    if d1_latent_resolved.year != d2.year:
        return Interval(t_from=Time(year=d1_latent_resolved.year, month=d1.month, day=d1.day), t_to=Time(year=d1_latent_resolved.year, month=d2.month, day=d2.day))
    
    return Interval(t_from=Time(year=d2.year, month=d1.month, day=d1.day), t_to=d2)


@rule(predicate("isDateTime"), _regex_to_join, predicate("isDateTime"))
def ruleDateTimeDateTime(
    ts: datetime, d1: Time, _: RegexMatch, d2: Time
) -> Optional[Interval]:
    if d1.year > d2.year:
        return None
    if d1.year == d2.year and d1.month > d2.month:
        return None
    if d1.year == d2.year and d1.month == d2.month and d1.day > d2.day:
        return None
    if (
        d1.year == d2.year
        and d1.month == d2.month
        and d1.day == d2.day
        and d1.hour > d2.hour
    ):
        return None
    if (
        d1.year == d2.year
        and d1.month == d2.month
        and d1.day == d2.day
        and d1.hour == d2.hour
        and d1.minute >= d2.minute
    ):
        return None
    return Interval(t_from=d1, t_to=d2)


@rule(predicate("isTOD"), _regex_to_join, predicate("isTOD"))
def ruleTODTOD(ts: datetime, t1: Time, _: RegexMatch, t2: Time) -> Interval:
    return Interval(t_from=t1, t_to=t2)


@rule(predicate("isPOD"), _regex_to_join, predicate("isPOD"))
def rulePODPOD(ts: datetime, t1: Time, _: RegexMatch, t2: Time) -> Interval:
    return Interval(t_from=t1, t_to=t2)

@rule(predicate("isDate"), dimension(Interval))
def ruleDateInterval(ts: datetime, d: Time, i: Interval) -> Optional[Interval]:
    if not (
        (i.t_from is None or i.t_from.isTOD or i.t_from.isPOD)
        and (i.t_to is None or i.t_to.isTOD or i.t_to.isPOD)
    ):
        return None
    t_from = t_to = None
    if i.t_from is not None:
        t_from = Time(
            year=d.year,
            month=d.month,
            day=d.day,
            hour=i.t_from.hour,
            minute=i.t_from.minute,
            POD=i.t_from.POD,
        )
    if i.t_to is not None:
        t_to = Time(
            year=d.year,
            month=d.month,
            day=d.day,
            hour=i.t_to.hour,
            minute=i.t_to.minute,
            POD=i.t_to.POD,
        )
    # This is for wrapping time around a date.
    # Mon, Nov 13 11:30 PM - 3:35 AM
    if t_from and t_to and t_from.dt >= t_to.dt:
        t_to_dt = t_to.dt + relativedelta(days=1)
        t_to = Time(
            year=t_to_dt.year,
            month=t_to_dt.month,
            day=t_to_dt.day,
            hour=t_to_dt.hour,
            minute=t_to_dt.minute,
            POD=t_to.POD,
        )
    return Interval(t_from=t_from, t_to=t_to)


@rule(predicate("isPOD"), dimension(Interval))
def rulePODInterval(ts: datetime, p: Time, i: Interval) -> Optional[Interval]:
    def _adjust_h(t: Time) -> Optional[int]:
        if t.hour is None:
            return None
        if t.hour < 12 and (
            "afternoon" in p.POD
            or "evening" in p.POD
            or "night" in p.POD
            or "last" in p.POD
        ):
            return t.hour + 12
        else:
            return t.hour

    # only makes sense if i is a time interval
    if not (
        (i.t_from is None or i.t_from.hasTime) and (i.t_to is None or i.t_to.hasTime)
    ):
        return None
    t_to = t_from = None
    if i.t_to is not None:
        t_to = Time(
            year=i.t_to.year,
            month=i.t_to.month,
            day=i.t_to.day,
            hour=_adjust_h(i.t_to),
            minute=i.t_to.minute,
            DOW=i.t_to.DOW,
        )
    if i.t_from is not None:
        t_from = Time(
            year=i.t_from.year,
            month=i.t_from.month,
            day=i.t_from.day,
            hour=_adjust_h(i.t_from),
            minute=i.t_from.minute,
            DOW=i.t_from.DOW,
        )
    return Interval(t_from=t_from, t_to=t_to)


#appended interval rules######################

#only elapsed duration
@rule(r"\bfor\b", dimension(Duration))
def ruleElapsedDuration(ts: datetime, _: RegexMatch, dur: Duration) -> Interval:
    delta = _duration_to_relativedelta(dur)
    start_ts = ts - delta
    start = Time(year=start_ts.year, month=start_ts.month, day=start_ts.day, hour=start_ts.hour, minute=start_ts.minute)
    return Interval(t_from=start, t_to=Time(year=ts.year, month=ts.month, day=ts.day, hour=ts.hour, minute=ts.minute))

#time + duration
@rule(dimension(Time), r"\bfor\b", dimension(Duration))
def ruleTimeDurationTime(ts: datetime, t: Time, _: RegexMatch, dur: Duration) -> Interval:
    delta = _duration_to_relativedelta(dur)
    
    end = None
    if t.isDateTime:
        end_ts = t.dt + delta
        end = Time(year=end_ts.year, month=end_ts.month, day=end_ts.day, hour=end_ts.hour, minute=end_ts.minute)
    else:
        #Latent time
        end_ts = _latent_tod(ts, t).dt + delta
        if t.isDate:
            end = Time(year=end_ts.year, month=end_ts.month, day=end_ts.day)
        elif t.isTOD:
            end = Time(year=t.year, month=t.month, day=t.day, hour=end_ts.hour, minute=end_ts.minute)
        
    return Interval(t_from=t, t_to=end)
"""
@rule(predicate("hasDate"), r"\bfor\b", dimension(Duration))
def ruleTimeDuration(
    ts: datetime, t: Time, _: RegexMatch, dur: Duration
) -> Optional[Interval]:
    # Examples:
    # on the 27th for one day
    # heute eine Übernachtung

    # To make an interval we should at least have a date
    if dur.unit in (
        DurationUnit.DAYS,
        DurationUnit.WEEKS,
        DurationUnit.MONTHS,
    ):
        delta = _duration_to_relativedelta(dur)
        end_ts = t.dt + delta
        # We the end of the interval is a date without particular times
        end = Time(year=end_ts.year, month=end_ts.month, day=end_ts.day)
        return Interval(t_from=t, t_to=end)

    if dur.unit in (DurationUnit.HOURS, DurationUnit.MINUTES):
        delta = _duration_to_relativedelta(dur)
        end_ts = t.dt + delta
        end = Time(
            year=end_ts.year,
            month=end_ts.month,
            day=end_ts.day,
            hour=end_ts.hour,
            minute=end_ts.minute,
        )
        return Interval(t_from=t, t_to=end)
    return None
"""

def _duration_to_relativedelta(dur: Duration) -> relativedelta:
    return {
        DurationUnit.DAYS: relativedelta(days=dur.value),
        DurationUnit.WEEKS: relativedelta(weeks=dur.value),
        DurationUnit.MONTHS: relativedelta(months=dur.value),
        DurationUnit.HOURS: relativedelta(hours=dur.value),
        DurationUnit.MINUTES: relativedelta(minutes=dur.value),
    }[dur.unit]
