#!/usr/bin/python
# coding=utf-8
"""

"""

import copy
import inspect
import os
import pkgutil
import sys
from types import IntType, StringType
import yaml
    
from zope.interface import implements

from zupport import registry
from zupport.interfaces import IPlugin, ITool
from zupport.utilities import Singleton, USER_DATA_DIR
from zupport.utilities.odict import OrderedDict
from zupport.zlogging import Logger

class ExtentContainer(object):
    """ Utility class for storing, reading and writing custom geographical
    extents.
    """

    # TODO: create a method that validates extents for a given resolution
    # AND/OR generates suitable extents based on some default values

    def __init__(self, path=None):
        self._config = self.load_configuration(path)
        self._curres = None

    def load_configuration(self, path, config_file='extents.yaml'):
        try:
            if not path:
                # If no path is provided, try the Zupport default location
                path = os.path.join(USER_DATA_DIR, config_file)

            return yaml.safe_load(open(path))

        except (IOError, OSError), e:
            # Throw the exception
            raise e
        except yaml.composer.ComposerError, e:
            raise e

    @property
    def resolutions(self):
        resolutions = self._config['Resolutions'].keys()
        resolutions.sort()
        return resolutions

    def get_extent(self, extent):
        if self.resolution:
            return self._config['Resolutions'][self.resolution][extent]
        else:
            pass

    def get_names(self, resolution):
        return self._config['Resolutions'][resolution].keys()

    @property
    def names(self):
        if self.resolution:
            return self._config['Resolutions'][self.resolution].keys()
        else:
            pass

    def _set_resolution(self, value):
        if value in self.resolutions:
            self._curres = value

    def _get_resolution(self):
        return self._curres

    resolution = property(_get_resolution, _set_resolution, None,"")

class Job(object):
    
    
    def __init__(self, service, batch, gui, *args, **kwargs):
        """ Using batch=True indicates that we will overide gp parameters
        manually.
        """
        
        self.batch = batch
        self.logger = Logger('Zupport')
        self._predesessor = None
        self._successor = None
        self.service = service
        
        self.tool = None
        # request_service returns a tuple (plugin_name, tool)
        plugin_name, tool = self.request_service(service)
        
        if tool:
            self.tool = tool
            # If batch is True, then gpparams is False
            self.tool.update((not batch), gui, *args, **kwargs)
            self.logger.debug('Setup service <%s> from plugin %s' % (service, 
                                                                   plugin_name))
        else:
            self.logger.warning('Service <%s> not available' % service)
    
    @property
    def parameters(self):
        return self.tool.parameters
    
    def request_service(self, name):
        return registry.queryUtility(ITool, name)

    def run(self):
        if self.tool and self.tool.ready:
            self.tool.run()

    def update_parameters(self, *args, **kwargs):
        self.tool.update(*args, **kwargs)

    def _get_predesessor(self):
        return self.__predesessor

    def _get_successor(self):
        return self.__successor

    def _set_predesessor(self, value):
        if isinstance(value, Job):
            self.__predesessor = value

    def _set_successor(self, value):
        if isinstance(value, Job):
            self.__successor = value

    predesessor = property(_get_predesessor, _set_predesessor, None, 
                           "predesessor's docstring")
    successor = property(_get_successor, _set_successor, None, 
                         "successor's docstring")

