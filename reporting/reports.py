import statistics as s
from datetime import datetime
from collections import OrderedDict

import xlsxwriter
import pandas as pd

from xlsxwriter.utility import xl_rowcol_to_cell, xl_range

from IO.db.models import Compound, GcRun, Standard
from IO.db import connect_to_db
from settings import CORE_DIR, DB_NAME
from utils.core import search_for_attr_value
from processing import get_mr_from_run, ALL_COMPOUNDS

__all__ = ['get_df_with_filters', 'write_df_to_excel', 'compile_quant_report', 'compile_enhancement_comparison']


def get_df_with_filters(use_mrs, filters=None, compounds=None):
    """
    Retrieves a dataframe from the database of all mixing ratios or peak areas for all compounds with optional filters.

    TODO: Generalize even more. This could accept filter, additional params (date, mr, ...?), etc.

    Retrieves mixing ratios (or peak areas if use_mrs=False) for all compounds, and can be filtered with additional
    expressions. Expressions are added on a per-compound basis, so filtering for specific compounds is not yet possible.
    Returned DataFrame has a datetimeindex of GcRun dates, and a column per compound.

    :param bool use_mrs: Boolean specifying if mixing ratios should be returned. False will return peak areas instead
    :param list filters: List containing Sqlalchemy filter expressions, eg [GcRun.type == 1, GcRun.quantified == 1]
        **Filters are added sequentially and should be given in their intended order
    :param list compounds: list of compounds to query for, defaults to all quantified compounds if not given
    :return pd.DataFrame:
    """
    engine, session = connect_to_db(DB_NAME, CORE_DIR)

    if not compounds:
        standard = (session.query(Standard)
                    .filter(Standard.name == 'quantlist')
                    .one())  # retrieve full list of compounds that are quantified from the database

        compounds = [q.name for q in standard.quantifications]

    # data will be unpacked into a dictionary of dates, where each date holds another OrderedDict of compounds:mrs
    dates = OrderedDict()

    mr_or_pa = Compound.mr if use_mrs else Compound.pa

    for compound in compounds:
        # get all ambient data that's not filtered
        results = (session.query(mr_or_pa, GcRun.date)
                   .join(GcRun, GcRun.id == Compound.run_id)
                   .filter(Compound.filtered == False)
                   .filter(Compound.name == compound))

        if filters:
            for expression in filters:
                results = results.filter(expression)

        results = results.order_by(GcRun.date).all()

        #  append to or create list with the results for that compound and date
        for r in results:
            try:
                dates[r.date][compound] = r[0]  # add the compound as the key and mr/pa as the value
            except KeyError:
                dates[r.date] = OrderedDict([(compound, r[0])])  # if date doesn't exist yet, create it's ODict

    # re-sort based on date, for safety
    dates = OrderedDict(sorted(dates.items()))

    for date, results in dates.items():
        dates[date] = OrderedDict(
            sorted(results.items(),
                   # sort by key-value pair, using the key's index in the list of compounds to determine their order
                   key=lambda kv_pair: compounds.index(kv_pair[0]))
        )

    return pd.DataFrame.from_dict(dates, orient='index')


def write_df_to_excel(df, header=None, filename_end=None, bold_row_0=False, bold_col_0=False):
    """
    Writes a dataframe with a datetime index to a file.

    Takes in an optional header and extra label for the filename.
    The first rows and columns can be bolded in the saved excel file with bold_[row/col]_0.

    TODO: Needs to take a callback that does more prior to saving, ie adding charts after data is written

    :param pd.DataFrame df: Pandas dataframe to write to file
        **must have a datetime index
    :param list header: list of headers to write to the file if desired. Usually, it's ['date'] + df.columns.tolist()
    :param str filename_end: a string to append to the filename if desired, otherwise the current date is used only
    :param bool bold_row_0: True to bold the first row, defaults to false/non-bold
    :param bool bold_col_0: True to bold the first column, defaults to false/non-bold
    :return: None; writes to file
    """

    from xlsxwriter import Workbook

    df.index = df.index.map(lambda x: datetime.strftime(x, '%Y-%m-%d %H:%M:%S'))  # change index to ISO8601 time

    datestamp = datetime.now().strftime("%Y_%m_%d")
    filename = f"{datestamp}_{filename_end}.xlsx" if filename_end else f"{datestamp}_data.xlsx"

    workbook = Workbook(filename)
    workbook.nan_inf_to_errors = True
    worksheet = workbook.add_worksheet('Data')

    row_0_fmt = workbook.add_format({'bold': bold_row_0})  # create row formats to apply based on inputs
    col_0_fmt = workbook.add_format({'bold': bold_col_0})

    if header:
        for col, head in enumerate(header):
            worksheet.write(0, col, head, row_0_fmt)

    row_count = 1 if header else 0  # start on row 1 if a header was provided

    for row in df.iterrows():
        col_count = 1
        worksheet.write(row_count, 0, row[0], col_0_fmt)  # write index to first col

        for col in row[1]:  # row[1] is all values that aren't the index - pandas df.iterrows() specific
            worksheet.write(row_count, col_count, col)
            col_count += 1

        row_count += 1

    workbook.close()


