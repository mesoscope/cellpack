import numpy
import panda3d
from panda3d.core import Mat4
from math import sqrt, pi, sin, cos, asin
from cellpack.autopack.transformation import angle_between_vectors


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


# TODO : move somewhere in a more apropriate place ?
def pandaMatrice(mat):
    if panda3d is None:
        return
    mat = mat.transpose().reshape((16,))
    #        print mat,len(mat),mat.shape
    pMat = Mat4(
        mat[0],
        mat[1],
        mat[2],
        mat[3],
        mat[4],
        mat[5],
        mat[6],
        mat[7],
        mat[8],
        mat[9],
        mat[10],
        mat[11],
        mat[12],
        mat[13],
        mat[14],
        mat[15],
    )
    return pMat


def get_reflected_point(self, new_position, boundingBox=None):
    # returns the reflection of a point across a bounding box
    if boundingBox is None:
        boundingBox = self.env.grid.boundingBox

    # distance from origin
    dist_o = new_position - boundingBox[0]
    ref_inds_o = dist_o < 0

    # distance from edge
    dist_e = boundingBox[1] - new_position
    ref_inds_e = dist_e < 0

    while True in ref_inds_o or True in ref_inds_e:
        # reflect around origin
        new_position[ref_inds_o] = boundingBox[1][ref_inds_o] + dist_o[ref_inds_o]
        dist_o = new_position - boundingBox[0]
        ref_inds_o = dist_o < 0

        # reflect around edge
        new_position[ref_inds_e] = boundingBox[0][ref_inds_e] - dist_e[ref_inds_e]
        dist_e = boundingBox[1] - new_position
        ref_inds_e = dist_e < 0

    return new_position
