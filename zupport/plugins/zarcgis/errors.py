#===============================================================================
# Custom Error classes

class GPError(Exception):
    """
    INPUTS:
    value (str): error message to be delivered.

    METHODS:
    __str__: returns error message for printing.
    """
    def __init__(self, value="Error occurred. Exiting ..."):
        self.value = value

    def __str__(self):
        return self.value

class FeatureTypeError(Exception):
    """ Customized error class caused if a Feature Class hasn't got the right
    Feature Type.

    INPUTS:
    value (str): error message to be delivered.

    METHODS:
    __str__: returns error message for printing.
    """
    def __init__(self, value="Feature Type Error. Exiting ..."):
        self.value = value

    def __str__(self):
        return self.value

class FieldError(Exception):
    """ Customized error class caused if a field name is not found in the
    provided Feature Class.

    INPUTS:
    value (str): field name that caused the error.

    METHODS:
    __str__: returns error message for printing.
    """
    def __init__(self, fname, fclass):
        self.value = "Field %s not found in Feature Class %s" % (fname, fclass)

    def __str__(self):
        return self.value

class LicenseError(Exception):
    """ Customized error class caused if a proper license version is not
    available.

    INPUTS:
    value (str): extension name that caused the error.

    METHODS:
    __str__: returns error message for printing.
    """
    def __init__(self, extension):
        self.value = "Extension %s not found in the system." % extension

    def __str__(self):
        return self.value