class Manager(Singleton):
    ''' Manager class that can load and execute plugins in a specific order.
    '''
    
    def __init__(self, parent=None):
        
        self.logger = Logger('Zupport.Manager')
        if parent and parent.logger:
            self.logger.debugging = parent.logger.debugging
        else:
            self.logger.debugging = True
        self.logger.debug('ZupportManager initialized')
        self._plugins = OrderedDict()
        try:
            import plugins
            
            # Import all the plugin modules that do not raise ImportError
            for loader, module_name, is_pkg in  pkgutil.iter_modules(plugins.__path__):
                try:
                    exec('from plugins import %s' % module_name)
                except ImportError, e:
                    self.logger.warning('Cannot load plugin: %s (%s)' % (module_name, e))
            
            # Load the initial plugins
            plugins_modules = inspect.getmembers(plugins, inspect.ismodule)
            plugins_path = os.path.abspath(os.path.dirname(plugins.__file__))
            for name, data in plugins_modules:
                self.logger.debug('Loading plugin: %s (%s)' % (name, plugins_path))
                self.load_plugin(name, plugins_path)
        
        except ImportError, e:
            self.logger.exception('Cannot load plugin: %s' % str(e))
        
        self.jobqueue = []
            
    def add_job(self, job):
        self.jobqueue.append(job)
    
    def get_plugin(self, name):
        if name in self._plugins.keys():
            return self._plugins[name]
        else:
            return None
    
    def loaded_plugins(self):
        all_tools = registry.getUtilitiesForBy(ITool)
        plugins = []
        # TODO: this sucks big time...
        for tool_name, data in all_tools.iteritems():
            plugins.append(data[0])
        return set(plugins)
    
    def load_plugin(self, name, plugins_path):
    
        try:
            if name in self.loaded_plugins():
                self.logger.info('Plugin %s already loaded' % name)
            else:
                self._plugins[name] = Plugin(name, plugins_path)

        except ImportError, e:
            self.logger.exception('Could not import plugin %s' % e)
            return 0
        
        except ValueError, e:
            self.logger.exception('%s Exiting...' % (e))    
            return 0
    
    def run_job(self, job):
        """ Run a single job.
        """
        self.logger.debug('Running job %s' % job.service)
        res = job.run()
        if res:
            self.logger.info('Finished job %s successfully' % job.service)
        else:
            self.logger.info('Job %s did not finish successfully' % job.service)
    
    def run_jobs(self):
        """ Run all jobs in the queue.
        FIXME: this is broken as a single tool instance exists in the registry
        and parameters are updated while creating a new Job instance. Either
        the registry must allow multiple tool instances or then Job parameters
        must be evaluated just before running the tool.
        """
        for job in self.jobqueue:
            job.run()
    
    def unload_plugin(self, toolname):
        if toolname in self.plugins.keys():
            del self.plugins[toolname]
            self.logger.info('Unloaded tool: %s' % toolname)
        else:
            self.logger.info('Tool not Loaded.')

class Parameter(object):
    """ Utility class for holding parameter information.
    
    Initially, instances have only 4 attributes:
    
    1. name: name of the parameter (required)
    2. value: value of the parameter (required)
    3. required: is the parameter required by whatever tool is using it 
       (optional: defaults to False)
    4. tip: short documentation on the parameter (optional: default to '')
    
    These are defined in a class attribute 'attr_acceptable'
    
    Class constructor accepts args, kwargs, or a single list or dictionary.
    
    """

    attr_acceptable = ['name', 'value', 'required', 'tip']

    def __init__(self, *args, **kwargs):
        
        self.name = None
        self.value = None
        self.required = None
        self.tip = None
        
        # Parse input data
        if args:
            if type(args[0]) in (list, tuple):
                self._init_list(args[0])
            elif type(args[0]) == dict:
                self._init_dict(args[0])
            else:
                self._init_list(args)
        if kwargs:
            self._init_dict(kwargs)
            
    def __setattr__(self, name, value):
        ''' Custom __setattr__ that controls the available attribute names. '''
        if name in Parameter.attr_acceptable:
            object.__setattr__(self, name, value)
        else:
            raise AttributeError('Name %s not valid for class attribute' % name)
            
    def __str__(self):
        return 'Name: %s\nValue: %s\nRequired: %s\nTip: %s\n' % (self.name,
                                                                 self.value,
                                                                 self.required,
                                                                 self.tip)
        
    def _init_list(self, data):
        ''' Parser method for list/tuple type input data.'''
        if len(data) < 2 or len(data) > 4:
            raise ParameterError('Single parameter of the type %s \
must have at least 2 and max 4 values.' % type(self))
        else:
            self.name = data[0]
            self.value = data[1]
            if len(data) == 4:
                self.required = data[2]
                self.tip = data[3]
            else:
                self.required = False
                self.tip = ''
        
    def _init_dict(self, data):
        ''' Parser method for dict type input data.'''
        try:
            self.name = data['name']
            self.value = data['value']
        except KeyError, e:
            raise KeyError('Single parameter of the type %s \
            must have dictionary values "name" and "value".' % type(self))
        if data.has_key('required'):
            self.required = data['required']
        else:
            self.required = False
        if data.has_key('tip'):
            self.tip = data['tip']
        else:
            self.tip = ''

    @property
    def label(self):
        '''Label cannot be set, instead it is automatically constructed based
        on whether the parameter is required or not'''
        label = self.name.capitalize()
        label = label.replace('_', ' ')
        if self.required:
            return label
        else:
            return label + ' (optional)'

