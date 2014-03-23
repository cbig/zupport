import numpy as N
import pylab as P
import os
import sys
import re
from types import TupleType
from datetime import date

from core import Sppfactory, Zigcommander

def count_alpha(cell_km, cell_actual, input_value): 
    return (2 * cell_km) / (input_value * cell_actual)

def read_array(filename, dtype, separator=' '):
    """ Read a file with an arbitrary number of columns.
        The type of data in each column is arbitrary
        It will be cast to the given dtype at runtime
    """
    
    cast = N.cast 
    data = [[] for dummy in xrange(len(dtype))]
    
    for line in open(filename, 'r'):
        # Clean out the white spaces
        p = re.compile('[\s]{1,}')
        line = p.sub(separator, line).strip()
        fields = line.split(separator)
        
        if fields[0].isdigit():
            fields = [item for item in fields if item != ""]
            # Leave zero area plots out
            if fields[1] != "0":
                for i, number in enumerate(fields):
                    data[i].append(number)
        # Empty line signifies change in data input
        elif 'Repeat' in fields:
            break
        
    try:
        for i in xrange(len(dtype)):
            data[i] = cast[dtype[i]](data[i])
    except ValueError, e:
        print e
        print data[i]
                        
    
    return N.rec.array(data, dtype=dtype)

def read_ascii_matrix(filename, skip=6, dtype=int):
    """Read in a ESRI ASCII grid skipping first 6 rows and using int as 
    a default dtype. Return a ndarray matrix.
    """
    sys.stdout.write('Reading file <%s>...\n' % filename)
    try:
        return N.loadtxt(filename, skiprows=skip, dtype=dtype)
    except IOError:
        print 'given filename <%s> invalid.' % filename
        print 'Exiting.'
        sys.exit(0)
    
# Different stats & analysis functions
        
def compare_multi_distributions(ND=-1, *args):
    """Comparers distributions for an arbitrary list of matrices. Function
    loops through all matrices and defines which elements overlap (=have value
    in all matrices). All matrices MUST be of same dimensions!
    """
    
    # Initialize the resulst list
    results = []
    
    # Check that all matrices have the same dimensions and type
    reftype = type (args[0])
    refdims = (N.size(args[0], 0), N.size(args[0], 1))
    
    for i, matrix in enumerate(args):
        dims = (N.size(matrix, 0), N.size(matrix, 1))
        try:
            assert type(matrix) is reftype, "Mismatch of type <%s> for matrix %s: %s"  \
                                        % (reftype, i+1, type(matrix))
            assert refdims == dims, "Mismatch of dimensions for matrix: " + \
                                    str(i+1) + " " + str(dims)
        except AssertionError, e:
            print '%s, exiting...' % e
            sys.exit(0)
        
        # Append an empty list to results list for later use
        results.append([])
    
    # Loop through matrices
    for i in refdims[0]:
        for j in refdims[1]:
            elems = []
            for i, matrix in enumerate(args):
                elems[i] = matrix[i, j]
        # for elems
            
def compare_distributions(matrix1, matrix2, NDs=[-1, -2]):
    """Comparers distributions for two matrices. Function
    loops through the two matrices and defines which elements overlap (=have value
    in all matrices). Both matrices MUST be of same dimensions! Also assumes
    that NoData values of an matrix are negative integers and actual values
    positive integers.
    """
    
    sys.stdout.write('Comparing distributions...\n')
    
    # Initialize the results dictionary: 
    results = {'matrix1': 0, 'both':0, 'matrix2': 0}
    
    # Check that all matrices have the same dimensions and type
    type1 = type(matrix1)
    dims1 = (N.size(matrix1, 0), N.size(matrix1, 1))
    dims2 = (N.size(matrix2, 0), N.size(matrix2, 1))
    try:
        assert type(matrix2) is type1, "Matrix types do not match"
        assert dims1 == dims2, "mismatch of dimensions for matrix"
    except AssertionError, e:
        print '%s, exiting...' % e
        sys.exit(0)

    # Loop through matrices
    for i in xrange(dims1[0]):
        for j in xrange(dims1[1]):
            val1 = matrix1[i, j]
            val2 = matrix2[i, j]
            if val1 not in NDs and  val2 in NDs:
                results['matrix1'] += 1
            elif val1 not in NDs and  val2 not in NDs:
                results['both'] += 1
            elif val1 in NDs and  val2 not in NDs:
                results['matrix2'] += 1
    
    print 'done.'
    return results

