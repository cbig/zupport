import types

from zope.interface import implements
from zupport.interfaces import ITool

from zupport.core import Tool

def service():
    return 'run from excel'

def setup(parameters, *args, **kwargs):
    return RunFromExcel(parameters, service=service(), *args, **kwargs)

class RunFromExcel(Tool):
    
    def __init__(self, parameters, *args, **kwargs):
        pass