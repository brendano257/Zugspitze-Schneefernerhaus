import datetime as dt
from datetime import datetime

from dateutil import relativedelta


def create_daily_ticks(days_in_plot, minors_per_day=4, end_date=datetime.now()):
    """
    Takes a number of days to plot back, and creates major (1 day) and minor (6 hour) ticks by default.

    :param int days_in_plot: number of days to be displayed on the plot
    :param int minors_per_day: number of minor ticks per day
    :param datetime end_date: the final day that will be on the plot, defaults to today
    :return tuple: date_limits, major_ticks, minor_ticks
    """

    date_limits = dict()
    date_limits['right'] = end_date.replace(hour=0, minute=0, second=0, microsecond=0) + dt.timedelta(
        days=1)  # end of day
    date_limits['left'] = date_limits['right'] - dt.timedelta(days=days_in_plot)

    major_ticks = [date_limits['right'] - dt.timedelta(days=x) for x in range(0, days_in_plot + 1)]

    minor_ticks = [date_limits['right'] - dt.timedelta(hours=x * (24 / minors_per_day))
                   for x in range(0, days_in_plot * minors_per_day + 1)]

    return date_limits, major_ticks, minor_ticks


def create_monthly_ticks(months_to_plot, minors_per_month=4, start=None):
    """
    Creates ticks for months, then minor ticks for each whole week (restarting each month) by default.

    Alternatively, specifying a start date will create ticks for the given start date through start_date+months_to_plot.

    TODO: Still definitely a better way, probably using timedelta_per_minor or something to create minor ticks.

    :param int months_to_plot: number of months to be displayed on the plot
    :param int minors_per_month: number of minor ticks per month
    :param datetime start: optional datetime to start making ticks from
        if not given, defaults to start=datetime.now() and end=start-months_to_plot
    :return tuple: date_limits, major_ticks, minor_ticks
    """
    date_limits = {}

    if not start:
        end = (datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
               + relativedelta(months=1))
        start = end - relativedelta(months=months_to_plot)
    else:
        end = start + relativedelta(months=months_to_plot)

    date_limits['right'] = end
    date_limits['left'] = start

    major_ticks = sorted([date_limits['right'] - relativedelta(months=x) for x in range(0, months_to_plot + 1)])

    # determine how many days each minor tick should be, excepting the case where minors_per_month == 0
    # because the month length isn't known ahead of time, always assume it's 31 days and account for it later[***]
    minor_step = 31 // minors_per_month if minors_per_month else None

    minor_ticks = []
    if minor_step:  # if any minor ticks need to be created
        for tick in major_ticks:
            # for every major tick, create minors_per_month+1 minor ticks (the extra minor will sit on the major tick)
            for step in range(1, minors_per_month + 1):
                # create new tick by adding the current tick number within this major, multiplied by the minor_step
                new_tick = tick + dt.timedelta(days=step*minor_step)
                if new_tick.month <= tick.month:  # [***] if assuming the month was 31 days caused overflow, ignore it
                    minor_ticks.append(new_tick)

    return date_limits, major_ticks, minor_ticks