def create_matrix(x, y, p):
    
    randmat = N.random.rand(x, y)
    matrix = N.zeros((x, y), int)
    
    for i in xrange(x):
        for j in xrange(y):
            if randmat[i, j] < p:
                matrix[i, j] = 1
            else:
                matrix[i, j] = -1
    
    return matrix


def make_comparisons(wdir, basedir, files, sequence, verbose=True, ext=''):
    """Function to go through all Z solution folders in a given wdir folder
    based on sequence provided by tuple sequence. Each folder is identified
    by integer id number in the beginning of the folder name. Single basedir
    is given followed by files which is a list of files in basedir that will
    work as reference for comaprison. 
    """
    # Determine whether the sequence is a list of folders or a range
    # Else it is assumed that sequnce is already a list containing folder ids
    if type(sequence) is TupleType:
        folder_ids = range(sequence[0], sequence[1] + 1)
    else:
        folder_ids = sequence
    
    # List all folders in the working directory
    folders = os.listdir(wdir)
    
    # Prepare reference directory and files and check that they exist
    ref_id = int(basedir.split('_')[0])
    for i, file in enumerate(files):
        files[i] = os.path.join(wdir, basedir, file)
        if not os.path.exists(files[i]):
            print 'Reference file %s does not exist!' % files[i]
            sys.exit(0)
    # If reference directory is included in folder_ids, remove it
    if ref_id in folder_ids:
        folder_ids.remove(ref_id)
    
    # Create a dictionary where folder id is key and target file name value
    f_dict = {}
    
    for folder in folders:
        for file in files:
            if os.path.isdir(os.path.join(wdir, folder)) and '_' in folder:
                f_id = int(folder.split('_')[0])
                t_name = os.path.join(wdir, folder, os.path.basename(file))
                if f_id in folder_ids and f_id:
                    if os.path.exists(t_name):
                        f_dict[f_id] = t_name
                    else:
                        print 'Target file %s does not exist!' % t_name
                        sys.exit(0)
    
    # Initialize oputput formats
    l_header = ['FID',
                'Case',
                'Union',
                'Intersect',
                'Overlap',
                'Matrxi1',
                'Matrix2',
                'File',
                'Time']
    s_header = '\t'.join(l_header)
    
    # Open output file
    out_name = os.path.join(wdir, basedir, 'com_dist_%s%s.txt' % (ref_id, ext))
    if os.path.exists(out_name):
        out_file = open(out_name, 'a')
    else:
        out_file = open(out_name, 'w')
        out_file.write(s_header + '\n')
    
    for file in files:
        matrix1 = read_ascii_matrix(file)
        for i, case in enumerate(folder_ids):
            matrix2 = read_ascii_matrix(f_dict[case])
            distsums = compare_distributions(matrix1, matrix2)
            msum = sum([s for s in distsums.values()])

            s_results = '\t'.join(map(str, [(i + 1),
                                  case,
                                  msum, 
                                  distsums['both'], 
                                  (float(distsums['both']) / float(msum)),
                                  distsums['matrix1'],
                                  distsums['matrix2'],
                                  f_dict[case],
                                  date.today().isoformat()]))
            
            out_file.write(s_results + '\n')
            if verbose:
                print
                print s_header
                print s_results
                print

    out_file.close()

def check_folder(folder, suffix):
    today = date.today().isoformat().replace('-', '')
    # Get existing dirs in output_parent
    folders = os.listdir(folder)
    # Loop through folders and get id number
    ids = []
    for folder in folders:
        try:
            ids.append(int(folder[:2]))
        except ValueError:
            pass
    
    num = max(ids) + 1
        
    if num < 10:
        num = '0%s' % num
            
    target = os.path.join(folder, '%s_%s_%s' % (num, today, suffix))
    if not os.path.exists(target):
        os.mkdir(target)
    return target

def check_weight(item):
    if '_w_' in item:
        return 1
    elif '_wl_' in item:
        return 2
    elif '_abc_' in item:
        return 3
    else:
        return 0
    
def check_alpha(item):
    if '_ds_' in item:
        return True
    else:
        return False
    
def check_method(item):
    if 'caz' in item:
        return 1
    elif 'abf' in item:
        return 2
    elif 'tbp' in item:
        return 3
    else:
        return 4

