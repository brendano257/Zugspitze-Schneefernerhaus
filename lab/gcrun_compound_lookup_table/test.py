"""
This was created to see what kind of effect get_mr and similar functions that rely on
> next(c for c in compounds if c.name)
are indeed much slower than a lookup, when taking into account the time to create the lookup table.

CONCLUSION:
    Instantiating objects is expensive (10K takes 11-12s), and adding a lookup table is negligible (adds .3s for 10K).

    HOWEVER, retrieving's worst-case for get_mr_from_run is O(n), which shows up massively at scale (1M retrievals).
        A lookup table on the other hand is ~O(1), and takes ~.4s regardless of location in the table.

    CAVEATS: A common use case is using a custom query or abstract_query() to get the join of GcRun.date and Compound.mr,
        this is most commonly done in plotting functions. In this case, one could use abstract_query and join, or could
        simply request the GcRuns for the necessary dates, then retrieve the compounds by hand. In this case, letting
        the database do the work is ~20x faster:

        Testing query with standard join (for 5 compounds, n=100):
        0.8508351650002624
        Testing query with lookup (for 5 compounds, n=100):
        19.09872152700018

        However, since the GcRuns can be re-lookup'd to get multiple compounds with no second query (if using lookups),
        this conveys an increasing advantage for more compounds, the database is only ~4X faster with 5 compounds:

        Testing query with standard join (for 5 compounds, n=100):
        4.180347804000121
        Testing query with lookup (for 5 compounds, n=100):
        18.507331383999826

        And, the effect is linear for both methods, the database just has a faster constant:

        Testing query with standard join (for 5 compounds, n=1000):
        41.825556479999705
        Testing query with lookup (for 5 compounds, n=1000):
        183.62742359100002

        As the number of compounds that need to be looked up increases, querying then using a lookup begins to win out:

        Testing query with standard join (for 30 compounds, n=100):
        25.1359389510003
        Testing query with lookup (for 30 compounds, n=100):
        18.420506164000017

        This suggests that a lookup is slightly better suited for use when all compounds (50+) need to be retrieved, as
        the cost of adding additional compounds to look up is essentially nothing. In fact, retrieving 6x the compounds
        was slightly faster (average of 100 trials in both cases -- just a statistical oddity most likely),
        but this assumes that removing any cases of None from dates is efficient enough to warrant the switchover.

        The above is in fact true, even retrieving and checking the value in the lookup (THREE TIMES PER ITER) is still
        faster at 30+ compounds. Using the below to compile the lists:

            for name in names:
                dates = [r.date for r in results if r.compound.get(name) is not None]
                mrs = [r.compound.get(name) for r in results if r.compound.get(name) is not None]

        Gives results of:
            Testing query with standard join (for 30 compounds, n=100):
            26.139285447000475
            Testing query with lookup (for 30 compounds, n=100):
            19.02287062800042

        For highly repetive operations over many compounds like plotting, the lookup is a clear winner.

    RESULT: A version of lookup will be implemented and used throughout the project. get_mr_from_run will be deprecated.
        Ideally, Integration, GcRun, and LogFile will get a generalized mixin class that adds a Class.compound[key]
        method, along with the necessary reconstructor decorator etc.

Results for instantiating 10K GcRuns WITHOUT a lookup table:
    0 11.850648481999087
    1 12.058820608999667
    2 11.859062002000428
    3 11.813784662997932
    4 11.947717243001534
    5 11.67642890299976
    6 11.732889538001473
    7 11.936172940000688
    8 11.825273722002748
    9 11.928780807000294

Results for instantiating 10K GcRuns WITH a lookup table:
    0 12.03523181700075
    1 12.224052637000568
    2 12.294624676997046
    3 12.28087434900226
    4 12.024313071000506
    5 12.293270664999
    6 12.0866622609974
    7 12.148853779999627
    8 12.229116312002589
    9 12.149646231999213

Results for retrieving 1M Compounds by name WITHOUT a lookup table (on ethane, a likely EARLY-indexed compound):
    0 2.135976962999848
    1 2.11295427100049
    2 2.0991927009999927
    3 2.104794745999243
    4 2.11133129800146
    5 2.1016711090014724
    6 2.1044043370020518
    7 2.101359569001943
    8 2.10647519199847
    9 2.104439769998862

Results for retrieving 1M Compounds by name WITH a lookup table (on ethane):
    0 0.03981156800000463
    1 0.03975109800012433
    2 0.03972263700052281
    3 0.0399148239994247
    4 0.03998263799803681
    5 0.04016138999941177
    6 0.03993257099864422
    7 0.03973145000054501
    8 0.0400232860010874
    9 0.039600877000339096

Results for retrieving 1M Compounds by name WITHOUT a lookup table (on toluene, a likely LATE-indexed compound):
    0 16.528157337001176
    1 16.560681620998366
    2 16.689192890000413
    3 16.613558902001387
    4 16.655288688001747
    5 16.40401796399965
    6 16.247222860001784
    7 16.281505775998085
    8 16.274297490999743
    9 16.340425498001423

Results for retrieving 1M Compounds by name WITH a lookup table (on toluene):
    0 0.047828384002059465
    1 0.047683556000265526
    2 0.04774178200023016
    3 0.04790357099773246
    4 0.04845501900126692
    5 0.048434017997351475
    6 0.04834720699727768
    7 0.04863480999847525
    8 0.04828710299989325
    9 0.048202690999460174
"""
from timeit import timeit
from types import FunctionType
from datetime import datetime

