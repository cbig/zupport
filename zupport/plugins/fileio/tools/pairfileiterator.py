from zope.interface import implements

from zupport.core import ParameterError, Tool
from zupport.utilities import ARC_RASTER_TYPES, msgInitSuccess
from zupport.zlogging import Logger

from zupport.interfaces import ITool

from ..core import ParsedWorkspace

def service():
    return 'pairfileiterator'

def setup(parameters, *args, **kwargs):
    return PairFileiterator(parameters, service=service(), *args, **kwargs)

class PairFileiterator(Tool):
    
    implements(ITool)
    
    id = 0
    
    def __init__(self, parameters, service, *args, **kwargs):
        Tool.__init__(self, parameters, service, *args, **kwargs)

        self.name = self.__class__.__name__
        # Identifier is a combination of the name and the class counter
        self.id = (self.name, PairFileiterator.id)
        
        self.log = Logger("Zupport.%s" % (self.__class__.__name__), 
                                             debugging=True)
        
        self.service = service
        
        self.log.debug(msgInitSuccess)
        
    def __del__(self):
        if PairFileiterator:
            PairFileiterator.id = PairFileiterator.id - 1
            
    def run(self):
        
        try:
            
            self.validate_parameters()
        
            input_workspace = self.get_parameter(0)
            wildcard = self.get_parameter(1)
            template = self.get_parameter(2)
            self.log.debugging = self.get_parameter(3)
            
            self.log.debug('Parsing workspace %s with template %s' % (input_workspace,
                                                                      template))
            workspace_files = ParsedWorkspace(template, input_workspace, 
                                              wildcard)
            no_rasters = len(workspace_files)
            if  no_rasters % 2 != 0:
                self.log.error('An even number of rasters needed!')
                # TODO: all tools should consistently return True/False 
                # indicating whether the operation was successful
                return(-1)
        
            rasterpairs = []
            i = 0
            while i < no_rasters:
                
                rasterpairs.append((workspace_files[i], workspace_files[i + 1]))
                i += 2
        
            for pair in rasterpairs:
                a_raster = pair[0]
                b_raster = pair[1]
                ID1 = a_raster.get_tag('ID1')
                ID2 = a_raster.get_tag('ID2') 
                if ID1 == b_raster.get_tag('ID1'):
                    if ID2 == b_raster.get_tag('ID2'):
                        self.log.debug('Raster A: %s' % a_raster.name)
                        self.log.debug('Raster B: %s' % b_raster.name)
        
        except ParameterError, e:
            self.log.exception('Error with parameters: %s' % e)
            raise