class ParameterList(object):
    """ Utility class for holding parameter information, objects are instances
    of Parameter class or its' subclasses.
    
    Object Parameters only has one required parameter, name. Object
    can be instantiated with (1) a list of suitable parameters in format 
    
    [{'name': spam, 'value': 1, 'required': True, 'tip': '', ...}]
    
    or (2) full blown guidata interface compatible dictionary in format
    
    {'toolname': [{'name': spam, 'value': 1, 'required': True, 'tip': '', ...}]}

    If no initial parameters are provided, a suitable yaml template 
    for parameters can be provided in the form of absolute or relative path. 

    Class can be subclassed; in this case the subclass must re-implement the 
    parse method in order to handle the provided parameters.
    
    """

    def __init__(self, name, template=None, data=None):
        # Name the instance
        self._name = name
        
        self._data = []
        
        if template is not None:
            data = self.__read(template)
            self.templatepath = template
                    
        self.parse(data)
            
        self.index = 0
        
    def __iter__(self):
        return self
    
    def __len__(self):
        return len(self.data)
    
    def __str__(self):
        return '\n'.join([str(parameter) for parameter in self.data])
            
    def add(self, *args, **kwargs):
        self.data.append(Parameter(*args, **kwargs))
    
    def missing(self):
        # TODO: should do parameter type specific checking
        
        missing = []
        for parameter in self.data:
            if parameter.required and parameter.value == '':
                missing.append(parameter)
        if missing:
            return missing
        else:
            return None
    
    @property
    def name(self):
        return self._name
    
    @property
    def data(self):
        return self._data
        
    def get_parameter(self, token):
        if type(token) == str or type(token) == unicode:
            for parameter in self.data:
                if parameter.name == token:
                    return parameter
        elif type(token) == int:
            return self.data[token]
        else:
            raise ValueError('Token type invalid for object Parameters: %s' % (
                                type(token)))
            
    def get_parameter_value(self, token):
        if type(token) == str or type(token) == unicode:
            for parameter in self.data:
                if parameter.name == token:
                    return parameter.value
        elif type(token) == int:
            return self.data[token].value
        else:
            raise ValueError('Token type invalid for object Parameters: %s' % (
                                type(token)))
        
    def next(self):
        if self.index < len(self.data):
            self.index += 1
            return self.data[self.index - 1]
        else:
            # Enable re-iteration
            self.index = 0
            raise StopIteration()
    
    def parse(self, data):
        ''' Method for parsing input data.
        
        Data can be a single list / tuple / dictionary, or a nested structure.
        Method assumes homogeneity in nestedness, i.e. if the first element
        in the data structure is a list, the whole data structure is a list of
        lists.'''
        
        if data is not None:
            # Check the first level data structure type
            if type(data) == list or type(data) == tuple:
                for element in data:
                    # Check the second level data structure type
                    if type(element) == list or type(element) == tuple or type(element) == dict:
                        # Data is nested list
                        self.add(element)
                    else:
                        # Data is a  single list / tuple
                        self.add(data)
                        break
            if type(data) == dict:
                # Data is a dictionary, must only have 0 or 1 keys which determines
                # the name of the tool that the parameters are for
                assert len(data.keys()) > 1, 'Input data can only have one key.'
                for element in data.values():
                        self.add(element)
           
    @property
    def help(self):
        return self.get_parameter_value('help')
                        
    @property
    def parameter_names(self):
        ''' Property method returns all the parameter names in self.'''
        return [parameter.name for parameter in self.data]
 
    def __read(self, infile):
        
        if not infile.endswith('.yaml'):
            infile = infile + '.yaml'
        if os.path.exists(infile):
            try:
                data = yaml.safe_load(open(infile, 'r'))
                # TODO: hack, there should be a way of comparing template name
                # (key) and Parameters instance.name
                return data.values()[0]
            except (IOError, OSError), e:
                raise
        else:
            raise ValueError('Template path does not exits: %s' % infile)
    
    def remove(self, name):
        for parameter in self.data:
            if parameter.name == name:
                self.data.remove(parameter)
                
    def set_parameter(self, token, object):
        if type(token) == str or type(token) == unicode:
            for parameter in self.data:
                if parameter.name == token:
                    parameter = object
        elif type(token) == int:
            self.data[token] = object
        else:
            raise ValueError('Token type invalid for object Parameters: %s' % (
                                type(token)))
    
    def set_parameter_value(self, token, value):
        
        if type(token) == str or type(token) == unicode:
            # Check if parameter name exists
            if token not in self.parameter_names:
                raise ParameterError('Invalid parameter: %s' % token)
            for parameter in self.data:
                if parameter.name == token:
                    parameter.value = value
        elif type(token) == int:
            self.data[token].value = value
        else:
            raise ValueError('Token type invalid for object Parameters: %s' % (
                                type(token)))

