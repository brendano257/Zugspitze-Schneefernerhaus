from processing.constants import EBAS_REPORTING_COMPOUNDS


SEASONAL_CYCLE_COMPOUNDS = frozenset((
    'ethane', 'methyl_chloride', 'propane', 'i-butane', 'n-butane', 'CH2Cl2', 'i-pentane',
    'n-pentane', 'CH2Br2', 'hexane', 'benzene', 'toluene', 'CHBr3',
))

MEDIAN_10_COMPOUNDS = frozenset((
    'HCFC-141b', 'H-1301', 'HFC-143a', 'HCFC-124', 'PFC-116', 'CFC-11', 'methyl_chloroform', 'CCl4', 'SO2F2',
     'CFC-12', 'HFC-125', 'HCFC-142b', 'OCS', 'CFC-115', 'CFC-13', 'HCFC-22', 'PFC-318',
     'H-2402', 'PFC-218', 'H-1211', 'methyl_bromide', 'CFC-113',  'HFC-245fa',
    'CFC-114', 'HFC-365mfc', 'HFC-134a'
))

TWENTY_ONE_DAY = frozenset((
    'OCS', 'HFC-141b', 'HFC-142b'
))

MEDIAN_25_COMPOUNDS = frozenset((
        'perchloroethylene', 'methyl_iodide', 'HFC-152a', 'chloroform',
))

NONE = frozenset((
    'isoprene',
))

ALL = SEASONAL_CYCLE_COMPOUNDS.union(MEDIAN_10_COMPOUNDS).union(MEDIAN_25_COMPOUNDS).union(NONE)

# module won't run if all compounds aren't accounted for in any group; just a safety check
if not ALL == frozenset(EBAS_REPORTING_COMPOUNDS):
    print(sorted(ALL))
    print(sorted(EBAS_REPORTING_COMPOUNDS))
    ValueError('All compounds were not represented in filter categories.')

if __name__ == '__main__':
    pass