from sqlalchemy.orm import class_mapper

from IO.db import GcRun, Integration, LogFile, DBConnection, Compound
from reporting import abstract_query
from processing.processing import get_mr_from_run

with DBConnection() as session:
    # grab first GcRun in the record
    # gcrun = session.query(GcRun).limit(1).one()

    # print(GcRun._create_lookup, isinstance(GcRun._create_lookup, FunctionType))
    # print(GcRun.create_lookup, isinstance(GcRun.create_lookup, FunctionType))
    # print(GcRun.__iter__, isinstance(GcRun.__iter__, FunctionType))
    # print(GcRun._create_lookup.__sa_reconstructor__)

    # _gc_run_mapper = class_mapper(GcRun)
    # print(_gc_run_mapper._reconstructor)

    # mapper = class_mapper(GcRun)
    # mapper._reconstructor = GcRun._create_lookup

    # print(_gc_run_mapper._reconstructor)
    #
    gcrun = session.query(GcRun).limit(1).one()

    #

    # print('-------------------------')
    # keys = dir(GcRun)
    # for key in keys:
    #     for c in GcRun.__mro__:
    #         if key in c.__dict__:
    #             print(key, c.__dict__[key])
    # print('-------------------------')

    # optionally, show that lookup works on 'load' event
    print(gcrun.compound['ethane'])
    print(gcrun.compound['toluene'])
    #
    integration_id = gcrun.integration.id
    log_id = gcrun.log.id

# TEST TIMEIT OF INSTANTIATION
with DBConnection(autoflush=False) as session:
    integration = session.query(Integration).filter(Integration.id == integration_id).one()
    log = session.query(LogFile).filter(LogFile.id == log_id).one()

    run = GcRun(log, integration)

    # optional test of run.compound lookup after init is called
    print(run.compound)
    print(run.compound['ethane'])

#     for i in range(10):
#         print(i, timeit('GcRun(log, integration)', globals=globals(), number=10_000))