class ParameterError(Exception):
    """ Customized error class caused if parameters data structure is malformed.

    INPUTS:
    value (str): error message to be delivered.

    METHODS:
    __str__: returns error message for printing.
    """
    def __init__(self, value="Internal parameter data structure not valid.",
                 parameters=None):
        self.value = value
        self.parameters = parameters

    def __str__(self):
        return self.value + "\n" + str(self.parameters)

class Plugin(object):
    """
    """
    
    implements(IPlugin)
    
    def __init__(self, name, package_path):
        self._name = name
        self._ready = False
        self.logger = Logger('Zupport.Plugin')
        self.logger.debugging = True
        
        # package_path is the parent folder i.e. package folder for the s
        # plugin -> it must be appended to the sys.path in order to import 
        # the plugin module
        if package_path not in sys.path:
            self.logger.debug('Inserting %s to sys.path' % package_path)
            sys.path.insert(0, package_path)
        
        # Load the module
        try:
            # module here is the same as the plugin module, it needs to 
            # imported only once
            self.logger.debug(name)
            
            module = __import__(name)
            self.logger.debug(str(module))
            # Load initial tools
            tool_modules = module.get_tools()
            #tool_modules = get_tools(module)
            self.logger.debug('%s' % (module))
            if tool_modules:
                for tool_name, tool_module in tool_modules:
                    
                    self._load_tool(name=tool_name, module=tool_module)
                
            else:
                self.logger.warning('No tools available for plugin %s' % name)
            self._ready = True
            
        except ImportError:
            self.logger.error('Could not import %s' % name)
          
        if self._ready:  
            self.logger.info('Loaded plugin: %s' % name)
                
        
    def _load_tool(self, name, module):
        
        # TODO: implement checking for ITool interface
        self.logger.debug('[%s] Loading tool' % name)
        path = os.path.abspath(os.path.dirname(module.__file__))
        try:
            # TODO: tools folder is somewhat confusing here
            definition_file = os.path.join(path, name + '.yaml')
            if not os.path.exists(definition_file):
                self.logger.error(('[%s] Could not find defintion ' +
                'file %s') % (name, definition_file))
                return
            else:
                self.logger.debug('[%s] Definition file:  %s' % (name, 
                                                                definition_file))
            
            parameters = ParameterList(name, definition_file)
            
            tool = module.setup(parameters)
           
            # Add the tool to registry
            if ITool.providedBy(tool):
                registry.provideUtility(tool, ITool, name=tool.service, 
                                        providedby=self._name)
                self.logger.debug('Added %s to registry' % name) 
            else:
                self.logger.error(('Tool %s does not provide ITool interface' +
                                  ' and cannot be used') % name)
            
        except ImportError, e:
            self.logger.exception('Could not import tool %s' % e)
        
        except ValueError, e:
            self.logger.exception('%s Exiting...' % (e))    
        
    def _unload_tool(self, tool):
        pass
    
    def registered(self, tool):
        tools = self.registered_tools()
        if tool in [_tool[0] for _tool in tools]:
            return True
        else:
            return False
        
    def registered_tools(self):
        return list(registry.getUtilitiesFor(ITool, providedby=self._name))



