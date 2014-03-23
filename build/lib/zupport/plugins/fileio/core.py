import glob
import os
import re
from types import IntType

from yaml import safe_load, dump

from zupport.utilities.odict import OrderedDict

from errors import ParseError

class FileGroupIterator(object):
    
    def __init__(self, inputws, wildcard, template, grouptags=None, 
                 groupmap=None):
        
        self.workspace = self.parse_workspace(template, inputws, wildcard)
        self.groups = OrderedDict()
        self.grouptags = grouptags
        if self.grouptags is not None:
            self.set_grouping(grouptags, groupmap)
            
    def __iter__(self):
        return self
    
    def __len__(self):
        return len(self.groups)
    
    def iteritems(self):
        for item in self.groups.iteritems():
            yield item
    
    def next(self):
        if not self.groups:
            raise StopIteration
        values = self.groups.popitem(0)
        return values
        
    def parse_workspace(self, template, inputws, wildcard):
        return ParsedWorkspace(template, inputws, wildcard)
        
    def set_grouping(self, tags, mapping=None):
        ''' Sets the grouping order of the workspace. Tags is a list of tags 
        found in ParsedFileNames. If only tags are provided, then they are 
        directly used as the basis of grouping. If an additional mapping is
        provided, it will be used. Mapping is a dict with original tag values
        as keys and mapping values as values.
        '''
        
        ws_objects = self.workspace.files
        
        for item in ws_objects:
            for tag in tags:
                if tag not in item.tags:
                    raise ValueError('%s is not a valid grouping tag' % tag)
            tag_values = item.get_tags(tags)
            if mapping:
                for value in tag_values:
                    if value not in item.tags.values():
                        raise ValueError('%s is not a valid grouping tag' % value)
                    if value not in mapping.keys():
                        raise ValueError('%s is not in mapping keys [%s]' % (value, mapping))
                    mapped_value = mapping[value]
                    if mapped_value in self.groups.keys():
                        self.groups[mapped_value].append(item)
                    else:
                        self.groups[mapped_value] = [item]
            else:
                if tag_values in self.groups.keys():
                    self.groups[tag_values].append(item)
                else:
                    self.groups[tag_values] = [item]
                
        self.grouptags = tags            

class ParsedFileName(object):
    
    def __init__(self, name, template):
        self.__name = os.path.basename(name)
        self.__path = name
        self.__template = template
        self.__tags = {}
        self.__order = []
        self.parse()
        
    def __str__(self):
        return self.name

    def parse(self):
        # Parse the template
        # Standard regex to find HTML tags
        re_tag = re.compile('(\<(/?[^\>]+)\>)', re.IGNORECASE)
        tags = re_tag.findall(self.template)

        # Get the separators
        re_sep = re.compile('((?<=>))(.(?=<))')
        seps = re_sep.findall(self.template)
        
        extension = ''
        separator = ''
        
        if '.' in self.name:
            re_ext = re.compile(r'\.([A-Za-z0-9-]+)')
            extensions = re_ext.findall(self.name)
            # If more tha 1 extension is found, only use the last one
            if len(extensions) > 1:
                extensions = [extensions[-1]]
            # FIXME: the dot should be part of the regex
            extension = '.' + extensions[0]
            self.set_tag('EXT', extension)
        
        # Separators*should* be the same, but strictly
        # they don't have to
        if seps:
            separator = seps[0][1]
            name_body = self.name.replace(extension, '')
            components = name_body.split(separator)
        else:
            # No separator provided, template must be followed literally    
            raise NotImplementedError("Name templating without separator not supported.")
        
        self.set_tag('SEP', separator)
        
        if len(components) != len(tags):
            raise ParseError("Template %s and name %s don't match" % 
                            (self.template, self.name))
        
        # Fill tag values with current components
        for tag, component in zip(tags, components):
            # Find out if component is numerical
            if component.isdigit():
                component = float(component)
            self.__order.append(tag[1])
            self.set_tag(tag[1], component)

    @property
    def body(self):
        value = []
        for i, item in enumerate(self.__order):
            if 'BODY' in item:
                value.append(self.get_tag(item))
        
        return self.separator.join(value)

    @property
    def extension(self):
        return self.get_tag('EXT')

    @property
    def name(self):
        return self.__name

    @property
    def path(self):
        return self.__path

    @property
    def separator(self):
        return self.get_tag('SEP')

    @property
    def tags(self):
        return self.__tags

    def get_tag(self, token):
        if type(token) == str or type(token) == unicode:
            if token in self.__tags.keys():
                return self.__tags[token]
            else:
                return None
        elif type(token) == int:
            if token >= 0 and token <= len(self.__order):
                return self.__order[token]
            else:
                return None

    def get_tags(self, tokens):
        if type(tokens) == list or type(tokens) == tuple: 
            tags = []
            for token in tokens:
                if type(token) == str or type(token) == unicode:
                    if token in self.__tags.keys():
                        tags.append(self.__tags[token])
                elif type(token) == int:
                    if token >= 0 and token <= len(self.__order):
                        tags.append(self.__order[token])
            return tuple(tags)
        else:
            raise ValueError, "Token must be either a list or a tuple"

    def get_template(self):
        return self.__template
        
    def set_tag(self, key, value):
        self.__tags[key] = value
        
    def set_template(self, value):
        self.__template = value
        
    template = property(get_template, set_template, None, "template's docstring")


