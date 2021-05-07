v = (
    (0.0, 0.0, 0.0),
    (1.0, 0.0, 0.0),
    (0.0, 1.0, 0.0),
    (1.0, 1.0, 0.0),
    (0.0, 2.0, 0.0),
    (1.0, 2.0, 0.0),
    (0.0, 3.0, 0.0),
    (1.0, 3.0, 0.0),
    (0.0, 4.0, 0.0),
    (1.0, 4.0, 0.0),
    (0.0, 5.0, 0.0),
    (1.0, 5.0, 0.0),
    (0.0, 6.0, 0.0),
    (1.0, 6.0, 0.0),
)

ind = (range(14),)

RED = (1.0, 0.0, 0.0)
GREEN = (0.0, 1.0, 0.0)
BLUE = (0.0, 0.0, 1.0)
col = (
    RED,
    RED,
    RED,
    GREEN,
    GREEN,
    GREEN,
    BLUE,
    BLUE,
    BLUE,
    RED,
    GREEN,
    BLUE,
    RED,
    GREEN,
)

col2 = (
    RED,
    RED,
    RED,
    RED,
    RED,
    RED,
    RED,
    GREEN,
    GREEN,
    GREEN,
    GREEN,
    GREEN,
    GREEN,
    GREEN,
)

from DejaVu.IndexedPolylines import IndexedPolylines

p = IndexedPolylines("testColor", vertices=v, faces=ind, materials=col)

from DejaVu import Viewer

vi = Viewer()
vi.AddObject(p)

p2 = IndexedPolylines("testColor2", vertices=v, faces=ind, materials=col2)
vi.AddObject(p2)

norm = ((1.0, 0.0, 0.0),) * 14
pn = IndexedPolylines(
    "testMaterial", vertices=v, faces=ind, materials=col, vnormals=norm
)
vi.AddObject(pn)

pn2col = IndexedPolylines(
    "testMaterial2", vertices=v, faces=ind, materials=col2, vnormals=norm
)
vi.AddObject(pn2col)

from DejaVu.Spheres import Spheres

s1 = Spheres("test", centers=v, radii=(0.4,), materials=col)
vi.AddObject(s1)

s2 = Spheres("test", centers=v, radii=(0.4,), materials=col2)
vi.AddObject(s2)

# make OPT=-g
# cp openglutil_num.so /mgl/tools/public_python/1.5.2b1/sgi4DIRIX646/lib/python1.5/site-packages/OpenGL/OpenGL/shared/irix646/openglutil_num.so