def compile_quant_report(quantifications, sample_name, standard_name, sample_certs, date=None):
    """
    Compiles a summary and detailed sheet of a set of quantifications in the same workbook.

    Given a set of quantifications, this creates one sheet with the results of each run side-by-side, with the mean,
    median, and relative stdev given. A second sheet contains the provided values for the standard, mean of the three
    quantified runs from the other tab, and the relative difference from the provided/certified values.

    :param list quantifications:  list of quantified SampleQuants
    :param str sample_name: str name of the standard being quantified
    :param str standard_name: str name of the standard the above was quantified by
    :param list sample_certs:  list of Quantification objects, usually from Standard.quantifications for [sample_name]
    :param datetime date: optional date to substitute for datetime.now(), will appear in the filename as %Y_%m_%d
    :return None: Spreadsheet is saved to working directory
    """
    if not date:
        date = datetime.now()

    date = date.strftime('%Y_%m_%d')

    book = xlsxwriter.Workbook(f'{date}_{sample_name}_qx_{standard_name}.xlsx')
    summaries = book.add_worksheet(name='Summary')
    runs = book.add_worksheet(name='Individual Runs')

    num2dec_fmt = book.add_format({'num_format': '0.00'})  # all numbers should be two decimal places
    bold_fmt = book.add_format({'bold': True})  # row/column headers are bolded
    bold_percent_fmt = book.add_format({'bold': True, 'num_format': '0.00%'})  # relative differences get bolded

    compounds = [q.name for q in sample_certs]

    dates = [q.sample.date.strftime('%Y-%m-%d %H:%M') for q in quantifications]
    runs_header = ['Compound'] + dates + ['', 'Mean', 'Median', 'Relative StDev']

    for col, head in enumerate(runs_header):
        runs.write(0, col, head, bold_fmt)

    run_row = 1
    stats_col = len(quantifications) + 2

    results = {}
    for compound in compounds:
        mrs = []

        runs.write(run_row, 0, compound, bold_fmt)  # write compound name to row header
        run_col = 1

        for q in quantifications:  # find mixing ratio, write to runs sheet and compile a list for stats of all runs
            compound_mr = get_mr_from_run(q.sample, compound)
            if compound_mr:
                runs.write(run_row, run_col, compound_mr, num2dec_fmt)
                mrs.append(compound_mr)

            run_col += 1

        if mrs:
            mean = s.mean(mrs)
            results[compound] = mean  # write means to dict for summary sheet

            stat_cells = [xl_rowcol_to_cell(run_row, stats_col + num) for num in (0, 1, 2)]
            # get A1 notation for cells to put stats in, moving over a column at a time

            range_ = xl_range(run_row, 1, run_row, len(quantifications))  # range of MR cells in this row

            # create formulae for mean, median, and relative stdev
            runs.write(stat_cells[0], f'=average({range_})', num2dec_fmt)
            runs.write(stat_cells[1], f'=median({range_})', num2dec_fmt)
            runs.write(stat_cells[2], f'=stdev({range_})/{stat_cells[0]}', bold_percent_fmt)

        run_row += 1

    summary_header = [f'Compounds in {sample_name}',
                      f'{sample_name} Certified Value',
                      f'Quantified Value (Mean: {len(quantifications)} Runs)',
                      '', 'Relative Difference']

    for col, head in enumerate(summary_header):  # write column header
        summaries.write(0, col, head, bold_fmt)

    cert_col = 1
    mr_col = 2

    for num, (compound, mr) in enumerate(results.items()):
        cert = search_for_attr_value(sample_certs, 'name', compound)
        if cert:
            cert_value = cert.value
        else:
            print(f'No cert value found for compound {compound} in {sample_name}')
            continue

        summaries.write(num + 1, 0, compound, bold_fmt)  # write compound names to row header
        summaries.write(num + 1, cert_col, cert_value, num2dec_fmt)  # write db-loaded certified values
        summaries.write(num + 1, mr_col, mr, num2dec_fmt)  # write this quant's values to third column

        cert_cell = xl_rowcol_to_cell(num + 1, cert_col)  # get A1 notation for cell formulae
        quant_cell = xl_rowcol_to_cell(num + 1, mr_col)

        if cert_value is not None:  # don't write formulae that will be #DIV/0!
            summaries.write(num + 1, 4, f'=({cert_cell}-{quant_cell})/{cert_cell}', bold_percent_fmt)

    book.close()


