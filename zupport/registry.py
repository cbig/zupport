#!/usr/bin/python
# coding=utf-8

from zope import component

from zupport.interfaces import ITool
    
def getUtilitiesFor(interface, providedby=None, context=None):
    utilities = component.getUtilitiesFor(interface, context)
    if providedby:
        new_utilities = []
        for name, value in utilities:
            plugin, name = _break_plugin_name(name)
            if plugin == providedby:
                new_utilities.append((name, value))
        return new_utilities
    else:
        return utilities
    
def getUtilitiesForBy(interface, context=None):
    utilities = component.getUtilitiesFor(interface, context)

    new_utilities = {}
    for name, value in utilities:
        plugin, name = _break_plugin_name(name)
        new_utilities[name] = (plugin, value)
    return new_utilities

def provideUtility(component_, provides=None, name=u'', providedby=u''):
    name = _create_plugin_name(name, providedby)
    component.provideUtility(component_, provides, name)

def queryUtility(interface, name='', default=None, context=None):
    utilities = getUtilitiesForBy(ITool)
    if name in utilities.keys():
        utility = utilities[name]
    else:
        utility = (None, None)
    return utility

def _create_plugin_name(name, plugin):
    if plugin != '':
        return u'%s::%s' % (plugin, name)

def _break_plugin_name(name):
    if '::' in name:
        return name.split('::')
    else:
        return (name, None)
    