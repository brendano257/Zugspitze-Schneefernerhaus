import json

from IO import connect_to_db, add_or_ignore_plot
from settings import CORE_DIR, BOULDAIR_BASE_PATH
from processing.constants import LOG_ATTRS, DAILY_ATTRS, ALL_COMPOUNDS
from IO.db.models import OldData, Daily, Compound, LogFile, Integration, GcRun, Standard, Quantification
from IO.db import FileToUpload, TempDir
from plotting.utils import create_monthly_ticks, create_daily_ticks
from plotting.plots import zugspitze_mixing_plot, zugspitze_parameter_plot, zugspitze_twoaxis_parameter_plot
from plotting.plots import zugspitze_pa_plot

__all__ = ['plot_new_data', 'plot_history', 'plot_logdata', 'plot_dailydata', 'plot_standard_and_ambient_peak_areas']


def plot_new_data(logger):
    """
    Plots mixing ratio data, creating plot files and queueing the files for upload.

    This will plot data, regardless of if there's any new data since it's not run continously.

    :param logger: logging logger to record to
    :return: bool, True if ran corrected, False if exit on error
    """
    logger.info('Running plot_new_data()')
    try:
        engine, session = connect_to_db('sqlite:///zugspitze.sqlite', CORE_DIR)
    except Exception as e:
        logger.error(f'Error {e.args} prevented connecting to the database in plot_new_data()')
        return False

    plotdir = CORE_DIR / 'plotting/created/mr_plots'
    remotedir = BOULDAIR_BASE_PATH + '/MR_plots'

    compounds_to_plot = (session.query(Quantification.name)
                         .join(Standard, Quantification.standard_id == Standard.id)
                         .filter(Standard.name == 'quantlist').all())
    compounds_to_plot[:] = [q.name for q in compounds_to_plot]

    date_limits, major_ticks, minor_ticks = create_monthly_ticks(6)

    with open(CORE_DIR / 'data/json/public' / 'zug_plot_info.json', 'r') as file:
        compound_limits = json.loads(file.read())

    for name in compounds_to_plot:
        results = (session.query(Compound.mr, Integration.date)
                   .join(Integration, Integration.id == Compound.integration_id)
                   .join(GcRun, GcRun.id == Integration.run_id)
                   .filter(Integration.date >= date_limits['left'])
                   .filter(GcRun.type == 5)
                   .filter(Compound.name == name)
                   .filter(Compound.filtered == False)
                   .order_by(Integration.date)
                   .all())

        dates = []
        mrs = []
        for result in results:
            dates.append(result[1])
            mrs.append(result[0])

        with TempDir(plotdir):
            try:
                compound_limits.get(name).get('bottom')
            except Exception:
                logger.warning(f'Compound {name} needs limits to plot!')
                continue

            plot_name = zugspitze_mixing_plot(None, ({name: [dates, mrs]}),
                                              limits={'right': date_limits.get('right', None),
                                                      'left': date_limits.get('left', None),
                                                      'bottom': compound_limits.get(name).get('bottom'),
                                                      'top': compound_limits.get(name).get('top')},
                                              major_ticks=major_ticks,
                                              minor_ticks=minor_ticks)

            file_to_upload = FileToUpload(plotdir / plot_name, remotedir, staged=True)
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
        engine, session = connect_to_db('sqlite:///zugspitze.sqlite', CORE_DIR)
    except Exception as e:
        logger.error(f'Error {e.args} prevented connecting to the database in plot_history()')
        return False

    plotdir = CORE_DIR / 'plotting/created/full_plots'
    remotedir = BOULDAIR_BASE_PATH + '/full_plots'

    compounds_to_plot = (session.query(Quantification.name)
                         .join(Standard, Quantification.standard_id == Standard.id)
                         .filter(Standard.name == 'quantlist').all())
    compounds_to_plot[:] = [q.name for q in compounds_to_plot]

    date_limits, major_ticks, minor_ticks = create_monthly_ticks(84, minors_per_month=1)

    major_ticks = major_ticks[::6]

    with open(CORE_DIR / 'data/json/public' / 'zug_long_plot_info.json', 'r') as file:
        compound_limits = json.loads(file.read())

    for name in compounds_to_plot:

        old_results = (session.query(OldData.date, OldData.mr)
                       .filter(OldData.name == name)
                       .order_by(OldData.date)
                       .all())

        new_results = (session.query(Compound.mr, Integration.date)
                       .join(Integration, Integration.id == Compound.integration_id)
                       .join(GcRun, GcRun.id == Integration.run_id)
                       .filter(Integration.date >= date_limits['left'])
                       .filter(GcRun.type == 5)
                       .filter(Compound.name == name)
                       .filter(Compound.filtered == False)
                       .order_by(Integration.date)
                       .all())

        dates = [o.date for o in old_results]
        mrs = [o.mr for o in old_results]
        for result in new_results:
            dates.append(result[1])
            mrs.append(result[0])

        with TempDir(plotdir):
            try:
                compound_limits.get(name).get('bottom')
            except Exception:
                logger.warning(f'Compound {name} needs limits to plot!')
                continue

            plot_name = zugspitze_mixing_plot(None, ({name: [dates, mrs]}),
                                              limits={'right': date_limits.get('right', None),
                                                      'left': date_limits.get('left', None),
                                                      'bottom': compound_limits.get(name).get('bottom'),
                                                      'top': compound_limits.get(name).get('top')},
                                              major_ticks=major_ticks,
                                              minor_ticks=minor_ticks)

            file_to_upload = FileToUpload(plotdir / plot_name, remotedir, staged=True)
            add_or_ignore_plot(file_to_upload, session)

            zero_plot_name = zugspitze_mixing_plot(None, ({name: [dates, mrs]}),
                                                   limits={'right': date_limits.get('right', None),
                                                           'left': date_limits.get('left', None),
                                                           'bottom': 0,
                                                           'top': compound_limits.get(name).get('top')},
                                                   major_ticks=major_ticks,
                                                   minor_ticks=minor_ticks,
                                                   filename_suffix='_zeroed')

            file_to_upload = FileToUpload(plotdir / zero_plot_name, remotedir, staged=True)
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
        engine, session = connect_to_db('sqlite:///zugspitze.sqlite', CORE_DIR)
    except Exception as e:
        logger.error(f'Error {e.args} prevented connecting to the database in plot_logdata()')
        return False

    plotdir = CORE_DIR / 'plotting/created/logplots'
    remotedir = BOULDAIR_BASE_PATH + '/logplots'

    date_limits, major_ticks, minor_ticks = create_daily_ticks(14, minors_per_day=2)
    major_ticks[:] = [major for num, major in enumerate(major_ticks) if num % 2 == 0]  # utilize only 1/2 of the majors

    logs = session.query(LogFile).filter(LogFile.date >= date_limits.get('left')).all()

    logdict = {}
    for param in LOG_ATTRS:
        logdict[param] = [getattr(l, param) for l in logs]

    dates = [l.date for l in logs]

    with TempDir(plotdir):
        name = 'log_sample_pressure_flow.png'
        zugspitze_parameter_plot(dates,
                                 ({'Sample Pressure Start': [None, logdict.get('sample_p_start')],
                                   'Sample Flow (V)': [None, logdict.get('sample_flow_act')]}),
                                 'Zugspitze Sample Pressures',
                                 name,
                                 limits={'right': date_limits.get('right'),
                                         'left': date_limits.get('left'),
                                         'bottom': 0,
                                         'top': 4},
                                 y_label_str='',
                                 major_ticks=major_ticks,
                                 minor_ticks=minor_ticks)

        file_to_upload = FileToUpload(plotdir / name, remotedir, staged=True)
        add_or_ignore_plot(file_to_upload, session)

        name = 'log_sample_pressure_during.png'
        zugspitze_parameter_plot(dates,
                                 {'Sample Pressure During': [None, logdict.get('sample_p_during')]},
                                 'Zugspitze Sample Pressure During Run',
                                 name,
                                 limits={'right': date_limits.get('right'),
                                         'left': date_limits.get('left'),
                                         'bottom': 4,
                                         'top': 12},
                                 y_label_str='Pressure (psi)',
                                 major_ticks=major_ticks,
                                 minor_ticks=minor_ticks)

        file_to_upload = FileToUpload(plotdir / name, remotedir, staged=True)
        add_or_ignore_plot(file_to_upload, session)

        name = 'log_gcheadp_pressures.png'
        zugspitze_parameter_plot(dates,
                                 {'GC HeadP Start': [None, logdict.get('gcheadp_start')],
                                  'GC HeadP During': [None, logdict.get('gcheadp_during')]},
                                 'Zugspitze GC Head Pressures',
                                 name,
                                 limits={'right': date_limits.get('right'),
                                         'left': date_limits.get('left'),
                                         'bottom': None,
                                         'top': None},
                                 y_label_str='Pressure (psi)',
                                 major_ticks=major_ticks,
                                 minor_ticks=minor_ticks)

        file_to_upload = FileToUpload(plotdir / name, remotedir, staged=True)
        add_or_ignore_plot(file_to_upload, session)

        name = 'log_wat_ads_active_traptemps.png'
        zugspitze_parameter_plot(dates,
                                 {'WT @ Sample Start': [None, logdict.get('wt_sample_start')],
                                  'WT @ Sample End': [None, logdict.get('wt_sample_end')],
                                  'Ads A @ Sample Start': [None, logdict.get('ads_a_sample_start')],
                                  'Ads A @ Sample End': [None, logdict.get('ads_a_sample_end')]},
                                 'Zugspitze Active Ads and Water Trap Temperatures',
                                 name,
                                 limits={'right': date_limits.get('right'),
                                         'left': date_limits.get('left'),
                                         'bottom': -55,
                                         'top': -30},
                                 major_ticks=major_ticks,
                                 minor_ticks=minor_ticks)

        file_to_upload = FileToUpload(plotdir / name, remotedir, staged=True)
        add_or_ignore_plot(file_to_upload, session)

        name = 'log_ads_inactive_traptemps.png'

        zugspitze_parameter_plot(dates,
                                 {'Ads B @ Sample Start': [None, logdict.get('ads_b_sample_start')],
                                  'Ads B @ Sample End': [None, logdict.get('ads_b_sample_end')]},
                                 'Zugspitze Inactive Ads Trap Temperatures',
                                 name,
                                 limits={'right': date_limits.get('right'),
                                         'left': date_limits.get('left'),
                                         'bottom': 15,
                                         'top': 35},
                                 major_ticks=major_ticks,
                                 minor_ticks=minor_ticks)

        file_to_upload = FileToUpload(plotdir / name, remotedir, staged=True)
        add_or_ignore_plot(file_to_upload, session)

        name = 'log_trap_temps.png'
        zugspitze_parameter_plot(dates,
                                 {'Trap @ FH': [None, logdict.get('trap_temp_fh')],
                                  'Trap @ Inject': [None, logdict.get('trap_temp_inject')],
                                  'Trap @ Bakeout': [None, logdict.get('trap_temp_bakeout')]},
                                 'Zugspitze Trap Temperatures',
                                 name,
                                 limits={'right': date_limits.get('right'),
                                         'left': date_limits.get('left')},
                                 major_ticks=major_ticks,
                                 minor_ticks=minor_ticks)

        file_to_upload = FileToUpload(plotdir / name, remotedir, staged=True)
        add_or_ignore_plot(file_to_upload, session)

        name = 'log_battery_voltages.png'
        zugspitze_parameter_plot(dates,
                                 {'BattV @ Inject': [None, logdict.get('battv_inject')],
                                  'BattV @ Bakeout': [None, logdict.get('battv_bakeout')]},
                                 'Zugspitze Battery Voltages',
                                 name,
                                 limits={'right': date_limits.get('right'),
                                         'left': date_limits.get('left'),
                                         'bottom': 8,
                                         'top': 14},
                                 major_ticks=major_ticks,
                                 minor_ticks=minor_ticks)

        file_to_upload = FileToUpload(plotdir / name, remotedir, staged=True)
        add_or_ignore_plot(file_to_upload, session)

        name = 'log_gc_start_wthot_temps.png'
        zugspitze_parameter_plot(dates,
                                 {'GC Start Temp': [None, logdict.get('gc_start_temp')],
                                  'WT Hot Temp': [None, logdict.get('wt_hot_temp')]},
                                 'Zugspitze GC Start and WT Hot Temps',
                                 name,
                                 limits={'right': date_limits.get('right'),
                                         'left': date_limits.get('left'),
                                         'bottom': 0,
                                         'top': 75},
                                 major_ticks=major_ticks,
                                 minor_ticks=minor_ticks)

        file_to_upload = FileToUpload(plotdir / name, remotedir, staged=True)
        add_or_ignore_plot(file_to_upload, session)

        name = 'log_heat_outs.png'
        zugspitze_parameter_plot(dates,
                                 {'HeatOut @ FH': [None, logdict.get('trapheatout_flashheat')],
                                  'HeatOut @ Inject': [None, logdict.get('trapheatout_inject')],
                                  'HeatOut @ Bakeout': [None, logdict.get('trapheatout_bakeout')]},
                                 'Zugspitze Heat Outputs',
                                 name,
                                 limits={'right': date_limits.get('right'),
                                         'left': date_limits.get('left')},
                                 major_ticks=major_ticks,
                                 minor_ticks=minor_ticks)

        file_to_upload = FileToUpload(plotdir / name, remotedir, staged=True)
        add_or_ignore_plot(file_to_upload, session)

        name = 'log_oven_mfc_ramp.png'
        zugspitze_twoaxis_parameter_plot(dates,
                                         {'GC Oven Temp': [None, logdict.get('gc_oven_temp')]},
                                         {'MFC1 Ramp': [None, logdict.get('mfc1_ramp')]},
                                         'Zugspitze Oven Temperature and MFC1 Ramp',
                                         name,
                                         limits1={'right': date_limits.get('right'),
                                                  'left': date_limits.get('left'),
                                                  'bottom': 180,
                                                  'top': 230},
                                         limits2={'bottom': .65,
                                                  'top': .85},
                                         major_ticks=major_ticks,
                                         minor_ticks=minor_ticks,
                                         y2_label_str='MFC1 Ramp')

        file_to_upload = FileToUpload(plotdir / name, remotedir, staged=True)
        add_or_ignore_plot(file_to_upload, session)

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
        engine, session = connect_to_db('sqlite:///zugspitze.sqlite', CORE_DIR)
    except Exception as e:
        logger.error(f'Error {e.args} prevented connecting to the database in plot_dailydata()')
        return False

    plotdir = CORE_DIR / 'plotting/created/dailyplots'
    remotedir = BOULDAIR_BASE_PATH + '/dailyplots'

    date_limits, major_ticks, minor_ticks = create_daily_ticks(14, minors_per_day=2)
    major_ticks[:] = [major for num, major in enumerate(major_ticks) if num % 2 == 0]  # utilize only 1/2 of the majors

    dailies = session.query(Daily).filter(Daily.date >= date_limits['left']).all()

    dates = [d.date for d in dailies]

    dailydict = {}
    for param in DAILY_ATTRS:
        dailydict[param] = [getattr(d, param) for d in dailies]

    with TempDir(plotdir):
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

        file_to_upload = FileToUpload(plotdir / name, remotedir, staged=True)
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

        file_to_upload = FileToUpload(plotdir / name, remotedir, staged=True)
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

        file_to_upload = FileToUpload(plotdir / name, remotedir, staged=True)
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

        file_to_upload = FileToUpload(plotdir / name, remotedir, staged=True)
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

        file_to_upload = FileToUpload(plotdir / name, remotedir, staged=True)
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
        engine, session = connect_to_db('sqlite:///zugspitze.sqlite', CORE_DIR)
    except Exception as e:
        logger.error(f'Error {e.args} prevented connecting to the database in plot_standard_and_ambient_peak_areas()')
        return False

    date_limits, major_ticks, minor_ticks = create_monthly_ticks(18)
    major_ticks[:] = [major for num, major in enumerate(major_ticks) if num % 2 == 0]  # utilize only 1/2 of the majors

    pa_plotdir = CORE_DIR / 'plotting/created/PA_plots'
    std_pa_plotdir = CORE_DIR / 'plotting/created/std_PA_plots'

    remote_padir = BOULDAIR_BASE_PATH + '/PA_plots'
    remote_stddir = BOULDAIR_BASE_PATH + '/std_PA_plots'

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

        with TempDir(pa_plotdir):
            plot_name = zugspitze_pa_plot(None, ({compound: [dates, pas]}),
                                          limits={'right': date_limits.get('right', None),
                                                  'left': date_limits.get('left', None)},
                                          major_ticks=major_ticks,
                                          minor_ticks=minor_ticks)

            file_to_upload = FileToUpload(pa_plotdir / plot_name, remote_padir, staged=True)
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

        with TempDir(std_pa_plotdir):
            plot_name = zugspitze_pa_plot(None, ({compound: [dates, pas]}),
                                          limits={'right': date_limits.get('right', None),
                                                  'left': date_limits.get('left', None)},
                                          major_ticks=major_ticks,
                                          minor_ticks=minor_ticks,
                                          standard=True)

            file_to_upload = FileToUpload(std_pa_plotdir / plot_name, remote_stddir, staged=True)
            add_or_ignore_plot(file_to_upload, session)

    session.commit()
    session.close()
    engine.dispose()
    return True
