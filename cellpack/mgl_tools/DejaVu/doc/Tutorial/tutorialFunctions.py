def readSurface(name):
    """Read the files 'name'.vertices and 'name'.triangles and returns
    lists of 6-floats for vertices x,y,z,nx,ny,nz and a list of 3-ints
    for triangles"""

    import string

    f = open(name + ".vertices")
    vdata = f.readlines()
    f.close()

    vdata = map(string.split, vdata)
    vdata = map(
        lambda x: (
            float(x[0]),
            float(x[1]),
            float(x[2]),
            float(x[3]),
            float(x[4]),
            float(x[5]),
        ),
        vdata,
    )

    f = open(name + ".triangles")
    tdata = f.readlines()
    f.close()

    tdata = map(string.split, tdata)
    tdata = map(lambda x: (int(x[0]), int(x[1]), int(x[2])), tdata)

    return vdata, tdata
