"""
Creates a multi-quantification. A docstring should be similar to the below:

A sequence of standards were run over three days to quantify and compare STANDARD_ONE vs STANDARD_TWO.

The sequence was: (STANDARD_ONE, STANDARD_TWO, Blank2500);
    which was run after normal runs for three days (DATE --> DATE).
"""

from datetime import datetime

from reporting import create_multiday_quant_report

"""
Below is the first way, requiring no extra parameters.
"""
days_with_standards = [datetime(2019, 11, x) for x in (5, 6, 7)]
create_multiday_quant_report('CC416168', 'CC464566', days_with_standards)

"""
An alternative method may be necessary if one of the standards has a different name in the database.
Below is the case where CC412022 isn't listed in the database as cc412022, but as cc412022_noaa_provided
"""
days_with_standards = [datetime(2019, 12, x) for x in (20, 21, 22)]
create_multiday_quant_report('CC412022', 'SX3555', days_with_standards, alt_sample_name='cc412022_noaa_provided')
