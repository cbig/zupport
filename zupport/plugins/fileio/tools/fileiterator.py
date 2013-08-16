from zope.interface import implements

from zupport.core import Tool
from zupport.interfaces import ITool

def service():
    return 'Fileiterator'

def setup(parameters, *args, **kwargs):
    return Fileiterator(parameters, service=service(), *args, **kwargs)

class Fileiterator(Tool):
    
    implements(ITool)
    
    def __init__(self, parameters, service, *args, **kwargs):
        Tool.__init__(self, parameters)