class Workspace(object):
    """Utility class to list all or specific files in a file system folder
    (workspace). Object is iterable returning next file in the list.

    .. testsetup:: workspace

       import workspace
       import os

    .. doctest:: workspace

       >>> ws = Workspace(os.path.abspath('../data'))
       >>> print ws
       docs.xml
       docs.yaml
       >>> ws.filter('xml')
       >>> print ws
       docs.xml
       >>> ws.path = os.path.abspath('../fakedir')
       Traceback (most recent call last):
         ...
       ValueError: Workspace path does not exist.

    """

    def __init__(self, inpath, wildcard='*', recursive=False):
        """Constructor will look for existing file system path as defined by
        *inpath* and list all files in this workspace. Parameter *filter*
        is used as :mod:`glob` wildcard to define workspace file filter.
        *recursive* determines whether the search decends into subfolders.
        """
        self.path = inpath
        self.wildcard = wildcard
        self.recursive = recursive
        self._files = []
        self.refresh()

    def __iter__(self):
        return self

    def __str__(self):
        return '\n'.join([infile for infile in self.files])

    @property
    def files(self):
        """Returns a list of all files currently listed in the workspace.
        """
        return self._files

    def next(self):
        if not self._files:
            raise StopIteration
        return self._files.pop(0)

    def refresh(self):
        """Method refreshes the list of files in the current workspace. The
        result is affected but *path*, *filter* and *recursive* instance
        attributes set at the time of object instantiation.
        """
        if self.recursive:
            # TODO: implement this
            pass
        else:
            searchpath = os.path.join(self.path, '*.' + self.wildcard)
            files = glob.glob(searchpath)
            self._files = [os.path.basename(file) for file in files]
            if len(self.files) == 0:
                print 'Created an empty workspace.'

    def filter(self, filter):
        """Sets the workspace file filter to *filter*.
        """
        self.wildcard = filter
        self.refresh()

    def get_path(self):
        return self._path

    def set_path(self, path):
        if os.path.exists(path):
            self._path = path
        else:
            # TODO: log
            raise ValueError('Workspace path %s does not exist.' % path)

    path = property(get_path, set_path, None, "Path to an existing location \
                                                in the file system.")

