"""
A sequence of standards were run over three days to quantify and compare CC412022 vs CC464566.

The sequence was: (CC412022, CC464566, Blank2500);
    which was run after normal runs for three days (2020-12-4 --> 2020-12-6).
"""

from datetime import datetime

from reporting import create_multiday_quant_report

days_with_standards = [datetime(2020, 12, x) for x in (4, 5, 6)]
create_multiday_quant_report('CC412022', 'CC464566', days_with_standards)

days_with_standards = [datetime(2020, 12, x) for x in (4, 5, 6)]
create_multiday_quant_report('CC464566', 'CC412022', days_with_standards)
