import numpy
from math import sqrt, pi, sin, cos, asin
from cellpack.autopack.transformation import angle_between_vectors
from cellpack.mgl_tools.RAPID import RAPIDlib


# should use transform.py instead
def getNormedVectorOnes(a):
    n = a / numpy.linalg.norm(a)
    return numpy.round(n)


def getNormedVectorU(a):
    return a / numpy.linalg.norm(a)


def getNormedVector(a, b):
    return (b - a) / numpy.linalg.norm(b - a)


def getDihedral(a, b, c, d):
    v1 = getNormedVector(a, b)
    v2 = getNormedVector(b, c)
    v3 = getNormedVector(c, d)
    v1v2 = numpy.cross(v1, v2)
    v2v3 = numpy.cross(v2, v3)
    return angle_between_vectors(v1v2, v2v3)


def rotax(a, b, tau, transpose=1):
    """
    Build 4x4 matrix of clockwise rotation about axis a-->b
    by angle tau (radians).
    a and b are sequences of 3 floats each
    Result is a homogenous 4x4 transformation matrix.
    NOTE: This has been changed by Brian, 8/30/01: rotax now returns
    the rotation matrix, _not_ the transpose. This is to get
    consistency across rotax, mat_to_quat and the classes in
    transformation.py
    when transpose is 1 (default) a C-style rotation matrix is returned
    i.e. to be used is the following way Mx (opposite of OpenGL style which
    is using the FORTRAN style)
    """

    assert len(a) == 3
    assert len(b) == 3
    if tau <= -2 * pi or tau >= 2 * pi:
        tau = tau % (2 * pi)

    ct = cos(tau)
    ct1 = 1.0 - ct
    st = sin(tau)

    # Compute unit vector v in the direction of a-->b. If a-->b has length
    # zero, assume v = (1,1,1)/sqrt(3).

    v = [b[0] - a[0], b[1] - a[1], b[2] - a[2]]
    s = v[0] * v[0] + v[1] * v[1] + v[2] * v[2]
    if s > 0.0:
        s = sqrt(s)
        v = [v[0] / s, v[1] / s, v[2] / s]
    else:
        val = sqrt(1.0 / 3.0)
        v = (val, val, val)

    rot = numpy.zeros((4, 4), "f")
    # Compute 3x3 rotation matrix

    v2 = [v[0] * v[0], v[1] * v[1], v[2] * v[2]]
    v3 = [(1.0 - v2[0]) * ct, (1.0 - v2[1]) * ct, (1.0 - v2[2]) * ct]
    rot[0][0] = v2[0] + v3[0]
    rot[1][1] = v2[1] + v3[1]
    rot[2][2] = v2[2] + v3[2]
    rot[3][3] = 1.0

    v2 = [v[0] * st, v[1] * st, v[2] * st]
    rot[1][0] = v[0] * v[1] * ct1 - v2[2]
    rot[2][1] = v[1] * v[2] * ct1 - v2[0]
    rot[0][2] = v[2] * v[0] * ct1 - v2[1]
    rot[0][1] = v[0] * v[1] * ct1 + v2[2]
    rot[1][2] = v[1] * v[2] * ct1 + v2[0]
    rot[2][0] = v[2] * v[0] * ct1 + v2[1]

    # add translation
    for i in (0, 1, 2):
        rot[3][i] = a[i]
    for j in (0, 1, 2):
        rot[3][i] = rot[3][i] - rot[j][i] * a[j]
    rot[i][3] = 0.0

    if transpose:
        return rot
    else:
        return numpy.transpose(rot)


