
from dateutil.relativedelta import relativedelta
from qsstats import QuerySetStats
import utils 
#===============================================================================
def fill_missing_dates_with_zeros(time_series, agg_by, interval, 
                                   fill_with_empty_string = False):
    """
    When aggregating licenses, we don't get back any months that
    have no activity. Using dateutil, we will find such months
    months, and add them with to the report, with a count of 0.
    """
    
    # By default with always fill with zeros, unless the param 
    # fill_with_empty_string is set to true.
    filler = 0
    if fill_with_empty_string:
        filler = ""
        
    result_time_series = []
    dates = [x[0] for x in time_series]
    
    # Determine the first date that will be in the result time series.  If
    # we're aggregating, we need to step through the dates starting with the
    # first day of the week/month/year.
    current_date = interval[0]
    
    if agg_by == "week":
        # Find the Monday at the beginning of the week.
        current_date -= relativedelta(days=interval[0].weekday())
    elif agg_by == "month":
        current_date = current_date.replace(day=1)
    elif agg_by == "year":
        current_date = current_date.replace(day=1, month=1)
    elif agg_by == "daily" or agg_by == "dai":
        agg_by = "day"
    else:
        assert False, "Unknown aggregation type"

    # Loop through all the dates from the start up to and including the end,
    # filling any missing data points with zeros.
    index = 0
    
    while current_date <= interval[1]:
        if current_date in dates:
            result_time_series.append([current_date, time_series[index][1]])
            index += 1
        else:
            result_time_series.append([current_date, filler])

        current_date += relativedelta(**{agg_by + "s": 1})

    return result_time_series

#-------------------------------------------------------------------------------
def time_series(queryset, date_field, interval, func=None, agg=None):
    if agg in (None, "daily"): 
        qsstats = QuerySetStats(queryset, date_field, func)
        return qsstats.time_series(*interval)
    else:
        # Custom aggregation was set (weekly/monthly/yearly)
        agg_by = agg[:-2]

        # We need to set the range dynamically
        interval_filter = {date_field + "__gte" : interval[0],
                           date_field + "__lte" : interval[1]}

        # Slightly raw-ish SQL query
        result = (queryset.extra(select={agg_by: connections[queryset.db]
                             .ops.date_trunc_sql(agg_by, date_field)})
                             .values_list(agg_by)
                             .annotate(dcount=Count(date_field))
                             .filter(**interval_filter)
                             .order_by(agg_by))
        
        return fill_missing_dates_with_zeros(result, agg_by, interval)

#-------------------------------------------------------------------------------
def get_time_series_sequences(
        queryset_sequences, interval, aggregation=None,
        date_field="created", func=None):
    """
    This function takes a sequence of querysets and apply time_series to each 
    of them using the arguments passed in the given order.
    """
    
    return [time_series(queryset, date_field, interval, func, aggregation)
        for queryset in queryset_sequences]

#-------------------------------------------------------------------------------
def merge_time_series(time_series_sequences):
    """Given a sequence in the form
        [
            [(0, 10), (1, 20), (2, 15),],
            [(0, 5), (1, 4), (2, 22),]
        ]
    return a sequence of the form
        [
            (0, 10, 5),
            (1, 20, 
            4),
            (2, 15, 22),
        ]
    Note that the first elements (the 0's, 1's and 2's in the example above)
    must be the same.
    """
    # zip will put the data into the form
    #    [
    #        ((0, 10), (0, 5)),
    #        ((1, 20), (1, 4)),
    #        ((2, 15), (3, 22)),
    #    ]
    #assert _time_series_x_axes_line_up(time_series_sequences), \
    #    "Time series x axes do not line up"
    return [(pairs[0][0],) + tuple(pair[1] for pair in pairs)
        for pairs in zip(*time_series_sequences)]

#-------------------------------------------------------------------------------
def _time_series_x_axes_line_up(time_series_sequences):
    """Return whether or not a sequence of time series all contain the same
    x values.
    """
    for pairs in zip(*time_series_sequences):
        if [pair[0] for pair in pairs] != [pairs[0][0]] * len(pairs):
            return False
    return True

#-------------------------------------------------------------------------------
def compute_time_series(time_series_sequences, operation):
    """Given a sequence in the form
        [
            [(0, 10), (1, 20), (2, 15),],
            [(0, 5), (1, 4), (2, 22),]
        ]
    and an operation of the form
        lambda v0, v1: v0 * v1
    return
        [(0, 50), (1, 80), (2, 330)]
    """
    assert _time_series_x_axes_line_up(time_series_sequences), \
        "Time series x axes do not line up"
    return [(pairs[0][0], operation(*tuple(pair[1] for pair in pairs)))
        for pairs in zip(*time_series_sequences)]

#-------------------------------------------------------------------------------
def compute_time_serie(time_serie, operation):
    """Given a time series in the form
        
        [(x, 10), (y, 20), (z, 15)]
    
    and an operation of the form
        lambda v1: v1 * 2
    return
        [(x, 20), (y, 40), (z, 30)]
    """
    return [tuple((pair[0], operation(pair[1]))) for pair in time_serie]

#-------------------------------------------------------------------------------

def choose_unit_from_multiple_time_units_series(time_serie, time_key="seconds"):
    """Given a time series in the form
        [(x,  {'hours': 0, 'seconds': 0, 'minutes': 0, 'days': 0}),
         (y,  {'hours': 0, 'seconds': 0, 'minutes': 0, 'days': 0}),
         (z,  {'hours': 0, 'seconds': 0, 'minutes': 0, 'days': 0})
        ]
    
    and an a time key like: minutes, hours, days, seconds
    return
        [(x, num), (y, num), (z, num)]
    """
    return  [tuple((pair[0], pair[1][time_key])) for pair in time_serie]

#-------------------------------------------------------------------------------

def seconds_to_time_unit_series(time_series, time_unit):
    """
    Given a time series transform 
    """
    return choose_unit_from_multiple_time_units_series(
                                  compute_time_serie(time_series, 
                                  utils.seconds_to_multiple_time_units), 
                                  time_unit) 
