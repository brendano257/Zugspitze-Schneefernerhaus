from pathlib import Path
from abc import ABC, abstractmethod
from collections.abc import Sequence
import datetime as dt

from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship, Session

from IO.db.core import Base, connect_to_db
from IO.db.models.standards import Standard
from utils.core import search_for_attr_value, find_closest_date

from settings import CORE_DIR, DB_NAME


__all__ = ['Compound', 'LogFile', 'DailyFile', 'Daily', 'Integration', 'GcRun', 'Datum', 'OldData']


class Compound(Base):
    """
    Container for the measured value of a chemical species in a sample.

    A Compound must have a name, retention time (rt), ion, and peak area (pa) to be created. These are the core
    components that express a measurement on the GCMS. Once quantified (in a higher-level container, like a GcRun), they
    can be given a mixing ratio (mr), corrected/blank-subtracted peak area (corrected_pa) and a filtered flag for
    quality control.

    Compounds are related to LogFiles, Integrations, and GcRuns. Many Compounds can belong to any of the above.
    Compounds are created in the process of reading a results file and creating an Integration. When an integration is
    matched to a log file, then merged into a GcRun, the Compounds belonging to the Integration are then related to the
    matched LogFile, then GcRun for your querying convenience.
    """

    __tablename__ = 'compounds'

    id = Column(Integer, primary_key=True)

    name = Column(String)
    rt = Column(Float)
    ion = Column(Integer)
    pa = Column(Integer)
    corrected_pa = Column(Integer)
    mr = Column(Float)
    filtered = Column(Boolean)

    log_id = Column(Integer, ForeignKey('logfiles.id'))
    log = relationship('LogFile', foreign_keys=[log_id], back_populates='compounds')

    integration_id = Column(Integer, ForeignKey('integrations.id'))
    integration = relationship('Integration', foreign_keys=[integration_id], back_populates='compounds')

    run_id = Column(Integer, ForeignKey('gcruns.id'))
    run = relationship('GcRun', foreign_keys=[run_id], back_populates='compounds')

    def __init__(self, name, rt, ion, pa):
        """
        Create a compound with the required name, retention time, ion, and peak area.

        corrected_pa is set by blank subtracting the sample, where corrected_pa = pa - blank_value
        filtered is by default False, but can be set to True to indicate the sample is flagged as not-plottable

        :param str name: chemical name of the compound
        :param float rt: retention/elution time of the compound
        :param int ion: ion measured by GCMS for this compound
        :param int pa: peak area given by GCMS response under the peak
        """
        self.name = name
        self.rt = rt
        self.ion = ion
        self.pa = pa
        self.corrected_pa = None
        self.filtered = False