class Project(object):
    """ Utility class for describing Zupport project structure.

    Project properties include helpers for various persistent configuration
    options and geospatial variables. Project also holds the information on
    different operations performed.

    A project instance is always based in one folder either in
    ~/.zupport/projects or elsewhere.
    """

    def __init__(self, path, base_project=True):

        # Check the persistent configuration path
        self._configuration = {}
        self.config_dir = os.path.join(os.path.expanduser('~'), '.zupport',
                                                                 'config')
        if os.path.isdir(self.config_dir):
            try:
                self._configuration = self.load_configuration(self.config_dir,
                                                              'zupportrc.yaml')
            except (IOError, OSError), e:
                print "Couldn't read configuration file."
        else:
            # If no previous configuration structure exist, create it
            os.mkdir(self.config_dir)

        # Check the actual project
        self._project = {}
        if os.path.isdir(path) and not base_project:
            self.path = path
        elif not os.path.isdir(path) and not base_project:
            os.makedirs(path)
        else:
            self.path = os.path.join(os.path.expanduser('~'), '.zupport',
                                                              'projects', path)
            if not os.path.isdir(self.path):
                os.makedirs(self.path)

        # Try reading in the project file
        try:
            self._project = self.load_configuration(self.path, 'project.yaml')
        except (IOError, OSError), e:
            print "Couldn't read project info."

    def load_configuration(self, path, config_file):
        try:
            file = os.path.join(str(path), config_file)
            return yaml.safe_load(open(file))
        except (IOError, OSError), e:
            raise

    def save(self):
        stream = file(os.path.join(self.path, 'project.yaml'), 'w')
        yaml.dump(self.configuration, stream)
        stream.close()
   
class Result(object):
    '''Partial re-implementation of arcpy Result class
    '''
    def __init__(self, toolname, resultID, parent):
        self.toolname = toolname
        self.parameters = parent.parameter
        self._inputCount = len(self.parameters)
        self._maxSeverity = 0
        self._messageCount = 0
        self.output = OrderedDict()
        self._outputCount = 0
        self._resultID = resultID
        self._status = 0
        '''Status:
            0 — New
            1 — Submitted
            2 — Waiting
            3 — Executing
            4 — Succeeded
            5 — Failed
            6 — Timed out
            7 — Cancelling
            8 — Cancelled
            9 — Deleting
            10 — Deleted
        '''
        # Each message is a tuple (severity, message)
        self._messages = []
        
    @property
    def inputCount(self):
        return self._inputCount
    
    @property
    def maxSeverity(self):
        return self._maxSeverity
    
    @property
    def messageCount(self):
        return self._messageCount
    
    @property
    def outputCount(self):
        return self._outputCount
    
    @property
    def resultID(self):
        return self._resultID
   
    def addMessage(self, severity, msg):
        self._messages.append((severity, msg))
   
    def cancel(self):        
        '''Cancels an associated job'''
        raise NotImplementedError
   
    def getInput(self, index):
        '''Returns a given input, either as a recordset or string.'''
        self.parent.get_parameter(index)

    def getMessage(self, index):    
        '''Returns a specific message.'''
        return self.messages[index]
    
    def getMessages(self, severity):
        '''Returns messages.'''
        return_messages = []
        for message in self._messages:
            if message[0] == severity:
                return_messages.append(message[1])
        
    def getOutput(self, index):
        '''Returns a given output.
        '''
        try:
            if type(index) is IntType:
                # OrderedDict must be sliced
                return self.output[index:(index+1)]
            elif type(index) is StringType:
                return self.output[index]
            else:
                return None
        except IndexError:
            return None
        except KeyError:
            return None
        
    def getSeverity(self, index):
        '''Returns the severity of a specific message.'''
        return self._messages[index][0]
   
    def _getStatus(self):
        return self._status
   
    def setOutput(self, index, value):
        self.output[index] = value
        
    def _setStatus(self, status):
        if status in range(0, 11):
            self._status = status
        else:
            raise ValueError('Status values are [0, 10]')
            
    status = property(_getStatus, _setStatus, None, '')
     