def rotVectToVect(vect1, vect2, i=None):
    """returns a 4x4 transformation that will align vect1 with vect2
    vect1 and vect2 can be any vector (non-normalized)"""
    v1x, v1y, v1z = vect1
    v2x, v2y, v2z = vect2

    # normalize input vectors
    norm = 1.0 / sqrt(v1x * v1x + v1y * v1y + v1z * v1z)
    v1x *= norm
    v1y *= norm
    v1z *= norm
    norm = 1.0 / sqrt(v2x * v2x + v2y * v2y + v2z * v2z)
    v2x *= norm
    v2y *= norm
    v2z *= norm

    # compute cross product and rotation axis
    cx = v1y * v2z - v1z * v2y
    cy = v1z * v2x - v1x * v2z
    cz = v1x * v2y - v1y * v2x

    # normalize
    nc = sqrt(cx * cx + cy * cy + cz * cz)
    if nc == 0.0:
        return [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]

    cx /= nc
    cy /= nc
    cz /= nc

    # compute angle of rotation
    if nc < 0.0:
        if i is not None:
            print("truncating nc on step:", i, nc)
        nc = 0.0
    elif nc > 1.0:
        if i is not None:
            print("truncating nc on step:", i, nc)
        nc = 1.0

    alpha = asin(nc)
    if (v1x * v2x + v1y * v2y + v1z * v2z) < 0.0:
        alpha = pi - alpha

    # rotate about nc by alpha
    # Compute 3x3 rotation matrix

    ct = cos(alpha)
    ct1 = 1.0 - ct
    st = sin(alpha)

    rot = [
        [0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0],
    ]

    rv2x, rv2y, rv2z = cx * cx, cy * cy, cz * cz
    rv3x, rv3y, rv3z = (1.0 - rv2x) * ct, (1.0 - rv2y) * ct, (1.0 - rv2z) * ct
    rot[0][0] = rv2x + rv3x
    rot[1][1] = rv2y + rv3y
    rot[2][2] = rv2z + rv3z
    rot[3][3] = 1.0

    rv4x, rv4y, rv4z = cx * st, cy * st, cz * st
    rot[0][1] = cx * cy * ct1 - rv4z
    rot[1][2] = cy * cz * ct1 - rv4x
    rot[2][0] = cz * cx * ct1 - rv4y
    rot[1][0] = cx * cy * ct1 + rv4z
    rot[2][1] = cy * cz * ct1 + rv4x
    rot[0][2] = cz * cx * ct1 + rv4y

    return rot


def ApplyMatrix(coords, mat):
    """
    Apply the 4x4 transformation matrix to the given list of 3d points.

    @type  coords: array
    @param coords: the list of point to transform.
    @type  mat: 4x4array
    @param mat: the matrix to apply to the 3d points

    @rtype:   array
    @return:  the transformed list of 3d points
    """

    # 4x4matrix"
    mat = numpy.array(mat)
    coords = numpy.array(coords)
    one = numpy.ones((coords.shape[0], 1), coords.dtype.char)
    c = numpy.concatenate((coords, one), 1)
    return numpy.dot(c, numpy.transpose(mat))[:, :3]


def bullet_checkCollision_mp(world, node1, node2):
    #    world =
    #    node1 = histoVol.callFunction(self.env.addRB,(self, jtrans, rotMatj,),{"rtype":self.Type},)
    #    node2 = histoVol.callFunction(self.env.addRB,(self, jtrans, rotMatj,),{"rtype":self.Type},)
    return world.contactTestPair(node1, node2).getNumContacts() > 0


def rapid_checkCollision_rmp(liste_input):

    node1 = RAPIDlib.RAPID_model()
    node1.addTriangles(
        numpy.array(liste_input[0][0], "f"), numpy.array(liste_input[0][1], "i")
    )
    node2 = {}
    for inp in liste_input:
        if inp[-1] not in node2:
            node2[inp[-1]] = RAPIDlib.RAPID_model()
            node2[inp[-1]].addTriangles(
                numpy.array(inp[4], "f"), numpy.array(inp[5], "i")
            )
        RAPIDlib.RAPID_Collide_scaled(
            inp[2],
            inp[3],
            1.0,
            node1,
            inp[6],
            inp[7],
            1.0,
            node2[inp[-1]],
            RAPIDlib.cvar.RAPID_FIRST_CONTACT,
        )
        if RAPIDlib.cvar.RAPID_num_contacts != 0:
            return True
    return False


def rapid_checkCollision_mp(v1, f1, rot1, trans1, v2, f2, rot2, trans2):
    node1 = RAPIDlib.RAPID_model()
    node1.addTriangles(numpy.array(v1, "f"), numpy.array(f1, "i"))
    node2 = RAPIDlib.RAPID_model()
    node2.addTriangles(numpy.array(v2, "f"), numpy.array(f2, "i"))
    RAPIDlib.RAPID_Collide_scaled(
        rot1,
        trans1,
        1.0,
        node1,
        rot2,
        trans2,
        1.0,
        node2,
        RAPIDlib.cvar.RAPID_FIRST_CONTACT,
    )
    #    print ("Num box tests: %d" % RAPIDlib.cvar.RAPID_num_box_tests)
    #    print ("Num contact pairs: %d" % RAPIDlib.cvar.RAPID_num_contacts)
    # data3 = RAPIDlib.RAPID_Get_All_Pairs()
    return RAPIDlib.cvar.RAPID_num_contacts != 0