class LogFile(Base):
    """
    A container for the information contained in a log file created by LabView when a run is finished.

    LogFiles contain all the information that LabView logs, and are related one-to-one with any or none of
    [Integration, GcRun, Datum] and 0 to many Compounds. If a LogFile is unrelated, it indicates a missing Integration
    that could be matched to it. This may mean that LabView ran a run that went un-recorded by the GCMS, the data is
    unprocessed as of yet, or was removed etc.

    LogFiles are created when the log file is read, then later matched to Integration data within certain time
    tolerances. When related to an Integration, a GcRun (related to the LogFile and Integration) is created. At that
    time, any Compounds in the Integration are related to the LogFile and GcRun at the same time to make complex queries
    less convoluted.

    All parameters are not documented to preserve the sanity of the author.
    Common abbreviates are:
        temp: temperature
        wt: water trap
        fh: flash heat
        gc: gas chromatograph (the instrument)
        head: valve head (for the gc)
        p: pressure
        ads: adsorbent trap
        act: denotes measured value of 'whatever_flow_act', whereas 'whatever_flow' indicates the set point
    """
    __tablename__ = 'logfiles'

    id = Column(Integer, primary_key=True)

    date = Column(DateTime, unique=True)
    sample_time = Column(Float)
    sample_flow = Column(Float)
    sample_type = Column(Float)
    backflush_time = Column(Float)
    desorb_temp = Column(Float)
    flashheat_time = Column(Float)
    inject_time = Column(Float)
    bakeout_temp = Column(Float)
    bakeout_time = Column(Float)
    carrier_flow = Column(Float)
    sample_flow_act = Column(Float)
    sample_num = Column(Float)
    ads_trap = Column(Float)
    sample_p_start = Column(Float)
    sample_p_during = Column(Float)
    gcheadp_start = Column(Float)
    gcheadp_during = Column(Float)
    wt_sample_start = Column(Float)
    wt_sample_end = Column(Float)
    ads_a_sample_start = Column(Float)
    ads_b_sample_start = Column(Float)
    ads_a_sample_end = Column(Float)
    ads_b_sample_end = Column(Float)
    trap_temp_fh = Column(Float)
    trap_temp_inject = Column(Float)
    trap_temp_bakeout = Column(Float)
    battv_inject = Column(Float)
    battv_bakeout = Column(Float)
    gc_start_temp = Column(Float)
    gc_oven_temp = Column(Float)
    wt_hot_temp = Column(Float)
    sample_code = Column(Float)
    mfc1_ramp = Column(Float)
    trapheatout_flashheat = Column(Float)
    trapheatout_inject = Column(Float)
    trapheatout_bakeout = Column(Float)
    status = Column(String)

    compounds = relationship('Compound', back_populates='log')

    integration_id = Column(Integer, ForeignKey('integrations.id'))
    integration = relationship('Integration', uselist=False, foreign_keys=[integration_id], back_populates='log')

    run_id = Column(Integer, ForeignKey('gcruns.id'))
    run = relationship('GcRun', uselist=False, foreign_keys=[run_id], back_populates='log')

    data_id = Column(Integer, ForeignKey('data.id'))
    data = relationship('Datum', uselist=False, foreign_keys=[data_id], back_populates='log')

    def __init__(self, date, sample_time, sample_flow, sample_type, backflush_time, desorb_temp, flashheat_time,
                 inject_time, bakeout_temp, bakeout_time, carrier_flow, sample_flow_act, sample_num, ads_trap,
                 sample_p_start, sample_p_during, gcheadp_start, gcheadp_during, wt_sample_start, wt_sample_end,
                 ads_a_sample_start, ads_b_sample_start, ads_a_sample_end, ads_b_sample_end, trap_temp_fh,
                 trap_temp_inject, trap_temp_bakeout, battv_inject, battv_bakeout, gc_start_temp, gc_oven_temp,
                 wt_hot_temp, sample_code, mfc1_ramp, trapheatout_flashheat, trapheatout_inject, trapheatout_bakeout):
        """
        Create a LogFile with the given parameters.

        :param datetime date: date the log was recorded at, as provided by LabView
        :param float sample_time: duration in seconds of the sample, used in mixing ratio calculation
        :param float sample_flow: voltage of sample flow in Volts, used in mixing ratio calculate
        :param float sample_type: integer code for sample, used to determine type of sample
            {0: zero_air_blank, 1: alt_standard_port, 2: standard_port,
            3: standard_port, 4: unsure, 5: ambient_sample, 6: trap_blank}
        :param float backflush_time: instrument parameter
        :param float desorb_temp: instrument parameter
        :param float flashheat_time: instrument parameter
        :param float inject_time: instrument parameter
        :param float bakeout_temp: instrument parameter
        :param float bakeout_time: instrument parameter
        :param float carrier_flow: instrument parameter
        :param float sample_flow_act: instrument parameter
        :param float sample_num: instrument parameter
        :param float ads_trap: instrument parameter
        :param float sample_p_start: instrument parameter
        :param float sample_p_during: instrument parameter
        :param float gcheadp_start: instrument parameter
        :param float gcheadp_during: instrument parameter
        :param float wt_sample_start: instrument parameter
        :param float wt_sample_end: instrument parameter
        :param float ads_a_sample_start: instrument parameter
        :param float ads_b_sample_start: instrument parameter
        :param float ads_a_sample_end: instrument parameter
        :param float ads_b_sample_end: instrument parameter
        :param float trap_temp_fh: instrument parameter
        :param float trap_temp_inject: instrument parameter
        :param float trap_temp_bakeout: instrument parameter
        :param float battv_inject: instrument parameter
        :param float battv_bakeout: instrument parameter
        :param float gc_start_temp: instrument parameter
        :param float gc_oven_temp: instrument parameter
        :param float wt_hot_temp: instrument parameter
        :param float sample_code: instrument parameter
        :param float mfc1_ramp: instrument parameter
        :param float trapheatout_flashheat: instrument parameter
        :param float trapheatout_inject: instrument parameter
        :param float trapheatout_bakeout: instrument parameter
        """

        self.date = date
        self.sample_time = sample_time
        self.sample_flow = sample_flow
        self.sample_type = sample_type
        self.backflush_time = backflush_time
        self.desorb_temp = desorb_temp
        self.flashheat_time = flashheat_time
        self.inject_time = inject_time
        self.bakeout_temp = bakeout_temp
        self.bakeout_time = bakeout_time
        self.carrier_flow = carrier_flow
        self.sample_flow_act = sample_flow_act
        self.sample_num = sample_num
        self.ads_trap = ads_trap
        self.sample_p_start = sample_p_start
        self.sample_p_during = sample_p_during
        self.gcheadp_start = gcheadp_start
        self.gcheadp_during = gcheadp_during
        self.wt_sample_start = wt_sample_start
        self.wt_sample_end = wt_sample_end
        self.ads_a_sample_start = ads_a_sample_start
        self.ads_b_sample_start = ads_b_sample_start
        self.ads_a_sample_end = ads_a_sample_end
        self.ads_b_sample_end = ads_b_sample_end
        self.trap_temp_fh = trap_temp_fh
        self.trap_temp_inject = trap_temp_inject
        self.trap_temp_bakeout = trap_temp_bakeout
        self.battv_inject = battv_inject
        self.battv_bakeout = battv_bakeout
        self.gc_start_temp = gc_start_temp
        self.gc_oven_temp = gc_oven_temp
        self.wt_hot_temp = wt_hot_temp
        self.sample_code = sample_code
        self.mfc1_ramp = mfc1_ramp
        self.trapheatout_flashheat = trapheatout_flashheat
        self.trapheatout_inject = trapheatout_inject
        self.trapheatout_bakeout = trapheatout_bakeout
        self.status = 'single'


