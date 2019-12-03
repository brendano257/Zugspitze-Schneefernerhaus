import json

from IO import connect_to_db, add_or_ignore_plot
from settings import CORE_DIR, DB_NAME, BOULDAIR_BASE_PATH, DAILY_PLOT_DIR, MR_PLOT_DIR, FULL_PLOT_DIR, JSON_PUBLIC_DIR
from settings import LOG_PLOT_DIR, PA_PLOT_DIR, STD_PA_PLOT_DIR
from processing.constants import LOG_ATTRS, DAILY_ATTRS, ALL_COMPOUNDS
from IO.db.models import OldData, Daily, Compound, LogFile, Integration, GcRun, Standard, Quantification
from IO.db import FileToUpload, TempDir
from plotting.utils import create_monthly_ticks, create_daily_ticks
from plotting.plots import zugspitze_mixing_plot, zugspitze_parameter_plot, zugspitze_twoaxis_parameter_plot
from plotting.plots import zugspitze_pa_plot

from reporting import abstract_query
from plotting.plots import MixingRatioPlot, PeakAreaPlot, LogParameterPlot, TwoAxisLogParameterPlot

__all__ = ['plot_new_data', 'plot_history', 'plot_logdata', 'plot_dailydata', 'plot_standard_and_ambient_peak_areas']

ambient_filters = [
    GcRun.type == 5,
    Compound.filtered == False,
]


def plot_new_data(logger):
    """
    Plots mixing ratio data, creating plot files and queueing the files for upload.

    This will plot data, regardless of if there's any new data since it's not run continously.

    :param logger: logging logger to record to
    :return: bool, True if ran corrected, False if exit on error
    """
    logger.info('Running plot_new_data()')
    try:
        engine, session = connect_to_db(DB_NAME, CORE_DIR)
    except Exception as e:
        logger.error(f'Error {e.args} prevented connecting to the database in plot_new_data()')
        return False

    remotedir = BOULDAIR_BASE_PATH + '/MR_plots'

    compounds_to_plot = (session.query(Quantification.name)
                         .join(Standard, Quantification.standard_id == Standard.id)
                         .filter(Standard.name == 'quantlist').all())
    compounds_to_plot[:] = [q.name for q in compounds_to_plot]

    date_limits, major_ticks, minor_ticks = create_monthly_ticks(6, days_per_minor=7)

    with open(JSON_PUBLIC_DIR / 'zug_plot_info.json', 'r') as file:
        compound_limits = json.loads(file.read())

    for name in compounds_to_plot:
        params = (GcRun.date, Compound.mr)
        filters = (
            Compound.name == name,
            GcRun.date >= date_limits['left'],
            *ambient_filters
        )

        results = abstract_query(params, filters, GcRun.date)

        dates = [r.date for r in results]
        mrs = [r.mr for r in results]

        p = MixingRatioPlot(
            {name: (dates, mrs)},
            limits={**date_limits, **compound_limits[name]},
            major_ticks=major_ticks,
            minor_ticks=minor_ticks,
            filepath=MR_PLOT_DIR / f'{name}_plot.png'
        )

        p.plot()

        file_to_upload = FileToUpload(p.filepath, remotedir, staged=True)
        add_or_ignore_plot(file_to_upload, session)

    session.commit()
    session.close()
    engine.dispose()

    return True


