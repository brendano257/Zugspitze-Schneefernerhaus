__all__ = ['ALL_COMPOUNDS', 'LOG_ATTRS', 'DAILY_ATTRS']

# list of all compounds processed by system; used frequently throughout for plotting etc
ALL_COMPOUNDS = ('PFC-116', 'ethene', 'SF6', 'CFC-13', 'ethane', 'SO2F2', 'HFC-143a', 'PFC-218', 'HFC-125', 'OCS',
                 'H-1301', 'HFC-134a', 'HFC-152a', 'HCFC-22', 'CFC-115', 'propene', 'methyl_chloride', 'propane',
                 'propyne*', 'methanol', 'PFC-318', 'CFC-12', 'acetaldehyde', 'HCFC-142b', 'methyl_bromide', 'HCFC-124',
                 'HFC-245fa', 'methyl_formate', 'i-butane', 'iso-butene', '1,3-butadiene', '1-butene', 'H-1211',
                 'ethanol', 'trans-2-butene', 'CFC-114', 'n-butane', 'cis-2-butene', 'CH2Cl2', 'acetone',
                 'methyl_iodide', 'HFC-365mfc', 'CFC-11', 'HCFC-141b', 'i-pentane', '1-pentene', 'isoprene',
                 'trans-2-pentene', 'cis-2-pentene', 'n-pentane', 'CFC-113', 'H-2402', 'chloroform', '2-methylpentane',
                 '3-methylpentane', 'CH2Br2', 'hexane', 'benzene', 'methyl_chloroform', 'CCl4', 'cyclohexane',
                 'n-heptane', 'toluene', 'perchloroethylene', 'iso-octane', 'CHBr3', 'octane', 'ethylbenzene',
                 'm-xylene', 'o-xylene', '1,2,4-trimethylbenzene', '1,3,5-trimethylbenzene')

# list of all attributes to a LogFile object, sans date; used to simplify LogFile init and other bulk operations
LOG_ATTRS = ('sample_time', 'sample_flow', 'sample_type', 'backflush_time', 'desorb_temp', 'flashheat_time',
             'inject_time', 'bakeout_temp', 'bakeout_time', 'carrier_flow', 'sample_flow_act', 'sample_num', 'ads_trap',
             'sample_p_start', 'sample_p_during', 'gcheadp_start', 'gcheadp_during', 'wt_sample_start', 'wt_sample_end',
             'ads_a_sample_start', 'ads_b_sample_start', 'ads_a_sample_end', 'ads_b_sample_end', 'trap_temp_fh',
             'trap_temp_inject', 'trap_temp_bakeout', 'battv_inject', 'battv_bakeout', 'gc_start_temp', 'gc_oven_temp',
             'wt_hot_temp', 'sample_code', 'mfc1_ramp', 'trapheatout_flashheat', 'trapheatout_inject',
             'trapheatout_bakeout', 'status')

# list of all attributes to a Daily object; used to simplify Daily init and other bulk operations
DAILY_ATTRS = ('date', 'ads_xfer_temp', 'valves_temp', 'gc_xfer_temp', 'ebox_temp', 'catalyst_temp', 'molsieve_a_temp',
               'molsieve_b_temp', 'inlet_temp', 'room_temp', 'v5', 'mfc1', 'mfc2', 'mfc3', 'he_pressure', 'linep',
               'zerop')

# detection limits for any compounds given (in pptv)
DETECTION_LIMITS = {
    'hexane': .5,
    'isoprene': 1,
    'benzene': 1,
    'toluene': 1
}