class DailyFile(Base):
    """
    A container representing one file with logged parameters at 30-minute intervals by LabView.

    DailyFiles are used to track files that have been loaded into the database, and persist the size of the file to
    prevent unnecessary reads of untouched files. DailyFiles are related one --> many with the Daily measurements that
    are read from them.
    """
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True)

    entries = relationship('Daily', back_populates='file')

    _path = Column(String, unique=True)
    _name = Column(String)
    size = Column(Integer)

    def __init__(self, path):
        """
        Create a DailyFile with the specified Path.
        :param Path path: path of the file, to be persisted as a string
        """
        self.path = path
        self.size = path.stat().st_size
        self.entries = []

    @property
    def path(self):
        """Getter for path that returns a Path of the persisted string"""
        return Path(self._path)

    @path.setter
    def path(self, value):
        """Setting for path that resolves the Path, then persists the string of it; sets name of the path, too"""
        self._path = str(value.resolve())
        self._name = value.name

    @property
    def name(self):
        """Getter that returns the filename of the stored path"""
        return self._name


class Daily(Base):
    """
    A container for the regularly logged parameters that LabView records on the half-hour.

    Dailys are used for plotting only, and have very little use other than quality control/system monitoring.
    They are related many --> one with the DailyFile they were read from.
    """
    __tablename__ = 'dailies'

    id = Column(Integer, primary_key=True)

    date = Column(DateTime, unique=True)
    ads_xfer_temp = Column(Float)
    valves_temp = Column(Float)
    gc_xfer_temp = Column(Float)
    ebox_temp = Column(Float)
    catalyst_temp = Column(Float)
    molsieve_a_temp = Column(Float)
    molsieve_b_temp = Column(Float)
    inlet_temp = Column(Float)
    room_temp = Column(Float)
    v5 = Column(Float)
    mfc1 = Column(Float)
    mfc2 = Column(Float)
    mfc3 = Column(Float)
    he_pressure = Column(Float)
    linep = Column(Float)
    zerop = Column(Float)

    file_id = Column(Integer, ForeignKey('files.id'))
    file = relationship('DailyFile', back_populates='entries')

    def __init__(self, date, ads_xfer_temp, valves_temp, gc_xfer_temp, ebox_temp, catalyst_temp, molsieve_a_temp,
                 molsieve_b_temp, inlet_temp, room_temp, v5, mfc1, mfc2, mfc3, he_pressure, linep, zerop):
        """
        Creates a Daily measurement with the given date and parameters.

        :param datetime date: date the parameters were recorded at.
        :param float ads_xfer_temp: instrument parameter
        :param float valves_temp: instrument parameter
        :param float gc_xfer_temp: instrument parameter
        :param float ebox_temp: instrument parameter
        :param float catalyst_temp: instrument parameter
        :param float molsieve_a_temp: instrument parameter
        :param float molsieve_b_temp: instrument parameter
        :param float inlet_temp: instrument parameter
        :param float room_temp: instrument parameter
        :param float v5: instrument parameter
        :param float mfc1: instrument parameter
        :param float mfc2: instrument parameter
        :param float mfc3: instrument parameter
        :param float he_pressure: instrument parameter
        :param float linep: instrument parameter
        :param float zerop: instrument parameter
        """
        self.date = date
        self.ads_xfer_temp = ads_xfer_temp
        self.valves_temp = valves_temp
        self.gc_xfer_temp = gc_xfer_temp
        self.ebox_temp = ebox_temp
        self.catalyst_temp = catalyst_temp
        self.molsieve_a_temp = molsieve_a_temp
        self.molsieve_b_temp = molsieve_b_temp
        self.inlet_temp = inlet_temp
        self.room_temp = room_temp
        self.v5 = v5
        self.mfc1 = mfc1
        self.mfc2 = mfc2
        self.mfc3 = mfc3
        self.he_pressure = he_pressure
        self.linep = linep
        self.zerop = zerop