class ResultList(object):
    
    def __init__(self):
        self._results = []
        
    def add_result(self, result):
        self._results.append(result)
        
    @property
    def results(self):
        return self._results
        
    def save(self):
        # TODO: overlaps with logging functionality, sort it out
        txt_result_list = []
        for result in self.results:
            txt_result = []
            txt_result.append('Toolname: ' % result.toolname)
            txt_result.append('Status: %s' % result.status) 
            txt_result.append('Input count ' % result.inputCount)
            for parameter in result.parameters:
                txt_result.append('>> %s: %s'% (parameter.name, 
                                                parameter.value))
            txt_result.append('Output count: ' % result.outputCount)
            for i in range(0, result.outputCount):
                txt_result.append('>> Output %s: %s' % (i, result.getOutput(i)))
                
            
            txt_result.append('\n')
            txt_result_list.append(txt_result)
        
class Tool(object):
    """
    """

    def __init__(self, parameters, service=None):

        self._parameters = parameters
        self._ready = False
        #self.results = ResultList()
        #self.status = self.result.status
        self.service = service
        self.provided_by = None

    @property
    def backend(self):
        """Property to return a string holding the name of the used GIS
        engine."""

        return self._backend

    def get_parameter(self, token):
        """Return a parameter value defined by the *token* that can be an 
        integer (index) or string (key). Returns :const:`None` if token is 
        invalid."""
        
        return self.parameters.get_parameter_value(token)
    
    @property
    def parameters(self):
        return self._parameters


    def parameter_count(self):
        """Return the number of parameters in the tool object.
        """
        return len(self.parameters)
            
    def update(self, *args, **kwargs):
        """ Parse the provided *args and **kwargs into Parameters object 
        (self.parameters).
        """
        try:
            # Parameter values provided as args, check that they comply 
            # to Parameters object (self.parameters) structure. 
            # Parameter identity is defined by arg index, so it's 
            # only implicit. 
            if len(self.parameters) < len(args):
                raise ParameterError('Tool expects %s parameters, %s provided' %
                                     (len(self.parameters), len(args)))
            for i, arg in enumerate(args):
                self.parameters.set_parameter_value(i, arg)
            
            # Parameter values provided as kwargs, check that they comply 
            # to Parameters object (self.parameters) structure. 
            # Parameter identity is defined by key word, so it's 
            # explicit. Keys not found in Parameters object are ignored.
            for key, value in kwargs.iteritems():
                self.parameters.set_parameter_value(key, value)
        
            # TODO: should readiness be defined by Job or Tool object?
            self.ready = True
        
        except ParameterError, e:
            self.log.exception('%s' % e)
            
    def validate_parameters(self):
        
        missing = self.parameters.missing()
        if missing:
            missing = ';'.join(['%s: %s' % (item.name, item.value) for item in missing])
            self.logger.error('Following parameter values are missing: %s' % missing)
        else:
            self.ready = True
    
    def _get_ready(self):
        return self._ready
    
    def _set_ready(self, value):
        self._ready = bool(value)
        
    ready = property(_get_ready, _set_ready, None, '')

if __name__ == '__main__':
#    try:
#        import psyco
#        psyco.full()
#    except ImportError:
#        pass