def plot_history(logger):
    """
    Plot longterm plots containing data from 2013 onward.

    Queries the database to get all OldData as well as newer data processed by this system and plots them together.

    If OldData exists for a compound, it is combined with newer data and plotted from 2013 to the most recent data. One
    set of plots with a zeroed axis is created to show scale, as well as one with more appropriate bounds for viewing.

    :param logger: logging logger to record to
    :return: bool, True if ran correctly, False if exit on error
    """
    logger.info('Running plot_history()')

    try:
        engine, session = connect_to_db(DB_NAME, CORE_DIR)
    except Exception as e:
        logger.error(f'Error {e.args} prevented connecting to the database in plot_history()')
        return False

    remotedir = BOULDAIR_BASE_PATH + '/full_plots'

    compounds_to_plot = (session.query(Quantification.name)
                         .join(Standard, Quantification.standard_id == Standard.id)
                         .filter(Standard.name == 'quantlist').all())
    compounds_to_plot[:] = [q.name for q in compounds_to_plot]

    date_limits, major_ticks, minor_ticks = create_monthly_ticks(84, days_per_minor=0)

    major_ticks = major_ticks[::6]

    with open(JSON_PUBLIC_DIR / 'zug_long_plot_info.json', 'r') as file:
        compound_limits = json.loads(file.read())

    for name in compounds_to_plot:

        old_results = (session.query(OldData.date, OldData.mr)
                       .filter(OldData.name == name)
                       .order_by(OldData.date)
                       .all())

        params = (GcRun.date, Compound.mr)
        filters = (
            Compound.name == name,
            GcRun.date >= date_limits['left'],
            *ambient_filters
        )

        new_results = abstract_query(params, filters, GcRun.date)

        dates = [o.date for o in old_results] + [n.date for n in new_results]
        mrs = [o.mr for o in old_results] + [n.mr for n in new_results]

        limits = {**date_limits, **compound_limits[name]}

        # Create full plot w/ limits from file.
        fullplot = MixingRatioPlot(
            {name: (dates, mrs)},
            limits=limits,
            major_ticks=major_ticks,
            minor_ticks=minor_ticks,
            filepath=FULL_PLOT_DIR / f'{name}_plot.png'
        )

        fullplot.plot()

        file_to_upload = FileToUpload(fullplot.filepath, remotedir, staged=True)
        add_or_ignore_plot(file_to_upload, session)

        limits['bottom'] = 0

        # Create full plot w/ 0 limit for the bottom and top limit from file.
        fullplot_zeroed = MixingRatioPlot(
            {name: (dates, mrs)},
            limits=limits,
            major_ticks=major_ticks,
            minor_ticks=minor_ticks,
            filepath=FULL_PLOT_DIR / f'{name}_plot_zeroed.png'
        )

        fullplot_zeroed.plot()

        file_to_upload = FileToUpload(fullplot_zeroed.filepath, remotedir, staged=True)
        add_or_ignore_plot(file_to_upload, session)

    session.commit()
    session.close()
    engine.dispose()

    return True


