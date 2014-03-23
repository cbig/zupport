#!/usr/bin/python
# coding=utf-8

# Copyright (c) 2010 Rafa Muñoz Cárdenas
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
#   * Neither the name of Pioneers of the Inevitable, Songbird, nor the names
#     of its contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import inspect
import logging.config
import os
import traceback
from types import IntType, BooleanType

from zupport.utilities import (Singleton, LOGGING_INI, USER_DATA_DIR)

# First, try looking from USER_DATA_DIR
if os.path.exists(os.path.join(USER_DATA_DIR, os.path.basename(LOGGING_INI))):
    log_config = os.path.join(USER_DATA_DIR, os.path.basename(LOGGING_INI))
# Then try to look from Zupport installation
elif os.path.exists(LOGGING_INI):
    log_config = LOGGING_INI
else:
    raise IOError('No logging.ini file found')

# TODO: args[0] approach in the following decorators is not safe

def addLineNo(logFunction):
    def wrapper(self, *args, **kwargs):
        lineno = inspect.currentframe().f_back.f_lineno
        
        # HACK: in some cases lineno may be added twice, only have the first
        if 'line' in args[0]:
            linemsg = ''
        else:
            linemsg = 'line %s: ' % lineno
        msg = linemsg + str(args[0])
        logFunction(self, msg)
    return wrapper

def addStack(logFunction):
    def wrapper(self, *args, **kwargs):
        msg = args[0]
        if self.gui:
            stackmsg = ''.join(traceback.format_exc())
            msg += stackmsg
        logFunction(self, msg)
    return wrapper

class LoggerManager(Singleton):
    """
    Logger Manager.
    Handles all logging files.
    """
    def init(self):
        # Set up default log file location
        logging.config.fileConfig(log_config, defaults={'logdir': USER_DATA_DIR})
        self.logger = logging.getLogger()
        self.__gui = False
        
    def _get_gui(self):
        return self.__gui
    
    def _set_gui(self, value):
        assert type(value) is BooleanType or type(value) is IntType, \
               'GUI toggle value cannot be evaluated as boolean'
               
        if value:
            self.__gui = True
        else:
            self.__gui = False
        
    def debug(self, loggername, msg):
        self.logger = logging.getLogger(loggername)
        self.logger.debug(msg)

    def error(self, loggername, msg):
        self.logger = logging.getLogger(loggername)
        self.logger.error(msg)
        
    def exception(self, loggername, msg):
        self.logger = logging.getLogger(loggername)
        self.logger.exception(msg)

    def info(self, loggername, msg):
        self.logger = logging.getLogger(loggername)
        self.logger.info(msg)

    def warning(self, loggername, msg):
        self.logger = logging.getLogger(loggername)
        self.logger.warning(msg)
        
    _gui = property(_get_gui, _set_gui, None, '')

class Logger(object):
    """
    Logger object.
    """
    def __init__(self, loggername="root", debugging=False, parent=None):
        self.lm = LoggerManager() # LoggerManager instance
        self.loggername = loggername # logger name
        self.__debugging = debugging
        
        # TODO: strings should be replaced with ints form LOG
        self.levels = {'debug': self.debug, 'info': self.info, 
                       'warning': self.warning, 'error': self.error,
                       'exception': self.exception}
        
    def get_debugging(self):
        return self.__debugging
        
    def set_debugging(self, value):
        assert type(value) is BooleanType or type(value) is IntType, \
               'Debug toggle value can only be evaluated as boolean, not %s' % type(value) 
        if value:
            self.__debugging = True
            self.info('Debugging enabled')
        else:
            self.__debugging = False
            self.info('Debugging disabled')

    def get_gui(self):
        return self.lm._gui
    
    def set_gui(self, value):
        assert type(value) is BooleanType or type(value) is IntType, \
               'GUI toggle value cannot be evaluated as boolean'
               
        if value:
            self.lm._gui = True
        else:
            self.lm._gui = False

    # Message severity codes correspond to Python logging module

    @addLineNo
    def debug(self, msg, parent=None):
        if self.debugging:
            self.lm.debug(self.loggername, msg)
            if parent:
                parent.result.addMessage(10, msg)

    @addLineNo
    def error(self, msg, parent=None):
        self.lm.error(self.loggername, msg)
        if parent:
            parent.result.addMessage(40, msg)
        
    @addLineNo
    def exception(self, msg, parent=None):
        self.lm.exception(self.loggername, msg)
        if parent:
            parent.result.addMessage(50, msg)

    def info(self, msg, parent=None):
        self.lm.info(self.loggername, msg)
        if parent:
            parent.result.addMessage(20, msg)

    def warning(self, msg, parent=None):
        self.lm.warning(self.loggername, msg)
        if parent:
            parent.result.addMessage(40, msg)
        
    debugging = property(get_debugging, set_debugging, None, '')
    gui = property(get_gui, set_gui, None, '')  
        
