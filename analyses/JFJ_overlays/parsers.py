import json
from collections import namedtuple
from datetime import datetime

from finalization.runtime import get_all_final_data_as_dict
from processing.constants import ALL_COMPOUNDS
from settings import CORE_DIR, JSON_PUBLIC_DIR
from plotting import create_monthly_ticks, MixingRatioPlot

FULL_START_DATE = datetime(2013, 1, 1)
NEW_START_DATE = datetime(2018, 1, 1)
END_DATE = datetime(2021, 1, 1)

COMPOUND_NAME_LOOKUP = {
    'methyl_chloride': 'CH3Cl',
    'methyl_bromide': 'CH3Br',
    'chloroform': 'CHCl3',
    'perchloroethylene': 'PCE',
    'methyl_chloroform': 'CH3CCl3'
}


def clean_flagged_data(conv, field, clean=False):
    """
    Use the given converter on field, and except ValueErrors as returning None
    ValueErrors will occur when values are flagged, eg conv('12.11P') will fail and return None for that value
    :param conv:
    :param field:
    :param clean: if False, don't strip data field on ValueError, just return None; otherwise strip and return float
    :return:
    """
    try:
        return conv(field.strip())
    except ValueError:
        return None if not clean else conv(field.strip().rstrip('P'))


def read_jfj_all_compounds_file(filepath='JFJ.txt', clean=False):
    converters = [lambda x, f=func: f(x) for func in
                  (float, int, int, int, int, int, *([float] * 40))]

    with open(filepath, 'r') as file:
        t = namedtuple('data', [fieldname.strip().replace('-', '_') for fieldname in next(file).split()])

        data = [
            t(*[clean_flagged_data(conv, field, clean) for field, conv in zip(line.split(), converters)])
            for line in file
        ]

    jfj_data = dict.fromkeys(['date'] + list(ALL_COMPOUNDS), None)

    for k in jfj_data:
        jfj_data[k] = []

    for d in data:
        jfj_data['date'].append(datetime(d.YYYY, d.MM, d.DD, d.hh, d.min, 0))

        for compound in ALL_COMPOUNDS:
            # get the name if there's an alias, otherwise use the name
            compound_looked_up = COMPOUND_NAME_LOOKUP.get(compound, compound)
            datum = getattr(d, compound_looked_up.replace('-', '_'), None)
            jfj_data[compound].append(datum)

    empty = []
    for k, v in jfj_data.items():
        if not any(v):
            empty.append(k)

    for k in empty:
        del jfj_data[k]

    return jfj_data


def read_jfj_cfc_file(filepath='JFJ_CFC_Helmig_2020.txt', clean=False):
    converters = [lambda x, f=func: f(x) for func in
                  (int, int, int, int, int, *([float] * 7))]

    with open(filepath, 'r') as file:
        for i in range(7):
            next(file)  # skip header lines until data header

        t = namedtuple('data', [fieldname.strip().replace('-', '_') for fieldname in next(file).split(',')])

        data = [
            t(*[clean_flagged_data(conv, field, clean) for field, conv in zip(line.split(','), converters)])
            for line in file
        ]

    jfj_data = dict.fromkeys(['date'] + list(ALL_COMPOUNDS), None)

    for k in jfj_data:
        jfj_data[k] = []

    for d in data:
        jfj_data['date'].append(datetime(d.year, d.month, d.day, d.hour, d.min, 0))

        for compound in ALL_COMPOUNDS:
            # get the name if there's an alias, otherwise use the name
            compound_looked_up = COMPOUND_NAME_LOOKUP.get(compound, compound)
            datum = getattr(d, compound_looked_up.replace('-', '_'), None)
            jfj_data[compound].append(datum)

    empty = []
    for k, v in jfj_data.items():
        if not any(v):
            empty.append(k)

    for k in empty:
        del jfj_data[k]

    return jfj_data