def operate(runs, spp_xlfile, spp_xlsheet, mask_file=None, 
            pp_file=None, interact=None, conn=None, grps=None, blp=0.0):
    
    # Initiate the batch file for running Zonation
    batchfile = ''
    today = date.today().isoformat().replace('-', '')
    
    for run in runs:
        
        # Before starting, mark masks if used
        if mask_file is not None:
            run = run + '_mask'
            
        # First, create a Zigcommander object with which operations
        # are handlded
        com = Zigcommander(run)
        
        # Second, create necessary sppfile(s)
        # Notice that process will be terminated if ASCII files do not exist
        spp = Sppfactory(run)
        
        # Third, handle the right folder
        homefolder = check_folder(today, run)
        
        # Third, create run settings file (based on default)
        configfile = os.path.join(homefolder,(run + '.dat'))
        dat = com.create_config_file(configfile, use_default=True)
        dat.set_value('Settings', 'removal rule', check_method(run))
        
        if blp is not None:
            if blp > 0:
                dat.set_value('Settings', 'BLP', float(blp))
            else:
                print "BLP value must be positive: %s." % blp
        
        if mask_file is not None:
            if os.path.exists(mask_file):
                dat.set_value('Settings', 'use mask', '1')
                dat.set_value('Settings', 'mask file', mask_file)
            else:
                print "Mask file does not exist in path specified: %s." % mask_file
        
        # Fourth, create post processing capability if needed
        if pp_file is not None:
            if os.path.exists(pp_file):
                dat.set_value('Settings', 'post-processing list file', 
                              pp_file)
            else:
                print "Post processing file does not exist in path specified: %s." % mask_file
            
        if interact is not None:
            if os.path.exists(interact):
                dat.set_value('Settings', 'use interactions', 1)
                dat.set_value('Settings', 'interaction file', interact)
            else:
                print 'Interaction file does not exist in path specified: %s' % interact
                
        if conn is not None:
            if os.path.exists(conn):
                dat.set_value('Community analysis settings', 'load similarity matrix', 
                              1)
                dat.set_value('Community analysis settings', 'similarity matrix file', 
                              conn)
            else:
                print "Connectivity matrix file does not exist in path specified: %s." % conn
                
        if grps is not None:
            if os.path.exists(grps):
                dat.set_value('Settings', 'use groups', 
                              1)
                dat.set_value('Settings', 'groups file', 
                              grps)
            else:
                print "Groups file does not exist in path specified: %s." % grps
        
        # If 'dsb' -flag is found inside th edefinition string
        # create a spp file with same layers with and without DS
        if 'dsb' in run:
            spp.add_to_rack(path=spp_xlfile, 
                            sheet=spp_xlsheet,
                            weight=check_weight(run), 
                            alpha=check_alpha(run), 
                            method=check_method(run))
            spp.add_to_rack(path=spp_xlfile, 
                            sheet=spp_xlsheet,
                            weight=check_weight(run),
                            # Also the opposite of alpha 
                            alpha=(not check_alpha(run)), 
                            method=check_method(run))
        else:
            spp.add_to_rack(path=spp_xlfile, 
                            sheet=spp_xlsheet,
                            weight=check_weight(run), 
                            alpha=check_alpha(run), 
                            method=check_method(run))
        
        sppfile = os.path.join(homefolder,(run + '.spp'))
        spp.printfile(dirname=sppfile, exclude=['id'])
        
        # If everything was okay, write the dat file as well
        dat.write()
        
        # Sixth, create the batchrun capability
        batchname = today + '_run_all.bat'
        com.create_run_object(settings=configfile, 
                              sppfiles=sppfile,
                              output=os.path.join(homefolder, 'output.txt'),
                              DS=int(check_alpha(run)))
        
        batchfile = com.create_batch_file(output=batchname, 
                                          exclude=['id'], 
                                          append=True)
    # Finally, execute the batch file
    #os.system(batchfile)

if __name__ == '__main__':
    
    pass
