import datetime as dt
from datetime import datetime

from dateutil.relativedelta import relativedelta

__all__ = ['create_daily_ticks', 'create_monthly_ticks']


def create_daily_ticks(days_in_plot, minors_per_day=4, end_date=None):
    """
    Takes a number of days to plot back, and creates major (1 day) and minor (6 hour) ticks by default.

    :param int days_in_plot: number of days to be displayed on the plot
    :param int minors_per_day: number of minor ticks per day
    :param datetime end_date: the final day that will be on the plot, defaults to today
    :return tuple: (date_limits, major_ticks, minor_ticks)
    """

    if not end_date:
        end_date = datetime.now()

    date_limits = dict()
    date_limits['right'] = end_date.replace(hour=0, minute=0, second=0, microsecond=0) + dt.timedelta(
        days=1)  # end of day
    date_limits['left'] = date_limits['right'] - dt.timedelta(days=days_in_plot)

    major_ticks = [date_limits['right'] - dt.timedelta(days=x) for x in range(0, days_in_plot + 1)]

    minor_ticks = [date_limits['right'] - dt.timedelta(hours=x * (24 / minors_per_day))
                   for x in range(0, days_in_plot * minors_per_day + 1)]

    return date_limits, major_ticks, minor_ticks


def create_monthly_ticks(months_to_plot, days_per_minor=7, start=None):
    """
    Creates ticks for months, then minor ticks for each whole week (restarting each month) by default.

    Alternatively, specifying a start date will create ticks for the given start date through start_date+months_to_plot.

    :param int months_to_plot: number of months to be displayed on the plot
    :param int days_per_minor: number of days per minor tick, a falsy value will result in no minor ticks
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

    minor_ticks = []
    major_ticks = sorted([date_limits['right'] - relativedelta(months=x) for x in range(0, months_to_plot + 1)])

    if days_per_minor:
        # get maximum number of minor ticks possible in a month, given days_per_minor
        max_possible_minors = 31 // days_per_minor

        for major in major_ticks:
            for step in range(1, max_possible_minors + 1):
                minor = major + relativedelta(days=days_per_minor * step)
                if minor < major + relativedelta(months=1):
                    minor_ticks.append(minor)

    return date_limits, major_ticks, minor_ticks
