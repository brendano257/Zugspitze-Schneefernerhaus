def read_log_file(path):
    """
    Parse a LabView log file and return a dictionary of the parameters.

    Parses the text of a file line-by-line according to how they're written. Several values present in only newer
    log files are attempted and excepted as None. Failure to parse one of those lines will pass and return the
    dictionary as-is. The output of this is designed to and must return a dictionary such that:
    LogFile(**read_log_file(file)) creates a LogFile without error.

    :param Path path: path to the file to be read.
    :return dict: returns a dictionary containing all logged parameters
    """
    data = path.read_text().split('\n')

    logdata = {}
    logdata['date'] = datetime.strptime(data[18].split('\t')[0], '%Y%j%H%M%S')
    logdata['sample_time'] = data[0].split('\t')[1]
    logdata['sample_flow'] = data[1].split('\t')[1]
    logdata['sample_type'] = data[2].split('\t')[1]
    logdata['backflush_time'] = data[3].split('\t')[1]
    logdata['desorb_temp'] = data[4].split('\t')[1]
    logdata['flashheat_time'] = data[5].split('\t')[1]
    logdata['inject_time'] = data[6].split('\t')[1]
    logdata['bakeout_temp'] = data[7].split('\t')[1]
    logdata['bakeout_time'] = data[8].split('\t')[1]
    logdata['carrier_flow'] = data[9].split('\t')[1]
    logdata['sample_flow_act'] = data[20].split('\t')[1]
    logdata['sample_num'] = data[10].split('\t')[1]
    logdata['ads_trap'] = data[12].split('\t')[1]
    logdata['sample_p_start'] = data[13].split('\t')[1]
    logdata['sample_p_during'] = data[19].split('\t')[1]
    logdata['gcheadp_start'] = data[14].split('\t')[1]
    logdata['gcheadp_during'] = data[31].split('\t')[1]
    logdata['wt_sample_start'] = data[15].split('\t')[1]
    logdata['wt_sample_end'] = data[21].split('\t')[1]
    logdata['ads_a_sample_start'] = data[16].split('\t')[1]
    logdata['ads_b_sample_start'] = data[17].split('\t')[1]
    logdata['ads_a_sample_end'] = data[22].split('\t')[1]
    logdata['ads_b_sample_end'] = data[23].split('\t')[1]
    logdata['trap_temp_fh'] = data[24].split('\t')[1]
    logdata['trap_temp_inject'] = data[26].split('\t')[1]
    logdata['trap_temp_bakeout'] = data[28].split('\t')[1]
    logdata['battv_inject'] = data[27].split('\t')[1]
    logdata['battv_bakeout'] = data[29].split('\t')[1]
    logdata['gc_start_temp'] = data[25].split('\t')[1]
    logdata['gc_oven_temp'] = data[32].split('\t')[1]
    logdata['wt_hot_temp'] = data[30].split('\t')[1]
    logdata['sample_code'] = data[18].split('\t')[0]

    logdata['mfc1_ramp'] = None
    logdata['trapheatout_flashheat'] = None
    logdata['trapheatout_inject'] = None
    logdata['trapheatout_bakeout'] = None

    try:
        logdata['mfc1_ramp'] = data[33].split('\t')[1]
        logdata['trapheatout_flashheat'] = data[34].split('\t')[1]
        logdata['trapheatout_inject'] = data[35].split('\t')[1]
        logdata['trapheatout_bakeout'] = data[36].split('\t')[1]
    except IndexError:
        pass

    return logdata


def read_daily_line(line):
    """
    Parses one line from a DailyFile and returns a dictionary containing the parameters by name.

    One line is parsed such that Daily(**read_daily_line(line)) creates a Daily instance successfully. Values are all
    returned as floats.

    :param str line: the line to be read, including whitespace since it will be parsed by splitting on tabs
    :return: dict
    """
    dailydata = {}
    ls = line.split('\t')
    try:
        dailydata['date'] = datetime.strptime(line.split('\t')[0].split('.')[0], '%y%j%H%M')
        dailydata['ads_xfer_temp'] = float(ls[1])
        dailydata['valves_temp'] = float(ls[2])
        dailydata['gc_xfer_temp'] = float(ls[3])
        dailydata['ebox_temp'] = float(ls[4])
        dailydata['catalyst_temp'] = float(ls[5])
        dailydata['molsieve_a_temp'] = float(ls[6])
        dailydata['molsieve_b_temp'] = float(ls[7])
        dailydata['inlet_temp'] = float(ls[8])
        dailydata['room_temp'] = float(ls[9])
        dailydata['v5'] = float(ls[10])
        dailydata['mfc1'] = float(ls[11])
        dailydata['mfc2'] = float(ls[12])
        dailydata['mfc3'] = float(ls[13])
        dailydata['he_pressure'] = float(ls[14])
        dailydata['linep'] = float(ls[15])
        dailydata['zerop'] = float(ls[16])
    except ValueError:
        print('ValueError while reading line from DailyFile.')

    return dailydata


def read_daily_file(filepath):
    """
    Parses an entire file of Daily data and returns a list of Daily objects.

    :param Path filepath: path to the file to be read
    :return list: returns a list of Daily instances
    """
    contents = filepath.read_text().split('\n')
    contents = [line for line in contents if line]

    dailies = []
    daily_dates = []
    for line in contents:
        try:
            d = Daily(**read_daily_line(line))
            if d.date not in daily_dates:  # prevent duplicately dated lines from the same file (LabView coding issue)
                dailies.append(d)
                daily_dates.append(d.date)
        except TypeError:
            print(f'Daily file {filepath.name} in {filepath.parts[-2]} could not be read and was skipped.')

    return dailies


def read_gcms_file(path):
    """
    Parses an integration_results.txt file such that Integration(**read_gcms_file(path)) creates an Integration.

    Reads metadata from the file header, then parses the response information by compound before returning a
    dictionary containing all the necessary information to create an Integration.

    :param Path path: filepath to be parsed
    :return dict: dictionary containing all the metadata and data for an Integration
    """
    # should parse standard files and assign name separately
    contents = path.read_text().split('\n')

    gcmsdata = {
        'filename': path.parts[-2],
        'date': datetime.strptime(contents[4].split(' : ')[1].strip(), '%d %b %Y %H:%M'),
        'path': path,
        'quant_time': datetime.strptime(contents[10].split(': ')[1].strip(), '%b %d %H:%M:%S %Y'),
        'method': contents[11].split(' : ')[1].strip()
    }

    compounds = []
    for line in contents[20:92]:
        ls = line.split()

        if len(ls) > 6:
            try:
                name = ls[1]
                rt = float(ls[2])
                ion = int(ls[3])
                pa = int(ls[4])
                compounds.append(Compound(name, rt, ion, pa))
            except Exception:
                print(f'GCMS file for {gcmsdata["filename"]} was not processed.')

    gcmsdata['compounds'] = compounds

    return gcmsdata
