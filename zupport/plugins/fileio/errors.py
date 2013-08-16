#!/usr/bin/python
# coding=utf-8

class ParseError(Exception):
    """ Customized error class caused if name and template parsing fails.

    INPUTS:
    value (str): error message to be delivered.

    METHODS:
    __str__: returns error message for printing.
    """
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value