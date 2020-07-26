/**
 * Filenames or API endpoints to get JSON data must be defined.
 *
 * These were not typed; something like the below in Python should be helpful:
 * for file in sorted(os.listdir()):
 *  print(f'"{file.split("_")[0]}": "data/{file}",')
 */

const JSONFiles = {
    "CCl4": "data/CCl4_filtered.json",
    "CFC-113": "data/CFC-113_filtered.json",
    "CFC-114": "data/CFC-114_filtered.json",
    "CFC-115": "data/CFC-115_filtered.json",
    "CFC-11": "data/CFC-11_filtered.json",
    "CFC-12": "data/CFC-12_filtered.json",
    "CFC-13": "data/CFC-13_filtered.json",
    "CH2Br2": "data/CH2Br2_filtered.json",
    "CH2Cl2": "data/CH2Cl2_filtered.json",
    "CHBr3": "data/CHBr3_filtered.json",
    "H-1211": "data/H-1211_filtered.json",
    "H-1301": "data/H-1301_filtered.json",
    "H-2402": "data/H-2402_filtered.json",
    "HCFC-124": "data/HCFC-124_filtered.json",
    "HCFC-141b": "data/HCFC-141b_filtered.json",
    "HCFC-142b": "data/HCFC-142b_filtered.json",
    "HCFC-22": "data/HCFC-22_filtered.json",
    "HFC-125": "data/HFC-125_filtered.json",
    "HFC-134a": "data/HFC-134a_filtered.json",
    "HFC-143a": "data/HFC-143a_filtered.json",
    "HFC-152a": "data/HFC-152a_filtered.json",
    "HFC-245fa": "data/HFC-245fa_filtered.json",
    "HFC-365mfc": "data/HFC-365mfc_filtered.json",
    "OCS": "data/OCS_filtered.json",
    "PFC-116": "data/PFC-116_filtered.json",
    "PFC-218": "data/PFC-218_filtered.json",
    "PFC-318": "data/PFC-318_filtered.json",
    "SF6": "data/SF6_filtered.json",
    "SO2F2": "data/SO2F2_filtered.json",
    "benzene": "data/benzene_filtered.json",
    "chloroform": "data/chloroform_filtered.json",
    "ethane": "data/ethane_filtered.json",
    "hexane": "data/hexane_filtered.json",
    "i-butane": "data/i-butane_filtered.json",
    "i-pentane": "data/i-pentane_filtered.json",
    "isoprene": "data/isoprene_filtered.json",
    "methyl_bromide": "data/methyl_bromide_filtered.json",
    "methyl_chloride": "data/methyl_chloride_filtered.json",
    "methyl_chloroform": "data/methyl_chloroform_filtered.json",
    "methyl_iodide": "data/methyl_iodide_filtered.json",
    "n-butane": "data/n-butane_filtered.json",
    "n-pentane": "data/n-pentane_filtered.json",
    "perchloroethylene": "data/perchloroethylene_filtered.json",
    "propane": "data/propane_filtered.json",
    "toluene": "data/toluene_filtered.json",
};

// list of compounds to include (should match the keys for files/api endpoints
const compounds = Object.keys(JSONFiles);

// all potential keys to plot on the y axis
const xOptions = {
    'date': d => d.date
}

const yOptions = {
    'mixing ratio': d => d.mr,
    'peak area': d => d.pa,
    'corrected peak area': d => d.cpa,
    'retention time': d => d.rt,
}

// object key to use for y-data when plotting
const dataXDefault = xOptions['date'];

// object key to use for y-data when plotting
const dataYDefault = yOptions['mixing ratio'];

// difference of "UTC/Epoch" times provided in JSON from real UTC
const UTCCorrection = 1;

// C formatter for time, passed to d3.timeFormat() for the x axis labels
const CTimeFormat = '%Y-%m-%d %H:%M';

// Limit to be imposed on zooming for the x-axis
const xZoomLimit = 24 * 60 * 60 * 1000;  // day in ms

// width of the plot
const width = 800;

// height of the plot
const height = 450;

// value to round all y-axis labels to
const yAxisRound = 1;

/**
 *
 */
function toolTipText(plot, d) {
    // report date, value, rt, pa, mr AND human readable sample code in the tooltip (split each portion by a space)
    // all things get rounded to 3 decimals, just in case

    return `<strong>${plot.formatISODate(d.date)}</strong><br>
            <strong>RT: </strong>${Math.floor(d.rt * 1000) / 1000}<br>
            <strong>PA: </strong>${Math.floor(d.pa * 1000) / 1000}<br>
            <strong>CPA: </strong>${Math.floor(d.cpa * 1000) / 1000}<br>
            <strong>MR: </strong>${Math.floor(d.mr * 1000) / 1000}<br>
            <strong>${d.file}</strong><br>
            `;
}

// margins for the plot
const plotMargins = {
    top: 10,
    bottom: 75,
    right: 20,
    left: 75
};

// necessary elements in the DOM
const plotDOMElements = {
    selector: document.getElementById('compound-select'),
    ySelector: document.getElementById('y-value-select'),
    xSelector: document.getElementById('x-value-select'),
    header: document.getElementById('plotHeader'),
    xMin: document.getElementById('xMin'),
    xMax: document.getElementById('xMax'),
    yMin: document.getElementById('yMin'),
    yMax: document.getElementById('yMax')
};

// necessary buttons in the DOM
const DOMButtons = {
    saveSelect: document.getElementById('btn-saveSelect'),
    downloadJSON: document.getElementById('btn-downloadJSON'),
    clearPlot: document.getElementById('btn-clearPlot'),
    clearAll: document.getElementById('btn-clearAll'),
    resetAxes: document.getElementById('btn-resetAxes'),
    undoZoom: document.getElementById('btn-undoZoom')
};

// necessary CSS elements to class and format items in the DOM
const CSS = {
    canvasID: '#dataSelectorCanvas',
    selectedTextBoxID: '#selectedTextBox',
    toolTipClass: 'tooltip',
    dataPointClass: 'data-point',
    jsonTextBoxID: '#jsonTextBox',
    jsonListID: '#jsonList',
    selectedOutlierClass: 'selectedOutlier',
    axisLinesClass: 'axisLines',
    axisTextClass: 'axisText'
};

DataSelectorUI = new DataSelector(
    compounds,
    dataXDefault,
    xOptions,
    dataYDefault,
    yOptions,
    CTimeFormat,
    UTCCorrection,
    width,
    height,
    xZoomLimit,
    yAxisRound,
    CSS,
    plotMargins,
    plotDOMElements,
    DOMButtons,
    toolTipText
);
