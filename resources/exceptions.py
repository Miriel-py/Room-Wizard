#exceptions.py
"""Contains custom exceptions"""


class NoArgumentsError(ValueError):
    """Custom exception for when no arguments are passed to a function"""
    pass

class NoDataFoundError(Exception):
    """Custom exception for when no data is returned from the database"""
    pass