def plot_logdata(logger):
    """
    Plots data from the LabView logs as stored in LogFile objects.

    Creates one set of plots of parameters logged by LabView with each run. Files are queued to upload the next time a
    call to upload any files is made.

    :param logger: logging logger to record to
    :return: bool, True if ran correctly, False if exit on error
    """
    logger.info('Running plot_logdata()')

    try:
        engine, session = connect_to_db(DB_NAME, CORE_DIR)
    except Exception as e:
        logger.error(f'Error {e.args} prevented connecting to the database in plot_logdata()')
        return False

    remotedir = BOULDAIR_BASE_PATH + '/logplots'

    date_limits, major_ticks, minor_ticks = create_daily_ticks(14, minors_per_day=2)
    major_ticks[:] = [major for num, major in enumerate(major_ticks) if not num % 2]  # utilize only 1/2 of the majors

    logs = session.query(LogFile).filter(LogFile.date >= date_limits.get('left')).all()

    logdict = {}
    for param in LOG_ATTRS:
        logdict[param] = [getattr(l, param) for l in logs]

    dates = [l.date for l in logs]

    all_plots = []

    sample_pressure_plot = LogParameterPlot(
        {'Sample Pressure Start': (dates, logdict.get('sample_p_start')),
         'Sample Flow (V)': (dates, logdict.get('sample_flow_act'))},
        title='Zugspitze Sample Pressures',
        filepath=LOG_PLOT_DIR / 'log_sample_pressure_flow.png',
        limits={**date_limits, 'bottom': 0, 'top': 4},
        y_label_str='',
        major_ticks=major_ticks,
        minor_ticks=minor_ticks
    )

    sample_pressure_plot.plot()
    all_plots.append(sample_pressure_plot)

    sample_pressure_during_plot = LogParameterPlot(
        {'Sample Pressure During': (dates, logdict.get('sample_p_during'))},
        title='Zugspitze Sample Pressure During Run',
        filepath=LOG_PLOT_DIR / 'log_sample_pressure_during.png',
        limits={**date_limits, 'bottom': 4, 'top': 12},
        y_label_str='Pressure (psi)',
        major_ticks=major_ticks,
        minor_ticks=minor_ticks
    )

    sample_pressure_during_plot.plot()
    all_plots.append(sample_pressure_during_plot)

    gchead_pressures_plot = LogParameterPlot(
        {'GC HeadP Start': (dates, logdict.get('gcheadp_start')),
         'GC HeadP During': (dates, logdict.get('gcheadp_during'))},
        title='Zugspitze GC Head Pressures',
        filepath=LOG_PLOT_DIR / 'log_gcheadp_pressures.png',
        limits={**date_limits},
        y_label_str='Pressure (psi)',
        major_ticks=major_ticks,
        minor_ticks=minor_ticks
    )

    gchead_pressures_plot.plot()
    all_plots.append(gchead_pressures_plot)

    active_wat_ads_traps_plot = LogParameterPlot(
        {'WT @ Sample Start': (dates, logdict.get('wt_sample_start')),
         'WT @ Sample End': (dates, logdict.get('wt_sample_end')),
         'Ads A @ Sample Start': (dates, logdict.get('ads_a_sample_start')),
         'Ads A @ Sample End': (dates, logdict.get('ads_a_sample_end'))},
        title='Zugspitze Active Ads and Water Trap Temperatures',
        filepath=LOG_PLOT_DIR / 'log_wat_ads_active_traptemps.png',
        limits={**date_limits, 'bottom': -55, 'top': -30},
        major_ticks=major_ticks,
        minor_ticks=minor_ticks
    )

    active_wat_ads_traps_plot.plot()
    all_plots.append(active_wat_ads_traps_plot)

    inactive_wat_ads_traps_plot = LogParameterPlot(
        {'Ads B @ Sample Start': (dates, logdict.get('ads_b_sample_start')),
         'Ads B @ Sample End': (dates, logdict.get('ads_b_sample_end'))},
        title='Zugspitze Inactive Ads Trap Temperatures',
        filepath=LOG_PLOT_DIR / 'log_ads_inactive_traptemps.png',
        limits={**date_limits, 'bottom': 15, 'top': 35},
        major_ticks=major_ticks,
        minor_ticks=minor_ticks
    )

    inactive_wat_ads_traps_plot.plot()
    all_plots.append(inactive_wat_ads_traps_plot)

    traps_temps_plot = LogParameterPlot(
        {'Trap @ FH': (dates, logdict.get('trap_temp_fh')),
         'Trap @ Inject': (dates, logdict.get('trap_temp_inject')),
         'Trap @ Bakeout': (dates, logdict.get('trap_temp_bakeout'))},
        title='Zugspitze Trap Temperatures',
        filepath=LOG_PLOT_DIR / 'log_trap_temps.png',
        limits={**date_limits},
        major_ticks=major_ticks,
        minor_ticks=minor_ticks
    )

    traps_temps_plot.plot()
    all_plots.append(traps_temps_plot)

    battery_voltages_plot = LogParameterPlot(
        {'BattV @ Inject': (dates, logdict.get('battv_inject')),
         'BattV @ Bakeout': (dates, logdict.get('battv_bakeout'))},
        title='Zugspitze Battery Voltages',
        filepath=LOG_PLOT_DIR / 'log_battery_voltages.png',
        limits={**date_limits, 'bottom': 8, 'top': 14},
        y_label_str='Voltage (V)',
        major_ticks=major_ticks,
        minor_ticks=minor_ticks
    )

    battery_voltages_plot.plot()
    all_plots.append(battery_voltages_plot)

    gc_start_wt_temps_plot = LogParameterPlot(
        {'GC Start Temp': (dates, logdict.get('gc_start_temp')),
         'WT Hot Temp': (dates, logdict.get('wt_hot_temp'))},
        title='Zugspitze GC Start and WT Hot Temps',
        filepath=LOG_PLOT_DIR / 'log_gc_start_wthot_temps.png',
        limits={**date_limits, 'bottom': 0, 'top': 75},
        major_ticks=major_ticks,
        minor_ticks=minor_ticks
    )

    gc_start_wt_temps_plot.plot()
    all_plots.append(gc_start_wt_temps_plot)

    heat_outs_plot = LogParameterPlot(
        {'HeatOut @ FH': (dates, logdict.get('trapheatout_flashheat')),
         'HeatOut @ Inject': (dates, logdict.get('trapheatout_inject')),
         'HeatOut @ Bakeout': (dates, logdict.get('trapheatout_bakeout'))},
        title='Zugspitze Heat Outputs',
        filepath=LOG_PLOT_DIR / 'log_heat_outs.png',
        limits={**date_limits},
        major_ticks=major_ticks,
        minor_ticks=minor_ticks
    )

    heat_outs_plot.plot()
    all_plots.append(heat_outs_plot)

    oven_mfc_ramp_plot = TwoAxisLogParameterPlot(
        {'GC Oven Temp': (dates, logdict.get('gc_oven_temp'))},
        {'MFC1 Ramp': (dates, logdict.get('mfc1_ramp'))},
        title='Zugspitze Oven Temperature and MFC1 Ramp',
        filepath=LOG_PLOT_DIR / 'log_oven_mfc_ramp.png',
        limits_y1={'right': date_limits.get('right'),
                   'left': date_limits.get('left'),
                   'bottom': 180,
                   'top': 230},
        limits_y2={'bottom': .65,
                 'top': .85},
        major_ticks=major_ticks,
        minor_ticks=minor_ticks,
        y2_label_str='MFC1 Ramp',
        color_set_y2=('orange',)
    )

    oven_mfc_ramp_plot.plot()
    all_plots.append(oven_mfc_ramp_plot)

    for plot in all_plots:
        file_to_upload = FileToUpload(plot.filepath, remotedir, staged=True)
        add_or_ignore_plot(file_to_upload, session)


    # with TempDir(LOG_PLOT_DIR):
        # name = 'log_sample_pressure_flow.png'
        # zugspitze_parameter_plot(dates,
        #                          ({'Sample Pressure Start': [None, logdict.get('sample_p_start')],
        #                            'Sample Flow (V)': [None, logdict.get('sample_flow_act')]}),
        #                          'Zugspitze Sample Pressures',
        #                          name,
        #                          limits={'right': date_limits.get('right'),
        #                                  'left': date_limits.get('left'),
        #                                  'bottom': 0,
        #                                  'top': 4},
        #                          y_label_str='',
        #                          major_ticks=major_ticks,
        #                          minor_ticks=minor_ticks)
        #
        # file_to_upload = FileToUpload(LOG_PLOT_DIR / name, remotedir, staged=True)
        # add_or_ignore_plot(file_to_upload, session)

        # name = 'log_sample_pressure_during.png'
        # zugspitze_parameter_plot(dates,
        #                          {'Sample Pressure During': [None, logdict.get('sample_p_during')]},
        #                          'Zugspitze Sample Pressure During Run',
        #                          name,
        #                          limits={'right': date_limits.get('right'),
        #                                  'left': date_limits.get('left'),
        #                                  'bottom': 4,
        #                                  'top': 12},
        #                          y_label_str='Pressure (psi)',
        #                          major_ticks=major_ticks,
        #                          minor_ticks=minor_ticks)
        #
        # file_to_upload = FileToUpload(LOG_PLOT_DIR / name, remotedir, staged=True)
        # add_or_ignore_plot(file_to_upload, session)

        # name = 'log_gcheadp_pressures.png'
        # zugspitze_parameter_plot(dates,
        #                          {'GC HeadP Start': [None, logdict.get('gcheadp_start')],
        #                           'GC HeadP During': [None, logdict.get('gcheadp_during')]},
        #                          'Zugspitze GC Head Pressures',
        #                          name,
        #                          limits={'right': date_limits.get('right'),
        #                                  'left': date_limits.get('left'),
        #                                  'bottom': None,
        #                                  'top': None},
        #                          y_label_str='Pressure (psi)',
        #                          major_ticks=major_ticks,
        #                          minor_ticks=minor_ticks)
        #
        # file_to_upload = FileToUpload(LOG_PLOT_DIR / name, remotedir, staged=True)
        # add_or_ignore_plot(file_to_upload, session)

        # name = 'log_wat_ads_active_traptemps.png'
        # zugspitze_parameter_plot(dates,
        #                          {'WT @ Sample Start': [None, logdict.get('wt_sample_start')],
        #                           'WT @ Sample End': [None, logdict.get('wt_sample_end')],
        #                           'Ads A @ Sample Start': [None, logdict.get('ads_a_sample_start')],
        #                           'Ads A @ Sample End': [None, logdict.get('ads_a_sample_end')]},
        #                          'Zugspitze Active Ads and Water Trap Temperatures',
        #                          name,
        #                          limits={'right': date_limits.get('right'),
        #                                  'left': date_limits.get('left'),
        #                                  'bottom': -55,
        #                                  'top': -30},
        #                          major_ticks=major_ticks,
        #                          minor_ticks=minor_ticks)
        #
        # file_to_upload = FileToUpload(LOG_PLOT_DIR / name, remotedir, staged=True)
        # add_or_ignore_plot(file_to_upload, session)

        # name = 'log_ads_inactive_traptemps.png'
        #
        # zugspitze_parameter_plot(dates,
        #                          {'Ads B @ Sample Start': [None, logdict.get('ads_b_sample_start')],
        #                           'Ads B @ Sample End': [None, logdict.get('ads_b_sample_end')]},
        #                          'Zugspitze Inactive Ads Trap Temperatures',
        #                          name,
        #                          limits={'right': date_limits.get('right'),
        #                                  'left': date_limits.get('left'),
        #                                  'bottom': 15,
        #                                  'top': 35},
        #                          major_ticks=major_ticks,
        #                          minor_ticks=minor_ticks)
        #
        # file_to_upload = FileToUpload(LOG_PLOT_DIR / name, remotedir, staged=True)
        # add_or_ignore_plot(file_to_upload, session)

        # name = 'log_trap_temps.png'
        # zugspitze_parameter_plot(dates,
        #                          {'Trap @ FH': [None, logdict.get('trap_temp_fh')],
        #                           'Trap @ Inject': [None, logdict.get('trap_temp_inject')],
        #                           'Trap @ Bakeout': [None, logdict.get('trap_temp_bakeout')]},
        #                          'Zugspitze Trap Temperatures',
        #                          name,
        #                          limits={'right': date_limits.get('right'),
        #                                  'left': date_limits.get('left')},
        #                          major_ticks=major_ticks,
        #                          minor_ticks=minor_ticks)
        #
        # file_to_upload = FileToUpload(LOG_PLOT_DIR / name, remotedir, staged=True)
        # add_or_ignore_plot(file_to_upload, session)

        # name = 'log_battery_voltages.png'
        # zugspitze_parameter_plot(dates,
        #                          {'BattV @ Inject': [None, logdict.get('battv_inject')],
        #                           'BattV @ Bakeout': [None, logdict.get('battv_bakeout')]},
        #                          'Zugspitze Battery Voltages',
        #                          name,
        #                          limits={'right': date_limits.get('right'),
        #                                  'left': date_limits.get('left'),
        #                                  'bottom': 8,
        #                                  'top': 14},
        #                          major_ticks=major_ticks,
        #                          minor_ticks=minor_ticks)
        #
        # file_to_upload = FileToUpload(LOG_PLOT_DIR / name, remotedir, staged=True)
        # add_or_ignore_plot(file_to_upload, session)

        # name = 'log_gc_start_wthot_temps.png'
        # zugspitze_parameter_plot(dates,
        #                          {'GC Start Temp': [None, logdict.get('gc_start_temp')],
        #                           'WT Hot Temp': [None, logdict.get('wt_hot_temp')]},
        #                          'Zugspitze GC Start and WT Hot Temps',
        #                          name,
        #                          limits={'right': date_limits.get('right'),
        #                                  'left': date_limits.get('left'),
        #                                  'bottom': 0,
        #                                  'top': 75},
        #                          major_ticks=major_ticks,
        #                          minor_ticks=minor_ticks)
        #
        # file_to_upload = FileToUpload(LOG_PLOT_DIR / name, remotedir, staged=True)
        # add_or_ignore_plot(file_to_upload, session)

        # name = 'log_heat_outs.png'
        # zugspitze_parameter_plot(dates,
        #                          {'HeatOut @ FH': [None, logdict.get('trapheatout_flashheat')],
        #                           'HeatOut @ Inject': [None, logdict.get('trapheatout_inject')],
        #                           'HeatOut @ Bakeout': [None, logdict.get('trapheatout_bakeout')]},
        #                          'Zugspitze Heat Outputs',
        #                          name,
        #                          limits={'right': date_limits.get('right'),
        #                                  'left': date_limits.get('left')},
        #                          major_ticks=major_ticks,
        #                          minor_ticks=minor_ticks)
        #
        # file_to_upload = FileToUpload(LOG_PLOT_DIR / name, remotedir, staged=True)
        # add_or_ignore_plot(file_to_upload, session)

        # name = 'log_oven_mfc_ramp.png'
        # zugspitze_twoaxis_parameter_plot(dates,
        #                                  {'GC Oven Temp': [None, logdict.get('gc_oven_temp')]},
        #                                  {'MFC1 Ramp': [None, logdict.get('mfc1_ramp')]},
        #                                  'Zugspitze Oven Temperature and MFC1 Ramp',
        #                                  name,
        #                                  limits1={'right': date_limits.get('right'),
        #                                           'left': date_limits.get('left'),
        #                                           'bottom': 180,
        #                                           'top': 230},
        #                                  limits2={'bottom': .65,
        #                                           'top': .85},
        #                                  major_ticks=major_ticks,
        #                                  minor_ticks=minor_ticks,
        #                                  y2_label_str='MFC1 Ramp')
        #
        # file_to_upload = FileToUpload(LOG_PLOT_DIR / name, remotedir, staged=True)
        # add_or_ignore_plot(file_to_upload, session)

    session.commit()
    session.close()
    engine.dispose()


