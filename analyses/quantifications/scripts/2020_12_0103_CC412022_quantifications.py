"""
A sequence of standards were run over three days to quantify and compare CC412022 vs SX3555.

The sequence was: (CC412022, SX3555, Blank2500);
    which was run after normal runs for three days (2020-12-1 --> 2020-12-3).
"""

from datetime import datetime

from reporting import create_multiday_quant_report

days_with_standards = [datetime(2020, 12, x) for x in (1, 2, 3)]
create_multiday_quant_report('CC412022', 'SX3555', days_with_standards)

days_with_standards = [datetime(2020, 12, x) for x in (1, 2, 3)]
create_multiday_quant_report('SX3555', 'CC412022', days_with_standards)
