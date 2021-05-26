__all__ = ['ALL_COMPOUNDS', 'LOG_ATTRS', 'DAILY_ATTRS', 'DETECTION_LIMITS', 'QUANTIFIED_COMPOUNDS',
           'EBAS_REPORTING_COMPOUNDS']

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

QUANTIFIED_COMPOUNDS = ('PFC-116', 'SF6', 'CFC-13', 'ethane', 'SO2F2', 'HFC-143a', 'PFC-218', 'HFC-125', 'OCS',
                        'H-1301', 'HFC-134a', 'HFC-152a', 'HCFC-22', 'CFC-115', 'methyl_chloride', 'propane',
                        'PFC-318', 'CFC-12', 'HCFC-142b', 'methyl_bromide', 'HCFC-124', 'HFC-245fa', 'i-butane',
                        'H-1211', 'CFC-114', 'n-butane', 'CH2Cl2', 'methyl_iodide', 'HFC-365mfc', 'CFC-11', 'HCFC-141b',
                        'i-pentane', 'isoprene', 'n-pentane', 'CFC-113', 'H-2402', 'chloroform', 'CH2Br2', 'hexane',
                        'benzene', 'methyl_chloroform', 'CCl4', 'toluene', 'perchloroethylene', 'CHBr3')

EBAS_REPORTING_COMPOUNDS = ('PFC-116', 'CFC-13', 'ethane', 'SO2F2', 'HFC-143a', 'PFC-218', 'HFC-125', 'OCS',
                        'H-1301', 'HFC-134a', 'HFC-152a', 'HCFC-22', 'CFC-115', 'methyl_chloride', 'propane',
                        'PFC-318', 'CFC-12', 'HCFC-142b', 'methyl_bromide', 'HCFC-124', 'HFC-245fa', 'i-butane',
                        'H-1211', 'CFC-114', 'n-butane', 'CH2Cl2', 'methyl_iodide', 'HFC-365mfc', 'CFC-11', 'HCFC-141b',
                        'i-pentane', 'isoprene', 'n-pentane', 'CFC-113', 'H-2402', 'chloroform', 'CH2Br2', 'hexane',
                        'benzene', 'methyl_chloroform', 'CCl4', 'toluene', 'perchloroethylene', 'CHBr3')

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

PROPOSED_AUTOMATIC_DETECTION_LIMITS = {
    "PFC-116": 0.299,
    "CFC-13": 0.194,
    "ethane": 161.151,
    "SO2F2": 0.142,
    "HFC-143a": 0.543,
    "PFC-218": 0.041,
    "HFC-125": 0.784,
    "OCS": 27.937,
    "H-1301": 0.116,
    "HFC-134a": 2.727,
    "HFC-152a": 0.484,
    "HCFC-22": 9.66,
    "CFC-115": 0.237,
    "methyl_chloride": 13.943,
    "propane": 7.684,
    "PFC-318": 0.057,
    "CFC-12": 6.939,
    "HCFC-142b": 0.748,
    "methyl_bromide": 0.223,
    "HCFC-124": 0.071,
    "HFC-245fa": 0.133,
    "i-butane": 0.508,
    "H-1211": 0.076,
    "CFC-114": 0.455,
    "n-butane": 0.728,
    "CH2Cl2": 2.299,
    "methyl_iodide": 0.099,
    "HFC-365mfc": 0.077,
    "CFC-11": 2.85,
    "HCFC-141b": 0.478,
    "i-pentane": 17.601,
    "isoprene": 6.005,
    "n-pentane": 0.971,
    "CFC-113": 2.753,
    "H-2402": 0.041,
    "chloroform": 0.858,
    "CH2Br2": 0.048,
    "hexane": 2.98,
    "benzene": 2.513,
    "methyl_chloroform": 0.13,
    "CCl4": 2.032,
    "toluene": 6.808,
    "perchloroethylene": 0.847,
    "CHBr3": 0.448
}