##  TEST TIMEIT OF RETRIEVAL
# with DBConnection() as session:
#     # grab first GcRun in the record
#     gcrun = session.query(GcRun).limit(1).one()
#
#     n = 1_000_000
#
#     # test 10K retrievals of ethane
#     print('Testing get_mr_from_run retrieval, ethane: ')
#     for i in range(10):
#         print(i, timeit('get_mr_from_run(gcrun, "ethane")', globals=globals(), number=n))
#
#     # test 10K retrievals of ethane
#     print('Testing lookup retrieval, ethane: ')
#     for i in range(10):
#         print(i, timeit('gcrun.lookup["ethane"]', globals=globals(), number=n))
#
#     # test 10K retrievals of toluene
#     print('Testing get_mr_from_run retrieval, toluene: ')
#     for i in range(10):
#         print(i, timeit('get_mr_from_run(gcrun, "toluene")', globals=globals(), number=n))
#
#     # test 10K retrievals of ethane
#     print('Testing lookup toluene, toluene: ')
#     for i in range(10):
#         print(i, timeit('gcrun.lookup["toluene"]', globals=globals(), number=n))

## TEST TIMEIT OF RETRIEVING FROM DATABASE VS LOOKUP
# with DBConnection() as session:
#
#     n = 100
#
#     ambient_filters = [
#         GcRun.type == 5,
#         Compound.filtered == False,
#     ]
#
#     name = 'ethane'
#
#     def query_with_join():
#         params = (GcRun.date, Compound.mr)
#         filters = (
#             Compound.name == name,
#             GcRun.date >= datetime(2020, 1, 1),
#             *ambient_filters
#         )
#
#         results = abstract_query(params, filters, GcRun.date, session=session)
#
#         dates = [r.date for r in results]
#         mrs = [r.mr for r in results]
#
#     def query_then_lookup():
#         results = abstract_query((GcRun,),
#                                  (GcRun.date >= datetime(2020, 1, 1), GcRun.type == 5),
#                                  GcRun.date, session=session)
#
#         dates = [r.date for r in results]
#         mrs = [r.compound.get(name) for r in results]
#
#     print('Testing query with standard join: ')
#     print(timeit('query_with_join()', globals=globals(), number=n))
#
#     print('Testing query with lookup: ')
#     print(timeit('query_then_lookup()', globals=globals(), number=n))

## TEST TIMEIT OF RETRIEVING FROM DATABASE VS LOOKUP WITH MULTIPLE COMPOUNDS
# with DBConnection() as session:
#
#     n = 100
#
#     ambient_filters = [
#         GcRun.type == 5,
#         Compound.filtered == False,
#     ]
#
#     names = ('PFC-116', 'ethene', 'SF6', 'CFC-13', 'ethane', 'SO2F2', 'HFC-143a', 'PFC-218', 'HFC-125', 'OCS',
#              'H-1301', 'HFC-134a', 'HFC-152a', 'HCFC-22', 'CFC-115', 'propene', 'methyl_chloride', 'propane',
#              'CH2Br2', 'hexane', 'benzene', 'methyl_chloroform', 'CCl4', 'cyclohexane',
#              'n-heptane', 'toluene', 'perchloroethylene', 'iso-octane', 'CHBr3', 'octane')
#
#     def query_with_join_multiple():
#         for name in names:
#             params = (GcRun.date, Compound.mr)
#             filters = (
#                 Compound.name == name,
#                 GcRun.date >= datetime(2020, 1, 1),
#                 *ambient_filters
#             )
#
#             results = abstract_query(params, filters, GcRun.date, session=session)
#
#             dates = [r.date for r in results]
#             mrs = [r.mr for r in results]
#
#     def query_then_lookup_multiple():
#         results = abstract_query((GcRun,),
#                                  (GcRun.date >= datetime(2020, 1, 1), GcRun.type == 5),
#                                  GcRun.date, session=session)
#
#         for name in names:
#             dates = [r.date for r in results if r.compound.get(name) is not None]
#             mrs = [r.compound.get(name) for r in results if r.compound.get(name) is not None]
#
#     print(f'Testing query with standard join (for {len(names)} compounds, n={n}): ')
#     print(timeit('query_with_join_multiple()', globals=globals(), number=n))
#
#     print(f'Testing query with lookup (for {len(names)} compounds, n={n}): ')
#     print(timeit('query_then_lookup_multiple()', globals=globals(), number=n))
