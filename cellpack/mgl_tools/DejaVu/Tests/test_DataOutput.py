## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by

import string, sys
import numpy.oldnumeric as Numeric
from mglutil.regression import testplus
from DejaVu.DataOutput import OutputVRML2
from time import sleep
from DejaVu.IndexedPolygons import IndexedPolygons
from DejaVu.Viewer import Viewer
from DejaVu.Texture import Texture
from DejaVu.colorTool import RGBRamp


def pause(sleepTime=0.4):
    sleep(sleepTime)


# def setUp():
#    pass


def mapToTexture(ramp):
    return Numeric.array(Numeric.array(ramp) * 255).astype("B")


def buildVertToTexCoords(verts, texCoords):
    d = {}
    i = 0
    for v in verts:
        d[str(v[0]) + str(v[1]) + str(v[2])] = texCoords[i]
        i = i + 1
    return d


def getTexCoords(vertices, lookup):
    tx = map(lambda v, l=lookup: l[str(v[0]) + str(v[1]) + str(v[2])], vertices)
    tx = Numeric.array(tx)
    tx.shape = (-1, 1)
    return tx


def test_getVRML2():

    # first, lets test if we can create a vrml2 file
    vi = Viewer(verbose=False)
    points = [
        [-1, 1, 1],
        [-1, -1, 1],
        [1, 1, 1],
        [1, -1, 1],
        [1, 1, -1],
        [1, -1, -1],
        [-1, 1, -1],
        [-1, -1, -1],
    ]
    indices = [
        [0, 1, 3, 2],
        [4, 5, 7, 6],
        [6, 7, 1, 0],
        [2, 3, 5, 4],
        [6, 0, 2, 4],
        [1, 7, 5, 3],
    ]
    geomBox = IndexedPolygons("box", vertices=points, faces=indices, visible=1)
    vi.AddObject(geomBox)
    V = OutputVRML2()
    vrml2 = V.getVRML2(vi.rootObject)
    assert len(vrml2)

    # now test the file
    Group = None
    children = None
    Transform = None
    Shape = None
    geometry = None
    IndexedFaceSet = None
    coord = None
    Coordinate = None
    point = None
    coordIndex = None

    # check that we have the following keywords
    for line in vrml2:
        for item in string.split(line):
            if item == "Group":
                Group = 1
            elif item == "children":
                children = 1
            elif item == "Transform":
                Transform = 1
            elif item == "Shape":
                Shape = 1
            elif item == "geometry":
                geometry = 1
            elif item == "IndexedFaceSet":
                IndexedFaceSet = 1
            elif item == "coord":
                coord = 1
            elif item == "Coordinate":
                Coordinate = 1
            elif item == "point":
                point = 1
            elif item == "coordIndex":
                coordIndex = 1

    assert Group == 1
    assert children == 1
    assert Transform == 1
    assert Shape == 1
    assert geometry == 1
    assert IndexedFaceSet == 1
    assert coord == 1
    assert Coordinate == 1
    assert point == 1
    assert coordIndex == 1
    vi.Exit()


def test_getVRML2withTexture():

    vi = Viewer(verbose=False)
    points = [
        [-1, 1, 1],
        [-1, -1, 1],
        [1, 1, 1],
        [1, -1, 1],
        [1, 1, -1],
        [1, -1, -1],
        [-1, 1, -1],
        [-1, -1, -1],
    ]
    indices = [
        [0, 1, 3, 2],
        [4, 5, 7, 6],
        [6, 7, 1, 0],
        [2, 3, 5, 4],
        [6, 0, 2, 4],
        [1, 7, 5, 3],
    ]
    geomBox = IndexedPolygons("box", vertices=points, faces=indices, visible=1)

    # add texture to geom
    prop = Numeric.array(range(0, 255, 36)).astype("f")
    ramp = RGBRamp()

    tex = mapToTexture(ramp)
    t = Texture()
    t.Set(enable=1, image=tex)
    geomBox.Set(texture=t)

    lookup = buildVertToTexCoords(geomBox.vertexSet.vertices.array, prop)
    tx = getTexCoords(geomBox.vertexSet.vertices.array, lookup)
    geomBox.Set(textureCoords=tx)

    # create viewer, add object to viewer and get vrml2
    vi.AddObject(geomBox)
    V = OutputVRML2()
    vrml2 = V.getVRML2(vi.rootObject)

    # check that we have the following keywords
    texture = None
    PixelTexture = None
    image = None
    texCoord = None
    TextureCoordinate = None

    for line in vrml2:
        for item in string.split(line):
            if item == "texture":
                texture = 1
            elif item == "PixelTexture":
                PixelTexture = 1
            elif item == "image":
                image = 1
            elif item == "texCoord":
                texCoord = 1
            elif item == "TextureCoordinate":
                TextureCoordinate = 1
    assert texture == 1
    assert PixelTexture == 1
    assert image == 1
    assert texCoord == 1
    assert TextureCoordinate == 1
    vi.Exit()


harness = testplus.TestHarness(
    __name__,
    # connect = setUp,
    funs=testplus.testcollect(globals()),
)

if __name__ == "__main__":
    testplus.chdir()
    print harness
    sys.exit(len(harness))