#    executetool('MultiClipRaster', 'zupport.rastertools.multiclipraster', 'arcgis',
#               r"G:\Data\Metsakeskukset\Etela-Savo\VMI\MSNFI.gdb\Keskipituus;G:\Data\Metsakeskukset\Etela-Savo\VMI\MSNFI.gdb\Tilavuus_koivu",
#               r"G:\Data\tmp\Scratch", "ERDAS IMAGINE",
#               r"G:\Data\GRASS\ArcData\sample_area_N_es.shp", 
#               None)

#    fields = ["TILAVUUS"]
#    for field in fields:
#        executetool('MultiConvertRaster', 'zupport.rastertools.multiconvertraster', 
#				'arcgis',
#				r'C:\Data\Staging\TemporaryStorage.gdb\FinlandYKJ\MK_puusto_ES',
#				[{'IPUULAJI': ['all']}, {'IOSITE': ['all']}],
#				field,
#				r'C:\Data\Staging\Output\MK_puusto\ositteet',
#				'ERDAS IMAGINE',
#				20,
#				r'C:\Data\Staging\Masks\MLVMI_maski_metsat.img',
#				debug=True)

#    executetool('CalculateRasterGroup', 'zupport.rastertools.calculaterastergroup', 
#                'arcgis',
#                r'C:\Data\Staging\Output\MK_puusto\index',
#                r'C:\Data\Staging\Output\MK_puusto\index\groups',
#                'SUM',
#                '<BODY1>_<BODY2>_<BODY3>_<SUB1>_<ID1>',
#                'BODY3')
#    executetool('CalculateRasterGroup', 'zupport.rastertools.calculaterastergroup', 
#                'arcgis',
#                r'C:\Data\Staging\Output\LP_puusto\index',
#                r'C:\Data\Staging\Output\LP_puusto\index\groups',
#                'SUM',
#                '<BODY1>_<BODY2>_<BODY3>_<SUB1>_<SUB2>_<ID1>',
#                'BODY3')
    
#    executetool('CalculateRasterGroup', 'zupport.rastertools.calculaterastergroup', 
#                'arcgis',
#                r'C:\Data\Staging\Output\MK_puusto\index\groups',
#                r'C:\Data\Staging\Output\MK_puusto\index\final',
#                'SUM',
#                '<BODY1>_<BODY2>_<ID1>',
#                'ID1')

#
#    executetool('CalculateRasterGroup', 'zupport.rastertools.calculaterastergroup', 
#                'arcgis',
#                r'C:\Data\Staging\Output\MK_puusto\index\groups',
#                r'C:\Data\Staging\Output\MK_puusto\index\final',
#                'SUM',
#                '<BODY1>_<BODY2>_<ID1>',
#                'ID1',
#                reftable,
#                reffields)

#    executetool('CrossSelect', 'zupport.rastertools.crossselect',
#                    'arcgis',
#                r'C:\Data\Staging\Masks\MHMVMKIVMI_kp_maski.img',
#                r'C:\Data\Staging\Output\final_index',
#                r'C:\Data\Staging\Output\final_index\kasvupaikat',
#                include=[1, 2, 3, 4, 5, 6, 7],
#                raster_name_tag='kp')

    ex = ExtentContainer()
    ex.resolution = 500
#    
#    manager = Manager()
#    manager.load_tool('Aggregate')
#    if manager.is_loaded("Aggregate"):
#        manager.executetool(toolname='Aggregate', 
#                            backend='arcgis',
#                            input_workspace=r'H:\Data\SuperMetso\Rasterit\index\100',
#                            output_workspace = r'H:\Data\SuperMetso\Rasterit\index',
#                            cell_factor=5,
#                            raster_type='ERDAS IMAGINE',
#                            extent=ex.get_extent('Finland'))
    manager = Manager()
    plugin = manager.get_plugin('zarcgis')
