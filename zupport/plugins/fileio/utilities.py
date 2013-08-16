#!/usr/bin/python
# coding=utf-8

import numpy as np

from errors import ParseError
from core import ParsedFileName

# Amount of bytes required by raster pixel type
PIXELTYPE = {'U1': 0.125,
             '1_BIT' : 0.125,
             'U2': 0.25,
             '2_BIT': 0.25,
             'U4': 0.5,
             '4_BIT': 0.5,
             'U8': 1.0,
             '8_BIT_UNSIGNED': 1.0,
             'uint8': 1.0,
             'S8': 1.0,
             '8_BIT_SIGNED': 1.0, 
             'int8': 1.0,
             'U16': 2.0,
             '16_BIT_UNSIGNED': 2.0,
             'uint16': 2.0,
             'S16': 2.0,
             '16_BIT_SIGNED': 2.0,
             'int16': 2.0,
             'U32': 4.0,
             '32_BIT_UNSIGNED': 4.0,
             'uint32': 4.0,
             'S32': 4.0,
             '32_BIT_SIGNED': 4.0,
             'int32': 4.0,
             'F32': 4.0,
             '32_BIT_FLOAT': 4.0,
             'float32': 4.0,
             'F64': 8.0,
             '64_BIT': 8.0,
             'float64': 8.0}
    
def parse_groups(template, identifier, names, reftable=None, reffields=None):
        ''' Parses a set of of input names based on a name body.
        
        Assumes that a set of input names are structured so that a substring
        within a name defines grouping. Names are parsed based on a common 
        name body tags <BODY>, sub tags <SUB#>  and identifier tags <ID#>. 
        Anything following '.' will be regarded as a file extension.
        
        Anything outside tags is interpreted as separators.
        
        For example name
        
            index_PUULAJI_11_OSITE_3.img
        
        would be described by a template

            <BODY>_<SUB1>_<ID1>_<SUB2>_<ID2>
            
            or
            
            <index>_<PUULAJI>_<#>_<OSITE>_<#>
            
        Extra parameters reftable and reffields can be used to define lookup
        from a provided DataFrame object. In this case reftable defines the 
        DataFrame object and reffields is a tuple containing two strings 
        ("FROM_FIELD", "TO_FIELD") mapping. Actual values are still provided by
        identifier tag <ID#>, but group is based on values in "TO_FIELD".

        Params:
        
        template: string describing the template structure
        identifier: string identifying which tag is used for grouping
        names: a list of strings
        
        Optional params:
        
        reftable: DataFrame providing a lookup table
        reffields: Tuple defining two field names
 
        @return: A dictionary with lists (groups) holding raster names and
                 group value as a key
             
        '''
        groupings = {}
        group = []
        group_id = None
        
        # Check reftable and reffields is provided
        if reftable and not reffields:
            raise ParseError("Reference table provided without reference fields")
        elif reffields and not reftable:
            raise ParseError("Reference fields provided without reference table")
        elif reffields and reftable:
            for field in reffields:
                # If it walks like a duck...
                if field not in reftable.get_fields():
                    raise KeyError("Field %s not present in DataFrame." % field)
        
        if template == '' or template == '.':
            # No template, use all names
            return groupings.append(names)
        else:
            # Parse the actual names based on the template
            for name in names:
                name = ParsedFileName(name, template)
                
                # First time initialize group id
                id = name.get_tag(identifier)
                
                if reftable and reffields:
                    # If reference lookup is needed, do it
                    # At this point we have checked that if reftable exists, 
                    # reffields must exist
                    id = getattr(reftable.where_field_equal(reffields[0], int(id)),
                                 reffields[1])
                    
                if id:
                    if not group_id:
                        group_id = id
                    
                    # Compare the current group id with the previous one
                    if id == group_id:
                        group.append(name)
                    else:
                        if groupings.has_key(group_id):
                            groupings[group_id] = groupings[group_id] + group
                        else:
                            groupings[group_id] = group
                        group = []
                        if reftable and reffields:
                            group_id = getattr(reftable.where_field_equal(reffields[0], 
                                                int(name.get_tag(identifier))),
                                                reffields[1])
                        else:
                            group_id = name.get_tag(identifier)
                        group.append(name)
                else:
                    raise ValueError('Identifier not found in template.')
            
            # Final left over
            if groupings.has_key(group_id):
                groupings[group_id] = groupings[group_id] + group
            else:
                groupings[group_id] = group
            
            # Return a dictionary
            return groupings

def parse_operator(operator):
    if operator == 'SUM':
        return ' + '
    elif operator == 'SUBTRACTION':
        return ' - '
    elif operator == 'MULTIPLICATION':
        return ' * '
    elif operator == 'DIVISION':
        return ' / '
    else:
        raise ValueError('Operator %s not suitable for simple algebra.' %
                            (operator))
def get_nodata_number(dtype):
    '''Returns default NoData representations in numerical form.
    '''
    if dtype in ['float32', 'F32', '32_BIT_FLOAT']:
        return -3.40282346639e+38
    elif dtype in ['float64', 'F64', '64_BIT']:
        return -1.79769313486e+308
    
def pixeltype_to_pixeltype(from_type, to_type):
    '''Function to convert different types of pixel type abbreviations to other
    types.
    
    The recognized type categories are: osgeo, arc_short, arc_long
    '''
    bits = [['', 'U1', '1_BIT'],
            ['', 'U2', '2_BIT'],
            ['', 'U4', '4_BIT'],
            ['uint8', 'U8', '8_BIT'],
            ['int8', 'S8', '8_BIT_SIGNED'],
            ['uint16', 'U16', '16_BIT_UNSIGNED'],
            ['int16', 'S16', '16_BIT_SIGNED'],
            ['uint32', 'U32', '32_BIT_UNISGNED'],
            ['int32', 'S32', '32_BIT_SIGNED'],
            ['float32', 'F32', '32_BIT_FLOAT'],
            ['float64', 'F64', '64_BIT']]
    
    for bit in bits:
        if from_type in bit:
            return (lambda x: {'osgeo': bit[0],
                               'arc_short': bit[1],
                               'arc_long': bit[2]}[x])(to_type)
    
def size_in_mem(size, type, unit='B'):
    
    if isinstance(type, np.dtype):
        type = str(type)
        
    units = {'B': 1,
             'kB': 1000, 
             'MB': 1000000,
             'GB': 1000000000}
    return (size * PIXELTYPE[type] / units[unit])

if __name__ == '__main__':
    print pixeltype_to_pixeltype('int32', 'arc_long')