def plot_dailydata(logger):
    """
    Plots data from the LabView logs as stored in Daily objects.

    Creates one set of plots of parameters logged by LabView on the half-hour. Files are queued to upload the next time
    a call to upload any files is made.

    :param logger: logging logger to record to
    :return: bool, True if ran correctly, False if exit on error
    """
    logger.info('Running plot_dailydata()')

    try:
        engine, session = connect_to_db(DB_NAME, CORE_DIR)
    except Exception as e:
        logger.error(f'Error {e.args} prevented connecting to the database in plot_dailydata()')
        return False

    remotedir = BOULDAIR_BASE_PATH + '/dailyplots'

    date_limits, major_ticks, minor_ticks = create_daily_ticks(14, minors_per_day=2)
    major_ticks[:] = [major for num, major in enumerate(major_ticks) if num % 2 == 0]  # utilize only 1/2 of the majors

    dailies = session.query(Daily).filter(Daily.date >= date_limits['left']).all()

    dates = [d.date for d in dailies]

    dailydict = {}
    for param in DAILY_ATTRS:
        dailydict[param] = [getattr(d, param) for d in dailies]

    with TempDir(DAILY_PLOT_DIR):
        name = 'daily_xfer_valve_ebox_temps.png'
        zugspitze_parameter_plot(dates,
                                 {'Ads Xfer Temp': [None, dailydict.get('ads_xfer_temp')],
                                  'Valves Temp': [None, dailydict.get('valves_temp')],
                                  'GC Xfer Temp': [None, dailydict.get('gc_xfer_temp')],
                                  'Ebox Temp': [None, dailydict.get('ebox_temp')]},
                                 'Zugspitze Daily Temperatures (Xfers, Valves, Ebox)',
                                 name,
                                 limits={'right': date_limits.get('right'),
                                         'left': date_limits.get('left'),
                                         'bottom': None,
                                         'top': None},
                                 major_ticks=major_ticks,
                                 minor_ticks=minor_ticks)

        file_to_upload = FileToUpload(DAILY_PLOT_DIR / name, remotedir, staged=True)
        add_or_ignore_plot(file_to_upload, session)

        name = 'daily_catalyst_temp.png'
        zugspitze_parameter_plot(dates,
                                 {'Catalyst Temp': [None, dailydict.get('catalyst_temp')]},
                                 'Zugspitze Daily Catalyst Temperature',
                                 name,
                                 limits={'right': date_limits.get('right'),
                                         'left': date_limits.get('left'),
                                         'bottom': 350,
                                         'top': 490},
                                 major_ticks=major_ticks,
                                 minor_ticks=minor_ticks)

        file_to_upload = FileToUpload(DAILY_PLOT_DIR / name, remotedir, staged=True)
        add_or_ignore_plot(file_to_upload, session)

        name = 'daily_inlet_room_temp.png'

        zugspitze_parameter_plot(dates,
                                 {'Inlet Temp': [None, dailydict.get('inlet_temp')],
                                  'Room Temp': [None, dailydict.get('room_temp')]},
                                 'Zugspitze Daily Temperatures (Inlet, Room)',
                                 name,
                                 limits={'right': date_limits.get('right'),
                                         'left': date_limits.get('left'),
                                         'bottom': None,
                                         'top': None},
                                 major_ticks=major_ticks,
                                 minor_ticks=minor_ticks)

        file_to_upload = FileToUpload(DAILY_PLOT_DIR / name, remotedir, staged=True)
        add_or_ignore_plot(file_to_upload, session)

        name = 'daily_5v_mfc.png'
        zugspitze_parameter_plot(dates,
                                 {'5V (v)': [None, dailydict.get('v5')],
                                  'MFC2': [None, dailydict.get('mfc2')],
                                  'MFC3': [None, dailydict.get('mfc3')],
                                  'MFC1': [None, dailydict.get('mfc1')]},
                                 'Zugspitze Daily 5V and MFC Readings',
                                 name,
                                 limits={'right': date_limits.get('right'),
                                         'left': date_limits.get('left'),
                                         'bottom': None,
                                         'top': None},
                                 y_label_str='',
                                 major_ticks=major_ticks,
                                 minor_ticks=minor_ticks)

        file_to_upload = FileToUpload(DAILY_PLOT_DIR / name, remotedir, staged=True)
        add_or_ignore_plot(file_to_upload, session)

        name = 'daily_pressures.png'
        zugspitze_parameter_plot(dates,
                                 {'LineP': [None, dailydict.get('linep')],
                                  'ZeroP': [None, dailydict.get('zerop')]},
                                 'Zugspitze Daily Pressures',
                                 name,
                                 limits={'right': date_limits.get('right'),
                                         'left': date_limits.get('left'),
                                         'bottom': None,
                                         'top': None},
                                 y_label_str='Pressure (psi)',
                                 major_ticks=major_ticks,
                                 minor_ticks=minor_ticks)

        file_to_upload = FileToUpload(DAILY_PLOT_DIR / name, remotedir, staged=True)
        add_or_ignore_plot(file_to_upload, session)

    session.commit()
    session.close()
    engine.dispose()


