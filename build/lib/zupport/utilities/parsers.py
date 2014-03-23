# coding=utf-8

import os
import re




        
if __name__ == '__main__':
    name = 'index_PUULAJI_10_OSITE_NO_3.img'
    template = '<ID1>_<BODY1>_<BODY2>_<SUB2>_<SUB3>_<ID2>'
    cn = ComplexName(name, template)
    print cn
    print cn.name
    print cn.extension
    print cn.body
    print cn.tags
    print cn.get_tag(1)
    print cn.get_tag('ID1')
    print cn.separator