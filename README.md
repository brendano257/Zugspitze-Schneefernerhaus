# Zugspitze-Schneefernerhaus
### A suite of data-analysis tools and processes for plotting and reporting atmospheric data from a remote station.

#### The Schneefernerhuas is a converted hotel that serves as an environmental research station just below the summit of Zugspitze in the alps.

#### This project was developed and is in use by <a href="http://bouldair.com/">Boulder A.I.R. LLC</a>, under contract for the German Met Office (DWD).
Trace gases including halogenated species and volatile organic compounds are monitored using a gas chromatograph 
mass-spectrometer (GCMS). The data are analyzed on the remote computer and transfered to a workstation to be analyzed 
and uploaded for the client.

The bulk of the data processing is done in /processing/processors, but individual processors rely on many utilities, 
supporting data, functions and ORM models outside of the processors.

# Poking Around:
The project as a whole is laid out as a Python package to make the author's life easier, but it shouldn't be considered 
a finished product or a true package that can be used elsewhere -- the working copy relies on at least a handful of JSON
config files that are kept private. Start here to get an idea for the project and what it does.

### \_\_main__.py
The main file is the place to begin looking in to the project. An argparser allows command line execution of the routine
data processing functions like downloading new data, processing data into plots and later uploading data.

### Other Places to Start

##### /lab
The lab is a great place to look at what I'm working on currently, or look at half-complete past-projects. 
In-development or past proof-of-concept files live here, and docstrings at the top will key you in to their purpose and 
if they've been finalized and moved elsewhere. 

##### /IO/db/models
Some of the longest docstrings are in data.py and the other model files because the ORM models are essential to the 
project. Nearly all data files and information loaded in are persisted in the database for easy access, and the ORM 
models reflect how the data come in and are subsequently processed.

##### /reporting
Generating human-readable formats and creating common reports can take up a lot of time, but generalized scripts can 
save a lot of time. Reporting contains my strongest attempts to keep myself out of Excel proper and in my IDE as much as
possible. See /analyses/quantifications for the most common use-cases of functions in /reporting.
