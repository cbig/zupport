'''
Created on 25.2.2011

@author: admin_jlehtoma
'''
import unittest
from mock import Mock
from zupport.gui import ZupportGUI
from zupport.utilities import Parameters

class Test(unittest.TestCase):

    def setUp(self):
        self.tool = Mock()
        self.tool.run = Mock()
        name = 'testtool'
        data = [{'name': 'input_workspace',
                  'required': True,
                  'tip': 'Path to input workspace',
                  'value': 'PATH:input/path/to/filesystem/location'}, 
                 {'name': 'output_workspace',
                  'required': True,
                  'tip': 'Path to output workspace',
                  'value': 'PATH'}, 
                 {'name': 'nodata_mode',
                  'required': True,
                  'tip': 'Should NoData be preserved',
                  'value': True},
                 {'name': 'interpolation_method',
                  'required': True,
                  'tip': 'The interpolation method to be used',
                  'value': ['Linear', 'Cubic', 'Inverse weighted distance']}]
        
        self.tool.parameters = Parameters(name=name, data=data)
        self.gui = ZupportGUI(self.tool)

    def tearDown(self):
        pass
    
#    def testCreateParametersName(self):
#        for name, item in self.data.iteritems():
#            self.parameters = Parameters(name=name, data=item)
#            self.assertEqual(self.parameters.name, name)

    def testGuiInitializationWithParameters(self):
        
        for parameter in self.tool.parameters:
            widget = getattr(self.gui.data, parameter.name)
            self.assertEqual(widget.value, parameter.value,
                             'Widget and parameter values do not match')
            
    def testShowGui(self):
        self.gui.show()

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()