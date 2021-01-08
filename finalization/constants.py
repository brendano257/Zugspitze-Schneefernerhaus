from processing.constants import EBAS_REPORTING_COMPOUNDS


SEASONAL_CYCLE_COMPOUNDS = frozenset((
    'ethene', 'ethane', 'propene', 'methyl_chloride', 'propane', 'i-butane', 'n-butane', 'CH2Cl2', 'i-pentane',
    'isoprene', 'n-pentane', 'CH2Br2', 'hexane', 'benzene', 'toluene', 'CHBr3'
))

MEDIAN_10_COMPOUNDS = ('PFC-116', 'SF6', 'CFC-13', 'SO2F2', 'HFC-143a', 'PFC-218', 'HFC-125', 'OCS',
                       'H-1301', 'HFC-134a', 'HFC-152a', 'HCFC-22', 'CFC-115',
                       'methanol', 'PFC-318', 'CFC-12', 'acetaldehyde', 'HCFC-142b', 'methyl_bromide', 'HCFC-124',
                       'HFC-245fa', 'methyl_formate', 'H-1211',
                       'ethanol', 'trans-2-butene', 'CFC-114', 'cis-2-butene', 'acetone',
                       'methyl_iodide', 'HFC-365mfc', 'CFC-11', 'HCFC-141b',
                       'trans-2-pentene', 'cis-2-pentene', 'CFC-113', 'H-2402', 'chloroform', '2-methylpentane',
                       '3-methylpentane', 'methyl_chloroform', 'CCl4', 'cyclohexane',
                       'n-heptane', 'perchloroethylene', 'iso-octane', 'octane', 'ethylbenzene',
                       'm-xylene', 'o-xylene', '1,2,4-trimethylbenzene', '1,3,5-trimethylbenzene')

MEDIAN_25_COMPOUNDS = ('PFC-116', 'ethene', 'SF6', 'CFC-13', 'ethane', 'SO2F2', 'HFC-143a', 'PFC-218', 'HFC-125', 'OCS',
                       'H-1301', 'HFC-134a', 'HFC-152a', 'HCFC-22', 'CFC-115', 'propene', 'methyl_chloride', 'propane',
                       'propyne*', 'methanol', 'PFC-318', 'CFC-12', 'acetaldehyde', 'HCFC-142b', 'methyl_bromide', 'HCFC-124',
                       'HFC-245fa', 'methyl_formate', 'i-butane', 'iso-butene', '1,3-butadiene', '1-butene', 'H-1211',
                       'ethanol', 'trans-2-butene', 'CFC-114', 'n-butane', 'cis-2-butene', 'CH2Cl2', 'acetone',
                       'methyl_iodide', 'HFC-365mfc', 'CFC-11', 'HCFC-141b', 'i-pentane', '1-pentene', 'isoprene',
                       'trans-2-pentene', 'cis-2-pentene', 'n-pentane', 'CFC-113', 'H-2402', 'chloroform', '2-methylpentane',
                       '3-methylpentane', 'CH2Br2', 'hexane', 'benzene', 'methyl_chloroform', 'CCl4', 'cyclohexane',
                       'n-heptane', 'toluene', 'perchloroethylene', 'iso-octane', 'CHBr3', 'octane', 'ethylbenzene',
                       'm-xylene', 'o-xylene', '1,2,4-trimethylbenzene', '1,3,5-trimethylbenzene')