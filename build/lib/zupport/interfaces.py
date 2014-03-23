#!/usr/bin/python
# coding=utf-8

from zope.interface import Interface, Attribute

class ITool(Interface):
    """
    """
    id = Attribute("""""")
    name = Attribute("""""")
    service = Attribute("""""")
    
    def get_parameter(index):
        """"""
        
    def validate_parameters():
        """"""

class IGISTool(Interface, ITool):
    """
    """
    backend = Attribute("""""")
    parameter_count = Attribute("""""")
    workspace = Attribute("""""")

    def run():
        """"""

    def setup():
        """"""

class IPlugin(Interface):
    """
    """
    
    name = Attribute("""""")
    plugins = Attribute("""""")

    def _load_tool(tool):
        """"""
    
    def provides():
        """"""
    
    def setup():
        """"""

    def _unload_tool(tool):
        """"""