#    if plugin:
#        print('Tools provided by %s' % plugin_name)
#        for tool in plugin.registered_tools():
#            print tool
#    print plugin.registered('aggregate')
#    job = Job('aggregate',
#              input_raster=r'H:\Data\SuperMetso\Rasterit\index\100\index_manty.img',
#              output_raster=r'H:\Data\SuperMetso\Rasterit\index_manty_500.img',
#              cell_factor=5,
#              raster_type='ERDAS IMAGINE',
#              extent=ex.get_extent('Finland'))
#    print plugin.registered('multiconvertraster')
#    job = Job('multiconvertraster',
#              input_feature=r'G:\Data\Metsakeskukset\Etela-Savo\Metsavara\osite.gdb\osite_1_9_sample',
#              input_condition_fields='OSITE;PUULAJI',
#              output_value_field='KLPM',
#              output_workspace=r'G:\Data\Metsakeskukset\Etela-Savo\Metsavara\MVGDBScratch.gdb',
#              pixel_size=20,
#              raster_type='ERDAS IMAGINE',
#              extent='',
#              snap_raster=r'G:\Data\Metsakeskukset\Etela-Savo\VMI\MSNFI.gdb\Kasvupaikka',
#              debug=True)
#    job = Job('discretizefields',
#              False,
#              False,
#              intable=r'G:\Data\Metsakeskukset\Etela-Savo\Metsavara\osite.gdb\XFOREST_SOSLASPSTO',
#              intable_discrete_field='OSITE',
#              intable_join_field='SKUVIOID',
#              infeature=r'G:\Data\Metsakeskukset\Etela-Savo\Metsavara\osite.gdb\test_osite_org',
#              #infeature=r'G:\Data\Metsakeskukset\Etela-Savo\Metsavara\HAKKUUT2.gdb\KUVIOT_HAK_SUOD_JCAUNT_DAT2000',
#              infeature_join_field='SKUVIOID',
#              output_feature=r'G:\Data\Metsakeskukset\Etela-Savo\Metsavara\osite.gdb\ositteet_kaikki',
#              debug=True)
    #print job.parameters
    job = Job('rasigmoidal',
              False,
              False,
              raster1=r'H:\Data\Metsakeskukset\Keski-Suomi\ositteet_test\OSITE_NO_2_PUULAJI_13_J_KESKILPM.img',
              raster2=r'H:\Data\Metsakeskukset\Keski-Suomi\ositteet_test\OSITE_NO_2_PUULAJI_13_KOK_TIL.img',
              output_raster=r'H:\Data\Metsakeskukset\Keski-Suomi\index_KES.gdb\testPUULAJI_13_OSITE_2_index',
              raster_type='ERDAS IMAGINE',
              asymptote=1.2,
              xmid=19,
              lxmod=0.22,
              rxmod=0.18,
              lscale=10.57,
              rscale=6.23,
              debug=True)
#    job = Job("pairfileiterator",
#              input_workspace=r'C:\Data\Staging\Output\MK_puusto\ositteet',
#              wildcard="*.img",
#              template='<BODY1>_<ID1>_<BODY2>_<ID2>_<BODY3>',
#              debug=True)
#    
#    from zupport.utilities.dataframe import read_csv, ZCustom
#    reffields = ("IPUULAJI", "LuokkaID")
#    reftable_file =  r"C:\Data\Staging\parameters111130.csv"
#    parameters = read_csv(reftable_file, dialect=ZCustom)
#
#    job = Job('calculaterastergroup',
#              False,
#              False,
#              r'C:\Data\Staging\Antti\index.gdb',
#              '*',
#              '<BODY1>_<ID1>_<BODY2>_<ID2>_<BODY3>',
#              ['ID1'],
#              'SUM',
#              r'C:\Data\Staging\Antti\index_groups.gdbb',
#              parameters,
#              reffields,
#              debug=True)
    
#    job = Job('crossselect',
#              False,
#              False, 
#              reference_raster=r'C:\Data\Staging\Masks\MHMVMKIVMI_kp_maski.img',
#              input_workspace=r'G:\Data\Metsakeskukset\Etela-Savo\Metsavara\MVScratch\index_group.gdb',
#              output_workspace=r'G:\Data\Metsakeskukset\Etela-Savo\Metsavara\MVScratch\index_group_kp.gdb',
#              include=[1, 2, 3, 4, 5, 6, 7],
#              exclude=[],
#              raster_format='ESRI FGDB',
#              raster_name_tag='kp')

    manager.add_job(job)
    manager.run_jobs()