def compile_enhancement_comparison(low, high, compounds=None, names=('Ridgeline', 'Glass Stack'), date=None,
                                   use_mrs=False):
    """
    Creates a spreadsheet report comparing a low and high sample's relative enhancement.

    Given a sample that's expected to be low and one that's expected to be higher, this creates a single-sheet workbook
    that places the sample's mixing ratios (or peak areas if use_mrs=False), side-by-side and computes a relative
    enhancement from the lower to the higher sample using Excel formulae in the sheet.

    Two common uses are computing the enhancement from the RidgeLine inlet samples to those from the Glass Stack and
    comparing air sampled from the exterior inlets to that sampled in the interior room (Ambient, RoomAir).

    :param GcRun low: GcRun that's expected to be the lower value
        The formula is `(high-low)/low` as a percent
    :param GcRun high: GcRun the object that's expected to have higher concentrations on average
    :param list compounds: a subset of compounds to be included, defaults to all compounds if not specified
    :param tuple names: tuple names for the (low, high) samples
    :param datetime date: datetime of the samples being compared
    :param bool use_mrs: bool if False, use peak areas only, otherwise, use mixing ratios
    :return None: Spreadsheet saved in working directory
    """
    if not date:
        date = datetime.now().strftime('%Y_%m_%d')
    else:
        date = date.strftime('%Y_%m_%d')

    book = xlsxwriter.Workbook(f'{date}_{names[0].replace(" ", "")}_{names[1].replace(" ", "")}_comparison.xlsx')
    sheet = book.add_worksheet(f'Comparison {date.replace("_", "-")}')

    if use_mrs:
        num_fmt = book.add_format({'num_format': '0.00'})  # all peak area numbers should be no decimal
    else:
        num_fmt = book.add_format({'num_format': '0'})

    bold_fmt = book.add_format({'bold': True})  # row/column headers are bolded
    bold_percent_fmt = book.add_format({'bold': True, 'num_format': '0.00%'})  # relative differences get bolded

    mr_or_pa = 'Mixing Ratios' if use_mrs else 'Peak Areas'

    header = ['Compound', f'{names[0]} {mr_or_pa}', f'{names[1]} {mr_or_pa}', '', 'Relative Enhancement']

    low_col = 1
    high_col = 2
    enhance_col = 4

    for num, h in enumerate(header):
        sheet.write(0, num, h, bold_fmt)

    if not compounds:
        compounds = ALL_COMPOUNDS

    for num, comp in enumerate(compounds):
        row = num + 1
        sheet.write(row, 0, comp, bold_fmt)

        low_comp = search_for_attr_value(low.compounds, 'name', comp)
        high_comp = search_for_attr_value(high.compounds, 'name', comp)

        if low_comp:
            low_val = low_comp.corrected_pa if not use_mrs else low_comp.mr
            sheet.write(row, low_col, low_val, num_fmt)
        else:
            low_val = None

        if high_comp:
            high_val = high_comp.corrected_pa if not use_mrs else high_comp.mr
            sheet.write(row, high_col, high_val, num_fmt)
        else:
            high_val = None

        if low_val and high_val:
            low_cell = xl_rowcol_to_cell(row, low_col)
            high_cell = xl_rowcol_to_cell(row, high_col)

            sheet.write(row, enhance_col, f'=({high_cell}-{low_cell})/{low_cell}', bold_percent_fmt)

    book.close()