class Integration(Base):
    """
    A container for the results of integrating a run on the GCMS.

    Integrations are created by parsing the GCMS integration_results.txt files. They can be related one to one with
    [LogFile, GcRun, Datum] and one --> many Compounds. Integrations contain metadata from the results file, and link to
    all the compounds that were analyzed as part of the sample. When matched by time to a LogFile, they create a GcRun
    and are linked to the GcRun and LogFile going foward. An un-matched Integration means a LabView log was lost, unread
    or other unavailable to match to the Integration. This is less commond than vice-versa, since LabView must run in
    order for the GCMS to record anything.
    """
    __tablename__ = 'integrations'

    id = Column(Integer, primary_key=True)
    filename = Column(String)
    date = Column(DateTime, unique=True)
    _path = Column(String)
    method = Column(String)
    status = Column(String)

    log = relationship('LogFile', uselist=False, back_populates='integration')
    compounds = relationship('Compound', back_populates='integration')

    run_id = Column(Integer, ForeignKey('gcruns.id'))
    run = relationship('GcRun', uselist=False, foreign_keys=[run_id], back_populates='integration')

    data_id = Column(Integer, ForeignKey('data.id'))
    data = relationship('Datum', uselist=False, foreign_keys=[data_id], back_populates='integration')

    def __init__(self, filename, date, path, quant_time, method, compounds):
        """
        Create an Integration object with the given date and path.

        Metadata from the integration_results.txt file is added, then all the compounds created from the file read are
        related to the Integration.

        :param str filename: name of the containing folder, e.g. '2019_12_31_01.D'
        :param datetime date: date of the recorded data
        :param Path path: path to the integration_results.txt file
        :param datetime quant_time: unused/unset as of now; metadata
        :param str method: analysis method given in integration_results.txt
        :param list compounds: a list of Compound objects to be related to the Integration
        """
        self.log = None
        self.filename = filename
        self.date = date
        self.path = path
        self.quant_time = quant_time
        self.method = method
        self.compounds = compounds
        self.status = 'single'

    @property
    def path(self):
        return Path(self._path)

    @path.setter
    def path(self, val):
        self._path = str(val)


