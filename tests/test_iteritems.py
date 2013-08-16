'''
Created on 30.11.2011

@author: admin_jlehtoma
'''
class IterTester(object):
    
    def __init__(self, keys, values):
        self._dict = {}
        if len(keys) == len(values):
            for key, value in zip(keys, values):
                self._dict[key] = value
    
    def __str__(self):
        return str(self._dict)
                
    def iteritems(self):
        for key, value in self._dict.iteritems():
            yield (key, value)
                
if __name__ == '__main__':
    o = IterTester(['A', 'B'], [[1, 2, 3], [2, 5, 7]])
    print(o)
    for key, value in o.iteritems():
        print key, value