#    wdir = r'E:\Data\Zonation\output\metsatalousmaa'
#    basedir = r'50_20081113_A2_met_300_in_w_cds_abf_mask'
#    files = ['output.ABF_MEABLP0.nwout.7.ras.asc'
#             #'output.ABF_MEABLP0.nwout.7.ras.asc'
#             ]
#    
#    make_comparisons(wdir, basedir, files, [49], ext='_50k')
    
    '''file1 = r'E:\Data\Zonation\output\metsatalousmaa' + \
            r'\45_20081113_A2_met_300_in_w_cds_abf_mask' + \
            r'\output.ABF_MEABLP0.nwout.6.ras.asc'
            
    file2 = r'E:\Data\Zonation\output\metsatalousmaa' + \
            r'\45_20081113_A2_met_300_in_w_cds_abf_mask' + \
            r'\output.ABF_MEABLP0.nwout.7.ras.asc'
            
    file3 = r'C:\Data\Zonation\output\metsatalousmaa' + \
            r'\33_uusi_noBLP' + \
            r'\output.ABF_MEABLP2.nwout.6.ras.asc'
            
    matrix1, matrix2 = read_ascii_matrix(file1), read_ascii_matrix(file2)
    d = compare_distributions(matrix1, matrix2)
    msum = sum([s for s in d.values()])
    print
    print 'Union disribution sum of matrices is: %s' % msum
    print 'Itersection distribution sum of matrices is: %s' % d['both']
    print 'Overalap is: %s' % (float(d['both']) / float(msum))
    print 'Matrix1 has %s unique elements' % d['matrix1']
    print 'Matrix2 has %s unique elements' % d['matrix2']
    print
    
    #TODO: get headers right
    mydescr = N.dtype([('Network', 'int32'), 
                       ('Area', 'int32'), 
                       ('Mean-Rank', 'float32'), 
                       ('X', 'float32'),
                       ('Y', 'float32'),
                       ('Spp_distribution_sum', 'float32'),
                       ('spp occurring', 'int32'),
                       ('>10%', 'int32'),
                       ('>1%', 'int32'),
                       ('>0.1%', 'int32'),
                       ('>0.01%', 'int32')])
    
    file = r'E:\Data\Zonation\nwoutspp6.txt'
    if os.path.exists(file):
        myrecarray = read_array(file, mydescr, separator='\t')
    else:
        print 'Inputfile not valid!'
        sys.exit(0)
    
    dim = len(myrecarray)
    # Resolution in Km
    res = 0.5
    # Extents in YKJ, DO NOT CHANGE THESE!!!
    extents = {'north': [3243187.5, 7255237.5, 3628087.5, 7779737.5],
               'south': [3159087.5, 6620112.5, 3733087.5, 7378212.5],
               'whole': [3159087.5, 6620037.5, 3733187.5, 7779737.5],
               'metso': [3159087.5, 6620037.5, 3733187.5, 7372512.5],
               'local': [3514667.5, 7284110.5, 3614668.5, 7384111.5]} 
    area = 1
    av_rank = 2
    x_coord = 3
    y_coord = 4
    
    x = N.zeros(dim, dtype='float32')
    y = N.zeros(dim, dtype='float32')
    a = N.zeros(dim, dtype='float32')
    
    for i in xrange(dim):
        #x[i] = res * (myrecarray[i][x_coord] + extents['whole'][0])
        #y[i] = myrecarray[i][y_coord]/2
        #y[i] = res * (extents['whole'][3] - myrecarray[i][y_coord])
        x[i] = myrecarray[i][area]
        y[i] = myrecarray[i][av_rank]

    
    # the bestfit line from polyfit
    m1, b1 = S.polyfit(x, y, 1) # a line is 1st order polynomial...
    a_s, b_s, r_value, p_value, stderr = stats.linregress(x, y)
    #m2, b2 = N.polyfit(x, a, 1)
    
    print 'm1: %s' % m1
    print 'b1: %s' % b1
    print 'a_s: %s' % a_s
    print 'b_s: %s' % b_s
    print 'R-squared: %.6f' % r_value ** 2
    print 'p-value: ', p_value
    
    P.subplot(211)
    #p.plot(x, y, 'ro')
    P.plot(x, y, 'ro', x, a_s * x + b_s, '-k', linewidth=2)
    P.axis([min(x), max(x), min(y), max(y)])
    P.ylabel('Rank')
    P.xlabel('Area')
    P.grid(True)
    
    
    P.subplot(212)
    n, bins, patches = P.hist(x, 150, normed=1)
    P.setp(patches, 'facecolor', 'g', 'alpha', 0.75)
    
    #p.plot(x_flip, y_flip, 'bo')
    ##p.plot(x, y, 'ro', x, a_s * x + b_s, '-k', linewidth=2)
    #p.axis([0, x_range, 0, y_range])
    P.ylabel('Freq')
    P.xlabel('Area')
    P.grid(True)
    
    #p.subplot(212)
    #p.plot(x, a, 'bo', x, m2 * x + b2, '-k', linewidth=2)
    #p.ylabel('Area')
    #p.xlabel('Rank')
    #p.grid(True)
    
    P.show()
    
    linregr()'''
    
