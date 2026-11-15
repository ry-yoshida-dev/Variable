class MeaninglessOperationWarning(UserWarning):
    """
    Warning for an operation whose result has no meaning for a variable.

    The operation itself still runs. Turn the warning into an error with
    ``warnings.simplefilter("error", MeaninglessOperationWarning)`` when strict
    checking is wanted.
    """
