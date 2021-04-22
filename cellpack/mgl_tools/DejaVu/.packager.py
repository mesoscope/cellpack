# The .packager.py is used by the DistTools package to get the files to be
# included in a distribution.
def getFiles(root, what = 'all', plat=None):
    """
    files <- getFiles(root, what='all', plat=None)

    files -- list of the files to be included in the download

    arguments:
    root -- path to the package. This is used by glob to get all the python
            modules.
    what -- string that can be 'all' and 'supported' to specified what files
    to include in the distribution. By default 'all' the files are added.
    plat -- platform ('linux2', 'irix646', 'sunos5' etc...)
    """
    import os
    from glob import glob
    # 1- Specify the list of all the Python module
    allPyModule = ["*.py", "ViPEr/*.py", "materialsDef/*.py", 'gui/*.py']

    # 2- Specify the list of the non supported Python module. These files
    # will be removed from the release of the supported python modules.
    pynotsupported = []

    # 3- Specify the documentation files and directories to be included in the
    # release
    docFiles = ["Tutorial"]
    
    # 4-Specify the extraFiles to be included in the release.
    extraFiles = ["*.ppm",
                  'CVS',
                  "ViPEr/CVS", "materialsDef/CVS", 'gui/CVS',
                  "RELNOTES"]
 
    # 5-Specify the testFiles to be included in the release.
    testFiles = ["Tests","ViPEr/Tests"]



    
    #########################################################
    ## Where things are done for you .
    #########################################################
    # if some files need to be removed, we need the exact list of the pymodule.
    if len(pynotsupported):
        # store the path of the current directory
        olddir = os.getcwd()
        os.chdir(root)
        files = []
        # we use glob to get the exact list of files.
        for p in allPyModule:
            files = files + glob(p)
        allPyModule = files
        files = []
        # need to get the list of the files ... no wild card possible.
        for p in pynotsupported:
            files = files + glob(p)
        pynotsupported = files
        os.chdir(olddir)
    # Creation of the proper list of files depending on the value of what
    
    if what == 'supported' and len(pynotsupported):
        # need to remove the non supported python files from all the python
        # files
        # These are the keys used for to make the releases...
        supportedFiles = filter(lambda x, l = pynotsupported:
                                    not x in l, allPyModule)
        
        return supportedFiles + testFiles + extraFiles
    
    elif what == 'all' or ( what == 'supported' and not len(pynotsupported)):
        # Other wise just add the documentation, test and extra files to all
        # the python modules.
        allFiles= allPyModule + docFiles + testFiles + extraFiles
        return allFiles
    elif what == 'documentation':
        return docFiles
    else:
        return []