class BlankSubtractedMixin(ABC):

    @abstractmethod
    def __init__(self):
        self.type = None
        self.date = None
        self.compounds = None
        pass

    @abstractmethod
    def quantify(self):
        pass

    def _default_to_pass_values(self, session):
        """
        Pass the value for all peaks.

        :param session: active sqlalchemy session
        :return:
        """
        print('Defaulted and pass all values.')
        for peak in self.compounds:
            peak.corrected_pa = peak.pa
        session.merge(self)

    def _subtract_peak(self, peak, blank_peak):
        """
        Blank subtract a single peak with the provided blank peak.

        :param Compound peak:
        :param Compound blank_peak:
        :return:
        :raises TypeError: if peaks are not of type Compound
        """

        if not isinstance(peak, Compound) or not isinstance(blank_peak, Compound):
            msg = 'provided peak and blank peak must be of type Compound'
            raise TypeError(msg)

        if peak.pa is not None and blank_peak.pa is not None:
            peak.corrected_pa = peak.pa - blank_peak.pa  # subtract the blank area
            print(f'{peak.name}: New PA: {peak.corrected_pa} = old PA: {peak.pa} -  blank PA: {blank_peak.pa}')
            if peak.corrected_pa < 0:
                print('Peak pa defaulted to 0 after negative found')
                peak.corrected_pa = 0  # catch negatives and set to 0
        elif peak.pa is None:
            print('Peak.pa was None, peak.corrected_pa will be none')
            peak.corrected_pa = None  # leave as None
        elif blank_peak.pa is None:
            print('Blank peak pa was None, peak.pa will be passed.')
            peak.corrected_pa = peak.pa  # subtract nothing
        else:
            print('The seemingly impossible happened!')
            peak.corrected_pa = peak.pa  # can we get here? Pass the value just in case

    def blank_subtract(self, *, session=object(), compounds_to_subtract=object(), blank=object(), hours_to_match=6):
        """
        TODO
        :param compounds_to_subtract:
        :param blank: Provide None to pass values
        :return:
        :raises TypeError: if blank is not of type GcRun or NoneType
        """

        print(f'Blank subtracting GcRun for {self.date}')

        blank_default = self.blank_subtract.__kwdefaults__['blank']  # get default object to use as a sentinel value
        compounds_to_subtract_default = self.blank_subtract.__kwdefaults__['compounds_to_subtract']  # ''
        session_default = self.blank_subtract.__kwdefaults__['session']  # ''

        if session is session_default:
            engine, session = connect_to_db(DB_NAME, CORE_DIR)
        elif not isinstance(session, Session):
            msg = 'Provided session must be a sqlalchemy Session object'
            TypeError(msg)

        if compounds_to_subtract is compounds_to_subtract_default:
            print('Defaulted to subtracting vocs')
            # default to getting vocs from database
            vocs = session.query(Standard).filter(Standard.name == 'vocs').one()
            compounds_to_subtract = [q.name for q in vocs.quantifications]

        if not isinstance(compounds_to_subtract, Sequence):
            msg = 'compounds_to_subtract must be of type Sequence'
            raise TypeError(msg)

        if blank is blank_default and self.type not in [0, 6]:
            print('Looking for blank to subtract.')
            # match blanks if not value was provided and this sample isn't a blank
            close_blanks = (session.query(GcRun)
                            .filter(GcRun.type == 0)
                            .filter(GcRun.date >= self.date - dt.timedelta(hours=hours_to_match),
                                    GcRun.date < self.date + dt.timedelta(hours=hours_to_match))
                            .all())

            match, delta = find_closest_date(self.date, [r.date for r in close_blanks], how='abs')
            self.blank = search_for_attr_value(close_blanks, 'date', match)  # will return None if not found

        if type(self.blank) not in (GcRun, type(None)):
            msg = 'Provided blank was not of type GcRun or NoneType'
            raise TypeError(msg)

        if self.blank is None:
            self._default_to_pass_values(session)
            return

        if self.blank:
            blank_peaks = self.blank.compounds

            if not blank_peaks:
                self._default_to_pass_values(session)
                return
            else:
                for peak in self.compounds:
                    if peak.name in compounds_to_subtract:  # only blank-subtract VOCs (or a given subset)
                        matched_blank_peak = search_for_attr_value(blank_peaks, 'name', peak.name)

                        if matched_blank_peak:
                            self._subtract_peak(peak, matched_blank_peak)
                        else:
                            peak.corrected_pa = peak.pa  # pass the value if no match
                    else:
                        peak.corrected_pa = peak.pa  # pass the value if it's not a subtracted peak

        session.merge(self)
        return


class JoinedMeta(type(BlankSubtractedMixin), type(Base)):
    pass


