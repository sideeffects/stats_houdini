import functools

_cached_queries = {}

def find_or_execute_query(query_function, *args, **kwargs):
    """Given a function that executes a query, along with the parameters to
    pass to that function, execute that function and return its results.
    However, if the function has been executed with those parameters before
    and the results are cached, return the cached results instead of actually
    executing the function.
    """
    # To keep the server from consuming lots of memory from cached queries,
    # we limit the number of cached results per query function.
    MAX_CACHES_PER_FUNCTION = 3

    if query_function not in _cached_queries:
        # We have never cached the results of calling this function, at all.
        # Run the query and create a list containing one cached result.
        # We store the parameters and the result, so that we can later check
        # if the parameters in the cache match the ones passed in.
        query_result = query_function(*args, **kwargs)
        _cached_queries[query_function] = [((args, kwargs), query_result)]
        return query_result

    # See if we have cached the results of calling this function with these
    # parameters.
    parms_and_results = _cached_queries[query_function]
    for i, (query_parms, query_result) in enumerate(parms_and_results):
        if query_parms == (args, kwargs):
            # Move the cached result earlier in the list because when we
            # remove cached results to make room later, we'll remove the
            # least recently accessed ones from the end.
            parms_and_results.insert(0, parms_and_results.pop(i))
            return query_result

    # If the cache is full, make room for the new cached results, deleting
    # the least recently accessed results.
    if len(parms_and_results) >= MAX_CACHES_PER_FUNCTION:
        parms_and_results.pop()

    query_result = query_function(*args, **kwargs)
    parms_and_results.insert(0, ((args, kwargs), query_result))
    return query_result

def cacheable(function):
    """This decorator lets you mark a function as caching its results."""
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        return find_or_execute_query(function, *args, **kwargs)
    return wrapper
