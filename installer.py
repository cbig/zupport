#!/usr/bin/python
# coding=utf-8

import os
import glob
import shutil
import sys
from optparse import OptionParser
import subprocess
from zupport.utilities import USER_DATA_DIR

def main():
    '''Installer script for deploying Zupport. Must be run from the root folder.
    '''
    
    usage = "Usage: %prog [-c -d -v -q] install | uninstall"
    
    parser = OptionParser(usage)
    parser.add_option("-c", "--clean", dest="clean", default=False,
                      help="Perform a clean install (delete old installation.")
    parser.add_option("-d", "--datadir", dest="datadir", default=None,
                      help="Custom data directory.")
    
    parser.add_option("-r", "--dry-run", default=False,
                      action="store_true", dest="dryrun",
                      help="Dry run installer without actually doing anything.")
    
    parser.add_option("-v", "--verbose", default=True,
                      action="store_true", dest="verbose")
    parser.add_option("-q", "--quiet",
                      action="store_false", dest="verbose")
    
    (options, args) = parser.parse_args()
    
    if len(args) != 1:
        parser.error("Incorrect number of arguments.")
    
    if options.dryrun:
        print '****** DRY RUN *******'

    if options.datadir is None:
        options.datadir = USER_DATA_DIR
    
    if options.clean:
        zupport_installation = r'C:\Python26\ArcGIS10.0\Lib\site-packages\zupport*'
        installation_items = glob.glob(zupport_installation)
        if installation_items:
            print 'Force removing old Zupport installation' 
            for item in installation_items:
                shutil.rmtree(item)
    
    print 'Easy installing Zupport and required dependencies'
    try:
        import setuptools
    except ImportError:
        print 'Installing setuptools'
        
        retcode = subprocess.call(["python", "ez_setup.py"])
        if retcode != 0:
            print 'Error installing setuptools, exiting.'
            sys.exit(0)
    
    print 'Installing other dependencies'
    retcode = subprocess.call(["python", "setup.py", "install"])
    if retcode != 0:
        print 'Error installing dependencies, Zupport may not work correctly.'
    
    target_history_dir = os.path.join(options.datadir, 'history')
    target_plugins_dir = os.path.join(options.datadir, 'plugins')
        
    for directory in [options.datadir, target_history_dir, target_plugins_dir]:
        if os.path.exists(directory) and options.verbose:
            print("\nUsing existing directory: %s" % directory)
        elif not os.path.exists(directory):
            print("Creating directory %s" % directory)
            if not options.dryrun:
                try:
                    os.makedirs(directory)
                except OSError, e:
                    print ("\nERROR: Directory %s cannot be created. %s" % (directory, e))
                    return 1
            
    print "\nCopying data file to user data directory"
    log_ini_file = os.path.abspath('./zupport/resources/logging.ini')
    extent_file = os.path.abspath('./zupport/data/extents.yaml')
    if os.path.exists(log_ini_file):
        if not options.dryrun:
            shutil.copy(log_ini_file, options.datadir)
    else:
        print('ERROR: no .ini-file found at %s' % log_ini_file)
        return 1
    
    if os.path.exists(extent_file):
        if not options.dryrun:
            shutil.copy(extent_file, options.datadir)
    else:
        print('ERROR: no extent file found at %s' % extent_file)
        return 1
        
    print "\nCopying plugins YAML files to user data directory"
    plugin_dir = os.path.abspath("./zupport/plugins")
    if os.path.exists(plugin_dir):
        yaml_files = glob.glob(os.path.join(plugin_dir, '*.yaml'))
        if options.verbose:
            print("Plugins found:")
            for plugin_path in yaml_files:
                plugin_name = os.path.basename(plugin_path).replace(".yaml", "").capitalize()
                print("[%s]: %s" % (plugin_name, plugin_path))
                if not options.dryrun:
                    shutil.copy(plugin_path, target_plugins_dir)
    elif not os.path.exists(plugin_dir) or not yaml_files:
        print("WARNING: no plugin definition files were found in %s" % plugin_dir)
    
    print "\nInstallation finished."
    return 0
    
if __name__ == "__main__":
    sys.exit(main()) 