class ParsedWorkspace(Workspace):
    '''Extends the regular workspace by being able to parse and process file
    names within the workspace. Instead of referring to individual files by
    path strings, ParserWorkspace contains files as instances of 
    ParsedFileName class.'''
    
    def __init__(self, template, *args, **kwargs):
        self._template = template
        Workspace.__init__(self, *args, **kwargs)

    def __getitem__(self, key):
        if type(key) is IntType:
            if key < -1 or key > len(self):
                raise IndexError('Index out of bounds')
            else:
                return self._files[key]
        else:
            raise TypeError('Only integer keys are valid')
        
    def __len__(self):
        return len(self._files)
    
    @property
    def files(self):
        """Override Workspace
        """
        return [filename for filename in self._files]
    
    @property
    def tags(self):
        """Return all the tags in the parsed file names.
        """
        [filename for filename in self._files.path]
    
    def refresh(self):
        """Override Workspace method
        """
        if self.recursive:
            # TODO: implement this
            pass
        else:
            searchpath = os.path.join(self.path, self.wildcard)
            files = glob.glob(searchpath)
            #files = [os.path.basename(file) for file in files]
            if len(files) == 0:
                print 'Created an empty workspace.'
            else:
                try:
                    self._files = [ParsedFileName(_file, self._template) for _file in files]
                except ParseError:
                    raise

class Yamlwrapper(object):
    '''
    A simple yaml wrapper for various tasks.
    '''

    def __init__(self, yaml_file):
        '''
        Loads in the yaml file
        '''
        try:
            self.data = safe_load(file(yaml_file, 'r'))
        except IOError, e:
            print e
        self.levels, self.nodes = self.__get_structure()
    
    def __build_branch(self, branch):
        str_branch = []
        prev_child = ''
        prev_parent = ''
        for node in branch:
            parent = node.keys()[0]
            child = node.values()[0]
            if parent == 'root' or prev_child == parent:
                str_branch.append(child)
            elif prev_parent == parent:
                break
            else:
                raise ValueError, 'Branch structure invalid: %s' % branch
            prev_child = child
            prev_parent = parent
        return ' -> '.join([node for node in str_branch])
    
    def __get_structure(self):
        tree = []
        # First root level
        for key, item in self.data.iteritems():
            root = key
            levels = 1
            branch = []
            branch.append({'root': root})
            # See nested levels
            while isinstance(item, dict):
                for key, item in item.iteritems():
                    levels += 1
                    branch.append({root: key})
                root = key
            tree.append(branch)
        return levels, tree
    
    def __find_node(self, target):
        locations = []
        for branch in self.nodes:
            for node in branch:
                keys, values = node.keys(), node.values()
                if target in keys or target in values:
                    locations.append(branch)
        return locations
    
    def get_node(self, *args):
        for arg in reversed(args):
            locations = self.__find_node(arg)
            if len(locations) > 1 and len(args) == 1:
                print 'Node <%s> is ambiguous and can be found in the following locations:' % arg
                for branch in locations:
                    try:
                        print '<%s>' % self.__build_branch(branch)
                    except ValueError, e:
                        print e
                print 'Use the first node to select the right branch.'
            else:
                pass
        '''if node in self.data.keys():
            return self.data[node]
        else:
            for vals in self.data.values():
                while isinstance(vals, dict):
                    if node in vals.keys():
                        return vals[node]
                    else:
                        vals = vals.values()'''
    
    def show(self):
        print dump(self.data)
                
def get_tools():
    import inspect
    import tools
    return ([(name, data) for name, data in 
                                inspect.getmembers(tools, inspect.ismodule)])
    
if __name__ == '__main__':
    iterator = FileGroupIterator(inputws=r'C:\Data\Staging\Output\MK_puusto\ositteet',
                                wildcard="*.img",
                                template='<BODY1>_<ID1>_<BODY2>_<ID2>_<BODY3>',
                                grouptags=['ID1', 'ID2'])
    
    print 'Grouping based on tags: %s' % iterator.grouptags
    for tags, item in iterator:
        for raster in item:
            print('Tag values: %s => filename: %s' % (tags, raster.name))
    
    iterator.set_grouping(['ID1'])
    print 'Grouping based on tags: %s' % iterator.grouptags
    for tags, item in iterator:
        for raster in item:
            print('Tag values: %s => filename: %s' % (tags, raster.name))
            
    mapping = {'1': '1', '2': '1', '3': '2'}
    iterator.set_grouping(['ID2'], mapping)
    print 'Grouping based on tags: %s' % iterator.grouptags
    for tags, item in iterator:
        for raster in item:
            print('Tag values: %s => filename: %s' % (tags, raster.name))