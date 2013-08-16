import os

from zope.interface import implements
from zupport.interfaces import IGISTool

from ..core import ArcTool
from ..errors import FeatureTypeError, FieldError, LicenseError
from zupport.utilities import (msgInitStart, msgInitSuccess)
from zupport.zlogging import ArcLogger

def service():
    return 'discretizefields'

def setup(parameters, *args, **kwargs):
    return DiscrertizeFields(parameters, service=service(), *args, **kwargs)

class DiscrertizeFields(ArcTool):
    """
    

    """
    implements(IGISTool)

    id = 0

    def __init__(self, parameters, service, *args, **kwargs):
        ArcTool.__init__(self, parameters, service, *args, **kwargs)

        DiscrertizeFields.id = DiscrertizeFields.id + 1
        self.name = self.__class__.__name__
        # Identifier is a combination of the name and the class counter
        self.id = (self.name, DiscrertizeFields.id)
        
        self.log = ArcLogger("Zupport.%s" % (self.__class__.__name__), 
                                             debugging=True)
        
        self.log.debug(msgInitStart)
        # Tool needs spatial analyst in order to run
        # TODO: this should be moved to ToolValidator
        try:
            self.register_extension('spatial')
        except LicenseError, e:
            self.log.error(e)
            return 1
        
        self.service = service
        
        self.log.debug(msgInitSuccess)

    def __del__(self):
        if DiscrertizeFields:
            DiscrertizeFields.id = DiscrertizeFields.id - 1

    def run(self):
        
        self.validate_parameters()
        
        intable = str(self.get_parameter(0))
        intable_discrete_field = str(self.get_parameter(1))
        intable_join_field = str(self.get_parameter(2))
        infeature = str(self.get_parameter(3))
        infeature_join_field = str(self.get_parameter(4))
        join_type = str(self.get_parameter(5))
        output_feature = str(self.get_parameter(6))
        self.log.debugging = bool(self.get_parameter(7))
        
        self.gp.env.workspace = os.path.dirname(intable)
        # Must use unqualified names! Avoid identical field names.
        self.gp.env.qualifiedFieldNames = False
        
        try:
            # Check input feature properties
            self.log.debug('Getting Feature Class properties')
            fc_desc = self.gp.Describe(infeature)
            if fc_desc.ShapeType != "Polygon":
                raise FeatureTypeError("Input Feature Class type (%s) not polygon." % fc_desc.ShapeType)
            
            self.log.debug('Checking if input feature join field %s exists' % infeature_join_field)
            if not self.gp.ListFields(infeature, infeature_join_field):
                raise FieldError(infeature_join_field, infeature)
        
            self.log.debug('Checking if input table %s fields exist' % intable)
            fields = [field.name for field in self.gp.ListFields(intable)]
            self.log.debug(fields)
            if intable_discrete_field not in fields:
                raise FieldError(intable_discrete_field, intable)
            if intable_join_field not in fields:
                raise FieldError(intable_join_field, intable)

            # STEP 1: Get the unique values ###################################
            
            # Get the unique values in the discrete field
            self.log.debug('Getting all unique values for field %s' % intable_discrete_field)
            
            # Use a set to get the unique field identifiers
            values = set()
            
            # FIXME: using search cursor can be slow...
            nrows = self.gp.GetCount_management(intable)
            self.log.debug("Row count: %s" % nrows)
    
            #rows = self.gp.SearchCursor(intable)

            #for row in rows:
            #    values.add(int(row.getValue(intable_discrete_field)))
             
            # HACK!
            values = set([1, 2, 3, 4, 5, 6, 7, 8, 9])
                
            self.log.debug('Unique values for %s: %s' % (intable_discrete_field, 
                                                         values))
            
            for value in values:
                
                # STEP 2: Select the rows from the input table with the current
                # value.
            
                selection_table = "selection_table"
                join_layer = "join_layer"
                
                where_clause = '"%s" = %s' % (intable_discrete_field, value)
                
                self.log.debug('Making table view from table %s with %s' % (intable, where_clause))
                
                # Make a table view with the where selection
                self.gp.MakeTableView_management(intable, selection_table, 
                                                 where_clause) 
                
                # STEP 3: Join the selected table with a Feature layers created
                # out of the input feature (geometry feature)
                self.log.debug('Creating a feature layer from %s' % (infeature))
                
                self.gp.MakeFeatureLayer_management(infeature, join_layer)
                
                self.log.debug('Joining %s and %s' % (infeature, 
                                                      intable))
                
                self.log.debug('Using join type: %s ' % join_type)
                
                self.gp.AddJoin_management(join_layer, infeature_join_field,
                                           selection_table, intable_join_field,
                                           join_type=join_type)
                
                
                nrows = int(self.gp.GetCount_management(join_layer).getOutput(0))
                if join_type == 'KEEP_COMMON':
                    self.log.debug('%s rows selected and joined' % nrows)
                    if nrows < 1:
                        self.log.debug('No records selected, continuing')
                        continue
                else:
                    self.log.debug('All geometry rows (%s) selected.' % nrows)
                    
                # STEP 4: Make a temporary feature class out of the Feature 
                # class

                out_path = os.path.dirname(output_feature)
                out_name = os.path.basename(output_feature)
                temp_feature = os.path.join(out_path, out_name + '_temp')
                self.log.debug('Creating temporary feature class %s' % temp_feature)
                self.gp.CopyFeatures_management(join_layer, 
                                                temp_feature)
                
                # STEP 5: Check if the output feature class exists and if not,
                # create one with the appropriate template (temporary feature 
                # class created in the previous step)
                if not self.gp.Exists(output_feature):
                    
                    geometry_type = "POLYGON"
                    
                    self.log.debug('Creating output feature class %s to %s' % (out_name, out_path))
                    
                    self.gp.CreateFeatureclass_management(out_path, out_name, 
                                                          geometry_type,
                                                          template=temp_feature)
                
                # STEP 6: Append all the features from the current 
                # selection/join to the output feature class
                
                nrows = int(self.gp.GetCount_management(temp_feature).getOutput(0))
                self.log.debug('Appending %s features to %s' % (nrows, out_name))
                self.gp.Append_management(temp_feature, output_feature, 
                                          schema_type="TEST")

                # STEP 7: Remove joins and the Table Views
                self.log.debug('Removing temporary data')
                self.gp.Delete_management(join_layer)
                self.gp.Delete_management(selection_table)
                if self.gp.Exists(temp_feature):
                    self.gp.Delete_management(temp_feature)
            
        except FeatureTypeError, fte:
            self.log.exception(fte.value)
            raise

        except FieldError, fe:
            self.log.exception(fe.value)
            raise
        
            