class GcRun(Base, BlankSubtractedMixin, metaclass=JoinedMeta):
    """
    A complete, successful run on the GC. Contains a LogFile, Integration by relation.

    GcRuns are the main workhorse of the Zugspitze data. When a LogFile from LabView, and an Integration result from
    Agilent's GC software are matched, a GcRun is created and the Integration, all it's compounds, and the LogFile are
    related to the GcRun. Creating a GcRun is the largest step in achieving a quantfied sample as it contains almost all
    the necessary data to quantify a sample upon creation. It only needs a working standard (with valid Quantifications)
    in order to be quantified.
    """
    __tablename__ = 'gcruns'

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, unique=True)
    type = Column(Integer)
    quantified = Column(Boolean)

    log = relationship('LogFile', uselist=False, back_populates='run')
    integration = relationship('Integration', uselist=False, back_populates='run')

    standard_id = Column(Integer, ForeignKey('standards.id'))
    standard = relationship('Standard', back_populates='run')

    compounds = relationship('Compound', back_populates='run')

    data = relationship('Datum', uselist=False, back_populates='run')

    working_std_id = Column(Integer, ForeignKey('gcruns.id'))
    working_std = relationship('GcRun', foreign_keys=[working_std_id], remote_side=[id])

    blank_id = Column(Integer, ForeignKey('gcruns.id'))
    blank = relationship('GcRun', foreign_keys=[blank_id], remote_side=[id])

    def __init__(self, log, integration):
        """
        Create a GcRun with a date-matched LogFile and Integration.

        When created, a GcRun relates itself to the LogFile and Integration, then co-relates all Compounds, Integrations
        and LogFiles. LogFiles and Integrations are then set to status='married' to make them ineligible for future
        matching.

        :param LogFile log: LogFile with a date that matches (within tolerances) the Integration supplied
        :param Integration integration: Integration with a date that matches (within tolerances) the LogFile supplied
        """
        self.log = log
        self.integration = integration
        self.date = log.date
        self.type = log.sample_type
        self.quantified = False
        self.compounds = integration.compounds

        log.integration = integration  # relate all relevant data when joined
        integration.log = log
        log.compounds = integration.compounds

        log.status = 'married'
        integration.status = 'married'

    def quantify(self):
        """
        Attempt to calculate mixing ratios for all compounds related to this GcRun.

        If no Standard has been related to this GcRun, exit and print warning. Otherwise, use the Standard's
        Quantifications and run metadata such as samples and flows to calculate a mixing ratio for this GcRun.

        The mixing ratio is the response ratio (sample / standard) mutliplied by the
        certified value in that standard, normalized for a 2500s, 2.5V sample volume.

        :return: None
        """
        if not self.standard:
            print(f'No standard to quantify GcRun for date {self.date}.')
            return None

        for quant in self.standard.quantifications:
            if quant.value is None:
                continue

            cpd = search_for_attr_value(self.compounds, 'name', quant.name)

            if self.working_std is None:
                print(f'No working standard found for GcRun {self.date}')
                return None
            else:
                if not cpd or cpd.corrected_pa is None:
                    # print(f'No {quant.name} found in compounds for GcRun {self.date}.')
                    continue
                else:
                    ws_compound = search_for_attr_value(self.working_std.compounds, 'name', quant.name)

                    if not ws_compound:
                        print(f'No working standard compound found for {quant.name} in GcRun {self.date}')
                        continue

                    if ws_compound.corrected_pa is not None:
                        if ws_compound.corrected_pa is not 0:
                            cpd.mr = (
                                    ((cpd.corrected_pa / ws_compound.corrected_pa) * 2500 * 2.5 * quant.value)
                                    / (self.log.sample_time * self.log.sample_flow)
                            )
                    # mixing ratio is the response ratio (sample / standard) mutliplied by the
                    # certified value in that standard, normalized for a 2500s, 2.5V sample volume

                    else:
                        print(f'No working standard value found for compound {quant.name} in GcRun {self.date}')
                        continue

        self.quantified = 1


class Datum(Base):
    """
    Unused data type meant to be a more finalized version of a GcRun.
    """
    __tablename__ = 'data'

    id = Column(Integer, primary_key=True)

    integration = relationship('Integration', uselist=False, back_populates='data')
    log = relationship('LogFile', uselist=False, back_populates='data')

    run_id = Column(Integer, ForeignKey('gcruns.id'))
    run = relationship('GcRun', uselist=False, foreign_keys=[run_id], back_populates='data')

    def __init__(self):
        """Do nothing."""
        pass


class OldData(Base):
    """
    A lightweight, persisted container for data from a previous iteration of the project.

    Originally loaded in from a result spreadsheet instances of OldData are results from the project prior to 2018.
    Used for plotting only.
    """
    __tablename__ = 'olddata'
    __tableargs__ = (UniqueConstraint('name', 'date', name='NameDate'))

    id = Column(Integer, primary_key=True)
    name = Column(String)
    date = Column(DateTime)
    mr = Column(Float)

    def __init__(self, name, date, mr):
        """
        Create an instance of OldData to be persisted.

        :param str name: compound name
        :param datetime date: date sample was collected
        :param float mr: mixing ratio in parts per trillion by volume (pptv)
        """
        self.name = name
        self.date = date
        self.mr = mr
