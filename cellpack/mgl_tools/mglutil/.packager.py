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

    # 1- List all the python modules of that package
    allPyModule = ["*.py", "math/*.py", "gui/*.py", "util/*.py",
                   "web/*.py", "gui/BasicWidgets/*.py","gui/InputForm/*.py",
                   "gui/Misc/*.py","gui/Misc/Tk/*.py","TestUtil/*.py",
                   "gui/BasicWidgets/Tk/*.py", "gui/InputForm/Tk/*.py",
                   'gui/BasicWidgets/Tk/TreeWidget/*.py',
                   ]

    # 2- List all the python modules not supported that should not be included
    # in certain releases.
    pynotsupported = ['web/*.py',]

    # 3- Specify the documentation files and directories to be included in the
    # release
    docFiles = []#["doc/"]

    # 4-Specify the extraFiles to be included in the release.
    extraFiles = ["CVS","math/CVS", "gui/CVS", "util/CVS",
                  "web/CVS", "gui/BasicWidgets/CVS","gui/InputForm/CVS",
                  "gui/Misc/CVS","gui/Misc/Tk/CVS","TestUtil/CVS",
                  "gui/BasicWidgets/Tk/CVS", "gui/InputForm/Tk/CVS",
                  'gui/BasicWidgets/Tk/cw.ppm','gui/BasicWidgets/Tk/TreeWidget/CVS',
                  'gui/BasicWidgets/Tk/TreeWidget/icons',
                  'TestUtil/bin/', "RELNOTES",
                  ]

    # 5-Specify the testFiles to be included in the release.
    testFiles = ['Tests/*.py','Tests/CVS',
                 'gui/BasicWidgets/Tk/Tests/',
                 'gui/InputForm/Tk/Tests/',
                 "gui/BasicWidgets/Tk/TreeWidget/Tests"
                 ]


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
        for p in pynotsupported:
            files = files + glob(p)
        pynotsupported = files
        os.chdir(olddir)

    if what == 'supported' and len(pynotsupported):
        # need to remove the non supported python files from all the python
        # files
        # These are the keys used for to make the releases...
        
        supportedFiles = filter(lambda x, l = pynotsupported:
                                    not x in l, allPyModule)
        
        return supportedFiles  + testFiles + extraFiles
    
    elif what == 'all' or ( what == 'supported' and not len(pynotsupported)):
        # Other wise just add the documentation, test and extra files to all
        # the python modules.
        allFiles= allPyModule + docFiles + testFiles + extraFiles
        return allFiles
    elif what=='documentation':
        return docFiles

    else:
        return []