def plot_standard_and_ambient_peak_areas(logger):
    """
    Plots peak area responses for both ambient samples and standard samples.

    Standard peak areas are plotted to show response over time, whereas ambient peak areas are seldom used but still
    appreciated/useful on occasion. Plots are queued to be uploaded the next time a call to upload files is made.

    :param logger: logging logger to record to
    :return: bool, True if ran correctly, False if exit on error
    """
    logger.info('Running plot_standard_and_ambient_peak_areas()')

    try:
        engine, session = connect_to_db(DB_NAME, CORE_DIR)
    except Exception as e:
        logger.error(f'Error {e.args} prevented connecting to the database in plot_standard_and_ambient_peak_areas()')
        return False

    date_limits, major_ticks, minor_ticks = create_monthly_ticks(18, days_per_minor=7)
    major_ticks[:] = [major for num, major in enumerate(major_ticks) if num % 2 == 0]  # utilize only 1/2 of the majors

    remote_pa_dir = BOULDAIR_BASE_PATH + '/PA_plots'
    remote_std_dir = BOULDAIR_BASE_PATH + '/std_PA_plots'

    for compound in ALL_COMPOUNDS:
        # Plot Ambient Peak Areas
        results = (session.query(Compound.pa, Integration.date)
                   .join(Integration, Integration.id == Compound.integration_id)
                   .join(GcRun, GcRun.id == Integration.run_id)
                   .filter(Integration.date >= date_limits['left'])
                   .filter(GcRun.type == 5)
                   .filter(Compound.name == compound)
                   .filter(Compound.filtered == False)
                   .order_by(Integration.date)
                   .all())
        dates = []
        pas = []
        for result in results:
            dates.append(result[1])
            pas.append(result[0])

        with TempDir(PA_PLOT_DIR):
            plot_name = zugspitze_pa_plot(None, ({compound: [dates, pas]}),
                                          limits={'right': date_limits.get('right', None),
                                                  'left': date_limits.get('left', None)},
                                          major_ticks=major_ticks,
                                          minor_ticks=minor_ticks)

            file_to_upload = FileToUpload(PA_PLOT_DIR / plot_name, remote_pa_dir, staged=True)
            add_or_ignore_plot(file_to_upload, session)

        # Plot Standard Peak Areas
        results = (session.query(Compound.pa, Integration.date)
                   .join(Integration, Integration.id == Compound.integration_id)
                   .join(GcRun, GcRun.id == Integration.run_id)
                   .filter(Integration.date >= date_limits['left'])
                   .filter(GcRun.type.in_([1, 2, 3]))
                   .filter(Compound.name == compound)
                   .order_by(Integration.date)
                   .all())

        dates = []
        pas = []
        for result in results:
            dates.append(result[1])
            pas.append(result[0])

        with TempDir(STD_PA_PLOT_DIR):
            plot_name = zugspitze_pa_plot(None, ({compound: [dates, pas]}),
                                          limits={'right': date_limits.get('right', None),
                                                  'left': date_limits.get('left', None)},
                                          major_ticks=major_ticks,
                                          minor_ticks=minor_ticks,
                                          standard=True)

            file_to_upload = FileToUpload(STD_PA_PLOT_DIR / plot_name, remote_std_dir, staged=True)
            add_or_ignore_plot(file_to_upload, session)

    session.commit()
    session.close()
    engine.dispose()
    return True
