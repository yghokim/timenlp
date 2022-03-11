"""Those rules are applied as postprocessing steps after scoring has been already
done. Needed for backwards compatibility."""
from timenlp.types import Artifact, Interval, Time
from datetime import datetime
from dateutil.relativedelta import relativedelta

#Young-Ho: These methods are modified to support past anchoring of latent time, which is an opposite way of the original ctparse.

def apply_postprocessing_rules(ts: datetime, art: Artifact) -> Artifact:
    """Apply postprocessing rules to a resolution *art*. This is
    introduced for backwards compatibility reasons.

    Example:

    8:00 pm, ts=2020.01.01 07:00

    produces a resolution:

    X-X-X 20:00

    after postprocessing this is anchored to the reference time:

    2020-01-01 20:00
    """
    if isinstance(art, Time):
        if art.isTOD:
            return _latent_tod(ts, art)
            
    if isinstance(art, Interval):
        if art.isTimeInterval:
            return _latent_time_interval(ts, art)

    return art

def _latent_tod(ts: datetime, tod: Time) -> Time:
    dm = ts + relativedelta(hour=tod.hour, minute=tod.minute or 0)
    if dm > ts:
        if tod.isMeridiemLatent:
            dm -= relativedelta(hours=12)
        else:
            dm -= relativedelta(days=1)
    
    #pull AM time to nearest hour. e.g., "10" called at 11:30 implies 10 PM rather than 10 AM.
    if tod.isMeridiemLatent and ts.hour >= 12 and tod.hour < 12:
        next_meridiem = dm + relativedelta(hours=12)
        if next_meridiem < ts:
            dm = next_meridiem
    
    #if dm <= ts:
    #    dm += relativedelta(days=1)
    
    return Time(
        year=dm.year, month=dm.month, day=dm.day, hour=dm.hour, minute=dm.minute
    )

FUTURE_TOLERANCE_DELTA = relativedelta(minutes = 10)

def _latent_time_interval(ts: datetime, ti: Interval) -> Interval:

    print("latent time interval convert", ti.t_from, ti.t_from.isMeridiemLatent, ti.t_to, ti.t_to.isMeridiemLatent)
    
    assert ti.t_from and ti.t_to  # guaranteed by the caller
    dm_from = ts + relativedelta(hour=ti.t_from.hour, minute=ti.t_from.minute or 0) if ti.t_from.isTOD == False else _latent_tod(ts, ti.t_from).to_datetime_unsafe()
    dm_to = ts + relativedelta(hour=ti.t_to.hour, minute=ti.t_to.minute or 0) if ti.t_to.isTOD == False else _latent_tod(ts, ti.t_to).to_datetime_unsafe()
 
    #First, fix a mismatch between the start and end time.
    if dm_to < dm_from:
        if ti.t_to.hasDate == False:
            if ti.t_to.isTOD:
                if ti.t_to.hour < 12 and ti.t_to.isMeridiemLatent:
                    dm_to += relativedelta(hours=12)
                else:
                    dm_to += relativedelta(days=1)
        elif ti.t_from.hasDate == False:
            if ti.t_from.isTOD:
                if ti.t_from.hour >= 12 and ti.t_from.isMeridiemLatent:
                    dm_from -= relativedelta(hours=12)
                else:
                    dm_from -= relativedelta(days=1)
    
    # fix future interval with latent dates
    if dm_to - FUTURE_TOLERANCE_DELTA > ts and ti.t_from.hasDate == False and ti.t_to.hasDate == False:
        while dm_to - FUTURE_TOLERANCE_DELTA > ts:
            if ti.t_from.isMeridiemLatent and ti.t_to.isMeridiemLatent:
                dm_from -= relativedelta(hours=12)
                dm_to -= relativedelta(hours=12)
            else:
                dm_from -= relativedelta(days=1)
                dm_to -= relativedelta(days=1)

    return Interval(
        t_from=Time(
            year=dm_from.year,
            month=dm_from.month,
            day=dm_from.day,
            hour=dm_from.hour,
            minute=dm_from.minute,
        ),
        t_to=Time(
            year=dm_to.year,
            month=dm_to.month,
            day=dm_to.day,
            hour=dm_to.hour,
            minute=dm_to.minute,
        ),
    )


#Original##################################################################################################

def old_latent_tod(ts: datetime, tod: Time) -> Time:
    dm = ts + relativedelta(hour=tod.hour, minute=tod.minute or 0)
    if dm <= ts:
        dm += relativedelta(days=1)
    return Time(
        year=dm.year, month=dm.month, day=dm.day, hour=dm.hour, minute=dm.minute
    )


def old_latent_time_interval(ts: datetime, ti: Interval) -> Interval:
    assert ti.t_from and ti.t_to  # guaranteed by the caller
    dm_from = ts + relativedelta(hour=ti.t_from.hour, minute=ti.t_from.minute or 0)
    dm_to = ts + relativedelta(hour=ti.t_to.hour, minute=ti.t_to.minute or 0)
    if dm_from <= ts:
        dm_from += relativedelta(days=1)
        dm_to += relativedelta(days=1)
    return Interval(
        t_from=Time(
            year=dm_from.year,
            month=dm_from.month,
            day=dm_from.day,
            hour=dm_from.hour,
            minute=dm_from.minute,
        ),
        t_to=Time(
            year=dm_to.year,
            month=dm_to.month,
            day=dm_to.day,
            hour=dm_to.hour,
            minute=dm_to.minute,
        ),
    )