class ArcLogger(Logger):
    """
    ArcLogger object.
    """
    def __init__(self, loggername="root", debugging=False):
        Logger.__init__(self, loggername, debugging)
        try:
            from zupport.plugins.zarcgis.utilities import get_geoprocessor
            self.gp = get_geoprocessor(10)
            self.__progressor = False
        except ImportError:
            raise
    
    def setProgressor(self, msg, min=0, max=100, type='step'):
        self.gp.SetProgressor(type, msg, min, max)
        self.__progressor = True
   
    def setProgressorPosition(self):
        if self.__progressor:
            self.gp.SetProgressorPosition()
        
    def resetProgressor(self):
        self.gp.ResetProgressor()
        self.__progressor = False
    
    @addLineNo
    def debug(self, msg):
        if self.debugging:
            super(ArcLogger, self).debug(msg)
            if self.gui:
                self.gp.AddMessage('DEBUG - %s' % msg)

    @addLineNo
    def error(self, msg):
        super(ArcLogger, self).error(msg)
        if self.gui:
            self.gp.AddError(msg)

    @addLineNo
    @addStack
    def exception(self, msg):
        super(ArcLogger, self).exception(msg)
        if self.gui:
            self.gp.AddError(msg)

    def info(self, msg):
        super(ArcLogger, self).info(msg)
        if self.gui:
            self.gp.AddMessage(msg)
            
    def progressor(self, msg, log=None):
        if self.__progressor:
            self.gp.SetProgressorLabel(msg)
        if log:
            if log in self.levels.keys():
                self.levels[log](msg)
                
    def warning(self, msg):
        super(ArcLogger, self).warning(msg)
        if self.gui:
            self.gp.AddWarning(msg)
            
if __name__ == '__main__':
    print globals()['USER_DATA_DIR']
    logger = ArcLogger('root.user')
    logger.debug('Debugging')
    logger.info('Infoing')
    logger.info('More info with an object')
    logger.warning('Warning!')
    logger.error('Error!!!')
#    try:
#        raise StandardError
#    except StandardError, e:
#        logger.exception('Oh dear, an exception occurred: %s.' % e)
    logger2 = ArcLogger('root.user2')
    print 'logger1 gui: ' + str(logger.gui)
    print 'logger1 dbg: ' + str(logger.debugging)
    print 'logger2 gui: ' + str(logger2.gui)
    print 'logger2 dbg: ' + str(logger2.debugging)
    logger.gui = True
    logger.debugging = True
    print 'logger1 gui: ' + str(logger.gui)
    print 'logger1 dbg: ' + str(logger.debugging)
    print 'logger2 gui: ' + str(logger2.gui)
    print 'logger2 dbg: ' + str(logger2.debugging)
    logger2.gui = False
    print 'logger1 gui: ' + str(logger.gui)
    print 'logger2 gui: ' + str(logger2.gui)
    