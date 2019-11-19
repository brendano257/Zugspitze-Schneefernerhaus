class Quantification(Base):
    """
    A container for storing quantification information for a standard.

    Quantifications are essentially Compounds that represent the provided values for a gas standard. They are related to
    a Standard object (many --> one), such that a Standard contains one or more Quantifications. For instance, a
    standard might have Quantifications of (name='ethane', value=1543.9), (name='propane', value=802) to indicate that
    that Standard had quantified values of 1543.9ppt for ethane and 802ppt for propane.

    Quantifications are referenced to determine the mixing ratio of a sample by comparing the measured sample response,
    divided by it's corresponding, measured standard response, all multiplied by that standard's Quantification.value
    for the name of that compound.
    """
    __tablename__ = 'quantifications'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    value = Column(Float)

    standard_id = Column(Integer, ForeignKey('standards.id'))
    standard = relationship('Standard', back_populates='quantifications')

    def __init__(self, name, value, standard):
        """
        Create a new Quantification and relate it to it's containing Standard object.

        :param str name: Name of the compound this Quantification is for
        :param float value: Provided or quantified value for the Standard
        :param Standard standard: Standard this Quantification is related to.
        """
        self.name = name
        self.value = value
        self.standard = standard


class Standard(Base):
    """
    A container for information about a gas reference standard.

    Standards contain a given string name, and optional start/end dates for which they're used to quantify samples (None
    is an acceptable required argument for start/end_date). Standards are related to one or more Quantifications that
    represent the given values for that Standard. These are used for calculating mixing ratios of samples.
    """
    __tablename__ = 'standards'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    quantifications = relationship('Quantification', back_populates='standard')

    run = relationship('GcRun', back_populates='standard')

    def __init__(self, name, start_date, end_date):
        """
        Create a Standard by name that applies to samples between the start and end dates.
        (name='NameHere', start_date=None, end_date=None) is acceptable.

        :param str name: Common name, usually a cylinder number.
        :param datetime start_date: Date from which this is the active working standard for quantifying samples.
            **Can be None if end_date is also None, meaning the Standard has provided values but hasn't yet been used
                as a working standard
        :param datetime end_date: Date up until which this is the active working standard for quantifying samples.
            **Can be None if start_date is also None, meaning the Standard has provided values but hasn't yet been used
                as a working standard
        """
        self.name = name
        self.start_date = start_date
        self.end_date = end_date


class SampleQuant:
    """
    An ad-hoc type, similar to a GcRun used for quantifying special samples outside the normal workflow.

    SampleQuants are used when the normal rules/functions for creating and quantifying a sample don't apply.
    For instance, when quantifying a gas standard run against another gas standard, a GcRun is a poor fit to aggregate
    the information and calculate values. Instead, a SampleQuant can be created and quantified in a more individually-
    scripted manner. SampleQuants *can* be persisted, but are often made and reported in a spreadsheet in a
    reproducible, but throw-away style.
    """

    def __init__(self, sample, quantifier, blank, standard, standard_blank=None):
        """
        Create a SampleQuant from GcRuns for the sample, quantifying run, corresponding blank run and Standard.

        :param GcRun sample: the GcRun to be quantfied
        :param GcRun quantifier: the GcRun to be used as the reference, must be of the type given by Standard
        :param GcRun blank: a corresponding blank run that was subtracted from the sample
        :param Standard standard: Standard object that represents the known values of the quantifier sample
        :param GcRun standard_blank: optional GcRun of a blank to be used on only the standard.
            defaults to the given blank if unprovided
        """
        self.sample = sample
        self.quantifier = quantifier
        self.blank = blank
        self.standard = standard

        if not standard_blank:
            self.standard_blank = blank
        else:
            self.standard_blank = standard_blank

    def quantify(self):
        """
        Quantify the sample after all inputs have been blank subtracted.

        Similar to GcRun.quantify, this calculates mixing ratios for the compounds in self.sample, using the supplied
        quantifying sample, blank, and Standard.

        TODO: Does not report the sample as quantified=1 after the fact.
            Originally this was written to be a non-persistant quantification...but it could be changed now.
        :return: None
        """
        if not self.standard:
            print(f'No standard to quantify Sample for date {self.sample.date}.')
            return None

        for quant in self.standard.quantifications:
            if quant.value is None:
                continue

            cpd = search_for_attr_value(self.sample.compounds, 'name', quant.name)

            if self.quantifier is None:
                print(f'No quantifier provided for Sample {self.sample.date}')
                return None
            else:
                if not cpd or cpd.corrected_pa is None:
                    # print(f'No {quant.name} found in compounds for GcRun {self.date}.')
                    continue
                else:
                    q_compound = search_for_attr_value(self.quantifier.compounds, 'name', quant.name)

                    if not q_compound:
                        print(f'No working standard compound found for {quant.name} in GcRun {self.sample.date}')
                        continue

                    if q_compound.corrected_pa is not None and q_compound.corrected_pa is not 0:
                        cpd.mr = (
                                ((cpd.corrected_pa / q_compound.corrected_pa) * self.quantifier.log.sample_time
                                 * self.quantifier.log.sample_flow * quant.value)
                                / (self.sample.log.sample_time * self.sample.log.sample_flow)
                        )
                    # mixing ratio is the response ratio (sample / standard) mutliplied by the
                    # certified value in that standard, normalized for a 2500s, 2.5V sample volume

                    else:
                        print(f'No working standard value found for compound {quant.name} in GcRun {self.sample.date}')
                        continue
