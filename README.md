# Zugspitze-Schneefernerhaus
### A suite of data-analysis tools and processes for plotting and reporting atmospheric data from a remote station.

#### The Schneefernerhuas is a converted hotel that serves as an environmental research station just below the summit of Zugspitze in the alps.

#### This project was developed and is in use by <a href="http://bouldair.com/">Boulder A.I.R. LLC</a>, under contract for the German Met Office (DWD).
Trace gases including halogenated species and volatile organic compounds are monitored using a gas chromatograph 
mass-spectrometer (GCMS). The data are analyzed on the remote computer and transfered to a workstation to be analyzed 
and uploaded for the client.

The bulk of the data processing is done in /processing/processors, but individual processors rely on many utilities, 
supporting data, functions and ORM models outside of the processors. 
