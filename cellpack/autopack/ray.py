# -*- coding: utf-8 -*-
"""
Created on Saturday September 1 1:50:00 2012
###############################################################################
#
# autoPACK Authors: Graham T. Johnson, Ludovic Autin, Mostafa Al-Alusi, Michel Sanner
#  Based on COFFEE Script developed by Graham Johnson between 2005 and 2010
#  with assistance from Mostafa Al-Alusi in 2009 and periodic input
#  from Arthur Olson's Molecular Graphics Lab
#
# AFGui.py Authors: Ludovic Autin with minor editing/enhancement from Graham Johnson
#
# Copyright: Graham Johnson ©2010
#
# This file "fillBoxPseudoCode.py" is part of autoPACK, cellPACK, and AutoFill.
#
#   autoPACK is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   autoPACK is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with autoPACK (See "CopyingGNUGPL" in the installation.
#   If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
Name: -
@author: Graham Johnson, Michel Sanner, Ludovic Autin, Kevin Wu
"""

import numpy
from math import sqrt


def vdiff(p1, p2):
    # returns p1 - p2
    x1, y1, z1 = p1
    x2, y2, z2 = p2
    return (x1 - x2, y1 - y2, z1 - z2)


def vcross(v1, v2):
    x1, y1, z1 = v1
    x2, y2, z2 = v2
    return (y1 * z2 - y2 * z1, z1 * x2 - z2 * x1, x1 * y2 - x2 * y1)


def dot(v1, v2):
    x1, y1, z1 = v1
    x2, y2, z2 = v2
    return (x1 * x2) + (y1 * y2) + (z1 * z2)


def vnorm(v1):
    x1, y1, z1 = v1
    n = 1.0 / sqrt(x1 * x1 + y1 * y1 + z1 * z1)
    return (x1 * n, y1 * n, z1 * n)


def vlen(v1):
    x1, y1, z1 = v1
    return sqrt(x1 * x1 + y1 * y1 + z1 * z1)


def ray_intersect_polygon(
    pRayStartPos,
    pRayEndPos,
    pQuadranglePointPositions,
    pQuadranglePointList,
    pTruncateToSegment,
):
    # This function returns TRUE if a ray intersects a triangle.
    # It also calculates and returns the UV coordinates of said
    # colision as part of the intersection test,

    # This line segment defines an infinite line to test for intersection
    vLineSlope = vdiff(pRayEndPos - pRayStartPos)
    vTriPolys = pQuadranglePointList
    vBackface = False
    vHitCount = 0

    vTriPoints = pQuadranglePointPositions
    j = 0

    # vQuadrangle = 1  # Default says polygon is a quadrangle.
    vLoopLimit = 2  # Default k will loop through polygon assuming its a quad.

    # FIXME handle quads
    # Test to see if quad is actually just a triangle.
    # if vTriPolys[j+3] == vTriPolys[j+2]:
    #   vQuadrangle = 0  # Current polygon is not a quad, its a triangle.
    #   vLoopLimit = 1  # Set k loop to only cycle one time.

    for k in range(vLoopLimit):
        # Always get the first point of a quad/tri
        vTriPt0 = vTriPoints[vTriPolys[j]]
        # Get point 1 for a tri and a quad's first pass,
        # but skip for a quad's second pass
        vTriPt1 = vTriPoints[vTriPolys[j + 1 + k]]
        # Get point 2 for a tri and a quad's first pass,
        # but get point 3 only for a quad on its second pass.
        vTriPt2 = vTriPoints[vTriPolys[j + 2 + k]]

        # Get the first edge as a vector.
        vE1 = vdiff(vTriPt1 - vTriPt0)  # Get the first edge as a vector.
        vE2 = vdiff(vTriPt2 - vTriPt0)  # Get the second edge.
        h = vcross(vLineSlope, vE2)
        a = dot(vE1, h)  # Get the projection of h onto vE1.

        # If the ray is parallel to the plane then it does not intersect it,
        # i.e, a = 0 +/- given rounding slop.
        if a > -0.00001 and a < 0.00001:
            # If the polygon is a quadrangle, test the other triangle
            # that comprises it.
            continue

        F = 1.0 / a

        # Get the vector from the origin of the triangle to the ray's origin.
        s = pRayStartPos - vTriPt0
        d = dot(s, h)
        u = (F * d[0], F * d[1], F * d[2])

        # Break if its outside of the triangle, but try the other triangle if
        # in a quad. U is described as u = : start of vE1 = 0.0,  to the end
        # of vE1 = 1.0 as a percentage.
        # If the value of the U coordinate is outside the range of values
        # inside the triangle, then the ray has intersected the plane outside
        # the triangle.
        if u < 0.0 or u > 1.0:
            continue

        q = vcross(s, vE1)
        d = dot(vLineSlope, q)
        v = (F * d[0], F * d[1], F * d[2])

        # Break if outside of the triangles v range.
        # If the value of the V coordinate is outside the range of values
        # inside the triangle, then the ray has intersected the plane outside
        # the triangle.
        # U + V cannot exceed 1.0 or the point is not in the triangle.
        # If you imagine the triangle as half a square this makes sense.
        # U=1 V=1 would be  in the
        # lower left hand corner which would be in the second triangle making
        # up the square.
        if v < 0.0 or u + v > 1.0:
            continue

        # This is the global collision position.
        vCollidePos = (
            vTriPt0[0] + u * vE1[0] + v * vE2[0],
            vTriPt0[1] + u * vE1[1] + v * vE2[1],
            vTriPt0[2] + u * vE1[2] + v * vE2[2],
        )

        # The ray is hitting a triangle, now test to see if its a triangle
        # hit by the ray.
        vBackface = False
        if dot(vLineSlope, vdiff(vCollidePos - pRayStartPos)) > 0:
            # This truncates our infinite line to a ray pointing from
            # start THROUGH end positions.
            vHitCount += 1
            if pTruncateToSegment and vlen(vLineSlope) < vlen(
                vdiff(vCollidePos - pRayStartPos)
            ):
                # This truncates our ray to a line segment from start to
                # end positions.
                break

            if a < 0.00001:  # Test to see if the triangle hit is a backface.
                vBackface = True

    return vBackface


def ray_intersect_polyhedron(
    pRayStartPos, pRayEndPos, vertices, faces, pTruncateToSegment
):
    # This function returns TRUE if a ray intersects a triangle.
    # It also calculates and returns the UV coordinates of said
    # collision as part of the intersection test,

    # This line segment defines an infinite line to test for intersection
    vLineSlope = vdiff(pRayEndPos, pRayStartPos)
    # vPolyhedronPos = GetGlobalPosition(pPolyhedron)
    vTriPoints = vertices
    # vTriPolys = faces
    vHitCount = 0

    # FIXME
    # for v in range(vTriPoints) i++):  # Lets globalize the polyhedron.
    #   vTriPoints[i] = vTriPoints[i] + vPolyhedronPos

    print("------------------------")
    print("ray", pRayStartPos, pRayEndPos)
    # Walk through each polygon in a polyhedron
    for fn, f in enumerate(faces):
        if len(f) == 3:
            # vQuadrangle = 0  # polygon is a triangle
            vLoopLimit = 1
        else:
            # vQuadrangle = 1  # Default says polygon is a quadrangle.
            vLoopLimit = 2

        for k in range(vLoopLimit):
            # Always get the first point of a quad/tri
            vTriPt0 = vTriPoints[f[0]]
            # Get point 1 for a tri and a quad's first pass,
            # but skip for a quad's second pass
            vTriPt1 = vTriPoints[f[1 + k]]
            # Get point 2 for a tri and a quad's first pass,
            # but get point 3 only for a quad on its second pass.
            vTriPt2 = vTriPoints[f[2 + k]]

            vE2 = vdiff(vTriPt2, vTriPt0)  # Get the second edge.
            h = vcross(vLineSlope, vE2)

            vE1 = vdiff(vTriPt1, vTriPt0)  # Get the first edge
            a = dot(vE1, h)  # Get the projection of h onto vE1.

            # If the ray is parallel to the plane then it does not
            # intersect it, i.e, a = 0 +/- given rounding slope.
            if a > -0.00001 and a < 0.00001:
                continue

            # If the polygon is a quadrangle, test the other triangle
            # that comprises it.

            F = 1.0 / a

            # Get the vector from the origin of the triangle to the
            # ray's origin.
            s = vdiff(pRayStartPos, vTriPt0)
            u = F * dot(s, h)

            # Break if its outside of the triangle, but try the other
            # triangle if in a quad.
            # U is described as u = : start of vE1 = 0.0,  to the end
            # of vE1 = 1.0 as a percentage.
            # If the value of the U coordinate is outside the range of
            # values inside the triangle,
            # then the ray has intersected the plane outside the triangle.
            if u < 0.0 or u > 1.0:
                continue

            q = vcross(s, vE1)
            v = F * dot(vLineSlope, q)

            # Break if outside of the triangles v range.
            # If the value of the V coordinate is outside the range of
            # values inside the triangle, then the ray has intersected
            # the plane outside the triangle.
            # U + V cannot exceed 1.0 or the point is not in the triangle.
            # If you imagine the triangle as half a square this makes
            # sense.  U=1 V=1 would be  in the lower left hand corner
            # which would be in the second triangle making up the square.*/
            if v < 0.0 or u + v > 1.0:
                continue

            # This is the global collision position.
            vCollidePos = (
                vTriPt0[0] + u * vE1[0] + v * vE2[0],
                vTriPt0[1] + u * vE1[1] + v * vE2[1],
                vTriPt0[2] + u * vE1[2] + v * vE2[2],
            )

            print("COllision", fn, vCollidePos)
            # The ray is hitting a triangle, now test to see if its a
            # triangle hit by the ray.
            # vBackface = False # TODO: figure out if this was supposed to be returned

            # This truncates our infinite line to a ray pointing from
            # start THROUGH end positions.
            if dot(vLineSlope, vdiff(vCollidePos, pRayStartPos)) > 0:
                vHitCount += 1
                if pTruncateToSegment and vlen(vLineSlope) < vlen(
                    vdiff(vCollidePos, pRayStartPos)
                ):
                    break
                # This truncates our ray to a line segment from
                # start to end positions.

                # Test to see if the triangle hit is a backface.
                if a < 0.00001:
                    # set master grid to organelle->getname inside
                    # vBackface = True  # TODO: figure out if this was supposed to be returned

                    # This stuff is specific to our Point inside goals.
                    # To see if a point is inside, I can stop at the
                    # first backface hit.
                    break

        return vHitCount


def f_ray_intersect_polyhedron(
    pRayStartPos, pRayEndPos, faces, vertices, pTruncateToSegment
):
    """This function returns TRUE if a ray intersects a triangle.
    It also calculates and returns the UV coordinates of said colision as part of the intersection test,
    Makes sure that we are working with arrays

    * TAKES IN pRayStartPos as LEFT-HANDED COORDINATE (Z,Y,X)
    * TAKES IN pRayEndPos AS LEFT-HANDED COORDINATE (Z,Y,X)
    * faces is a list of vertex indices that defines the polyhedron
    * vertices is the list of global coordinates that faces refers to
    * pTruncateToSegment decides whether or not the segment terminates at the end position, or keeps on
      going forever
    """
    pRayStartPos = numpy.array(pRayStartPos)
    pRayEndPos = numpy.array(pRayEndPos)

    vLineSlope = (
        pRayEndPos - pRayStartPos
    )  # This line segment defines an infinite line to test for intersection
    # vPolyhedronPos = numpy.array((0, 0, 0))
    vTriPoints = vertices
    vTriPolys = faces
    vBackface = None
    vBackfaceFinal = None
    maxDistance = 99999
    vHitCount = 0

    vEpsilon = 0.00001
    # vBreakj = False  # TODO: figure out if this was supposed to be used
    vCollidePos = None

    # Walk through each polygon in a polyhedron
    for testingFace in vTriPolys:
        # Loop through all the polygons in an input polyhedron
        # vQuadrangle = 1  # Default says polygon is a quadrangle.
        # vLoopLimit = 2  # Default k will loop through polygon assuming its a quad.
        # if (vTriPolys[j+3] == vTriPolys[j+2])  # Test to see if quad is actually just a triangle.
        #  {
        # vQuadrangle = 0  # Current polygon is not a quad, it's a triangle.
        vLoopLimit = 1  # Set k loop to only cycle one time.

        for k in range(vLoopLimit):
            vTriPt0 = numpy.array(
                vTriPoints[testingFace[0]]
            )  # Always get the first point of a quad/tri
            vTriPt1 = numpy.array(
                vTriPoints[testingFace[1]]
            )  # Get point 1 for a tri and a quad's first pass, but skip for a quad's second pass
            vTriPt2 = numpy.array(
                vTriPoints[testingFace[2]]
            )  # Get point 2 for a tri and a quad's first pass, but get point 3 only for a quad on its second pass.

            vE1 = vTriPt1 - vTriPt0  # et the first edge as a vector.
            vE2 = vTriPt2 - vTriPt0  # Get the second edge.
            h = vcross(vLineSlope, vE2)

            a = f_dot_product(vE1, h)  # Get the projection of h onto vE1.
            if a > -vEpsilon and a < vEpsilon:
                continue  # If the ray is parallel to the plane then it does not intersect it, i.e, a = 0 +/- given rounding slope.
                # If the polygon is a quadrangle, test the other triangle that comprises it.

            F = 1.0 / a
            s = (
                pRayStartPos - vTriPt0
            )  # Get the vector from the origin of the triangle to the ray's origin.
            u = F * f_dot_product(s, h)
            if u < 0.0 or u > 1.0:
                continue
                # /* Break if its outside of the triangle, but try the other triangle if in a quad.
                # U is described as u = : start of vE1 = 0.0,  to the end of vE1 = 1.0 as a percentage.
                # If the value of the U coordinate is outside the range of values inside the triangle,
                # then the ray has intersected the plane outside the triangle.*/

            q = vcross(s, vE1)
            v = F * f_dot_product(vLineSlope, q)
            if v < 0.0 or u + v > 1.0:
                continue
                # /*  Break if outside of the triangles v range.
                # If the value of the V coordinate is outside the range of values inside the triangle,
                # then the ray has intersected the plane outside the triangle.
                # U + V cannot exceed 1.0 or the point is not in the triangle.
                # If you imagine the triangle as half a square this makes sense.  U=1 V=1 would be  in the
                # lower left hand corner which would be in the second triangle making up the square.*/

            vCollidePos = (
                vTriPt0 + u * vE1 + v * vE2
            )  # This is the global collision position.
            assert len(vCollidePos) == 3

            # The ray is hitting a triangle, now test to see if its a triangle hit by the ray.
            vBackface = False
            if (
                f_dot_product(vLineSlope, vCollidePos - pRayStartPos) > 0
            ):  # This truncates our infinite line to a ray pointing from start THROUGH end positions.
                vHitCount += 1
                if pTruncateToSegment and vlen(vLineSlope) < vlen(
                    vCollidePos - pRayStartPos
                ):
                    print("broken")
                    break  # This truncates our ray to a line segment from start to end positions.

                d = vlen(pRayStartPos - vCollidePos)
                if d >= maxDistance:
                    continue
                if a < vEpsilon:  # Test to see if the triangle hit is a backface.
                    # set master grid to organelle->getname inside
                    vBackface = True
                    # This stuff is specific to our Point inside goals.
                    # vBreakj = True  # To see if a point is inside, I can stop at the first backface hit.
                    # break
                # else:
                # vBreakj = True

                vBackfaceFinal = vBackface
                maxDistance = d
    # vBackfaceFinal = vBackfaces[distances.index(min(distances))]
    return vHitCount, vBackfaceFinal


# makeGrid removed because redundant implementation.


def makeMarchingCube(gridSpacing, r):
    """
    Create a numpy array that represents the precomputed distances to each point
    for the cube of points surrounding our center point.
    """

    def _pythagorean(*edgeLengths):
        from math import sqrt

        total = 0
        for length in edgeLengths:
            total += length * length
        distance = sqrt(total)
        return distance

    from math import ceil

    pointsForRadius = int(
        ceil(r / gridSpacing)
    )  # Number of grid points required to represent our radius, rounded up
    pointsInEdge = 2 * pointsForRadius + 1  # Number of points in one edge of our cube
    center = pointsForRadius  # The index if our center point
    cube = numpy.zeros(shape=(pointsInEdge, pointsInEdge, pointsInEdge))
    distX = numpy.zeros(shape=(pointsInEdge, pointsInEdge, pointsInEdge))
    distY = numpy.zeros(shape=(pointsInEdge, pointsInEdge, pointsInEdge))
    distZ = numpy.zeros(shape=(pointsInEdge, pointsInEdge, pointsInEdge))
    for a in range(pointsInEdge):
        lenX = a - center
        for b in range(pointsInEdge):
            lenY = b - center
            for c in range(pointsInEdge):
                lenZ = c - center
                cube[a][b][c] = _pythagorean(lenX, lenY, lenZ) * gridSpacing
                distX[a][b][c] = lenX
                distY[a][b][c] = lenY
                distZ[a][b][c] = lenZ
    return cube, distX, distY, distZ


# getPointFrom3D needs to be imported from Grid.py
# Syntax: getPointFrom3D(self, pt3d)
# from Grid import getPointFrom3D


def findPointsCenter(*args):
    # Average down the column, such that we're averaging across all measurements in one dimension
    center = numpy.mean(args[0], axis=0)
    return center


# vcross, vlen removed because already imported.


def f_dot_product(vector1, vector2):
    """Return the dot product of two 3D vectors."""
    dottedVectors = [vector1[i] * vector2[i] for i in range(len(vector1))]
    return sum(dottedVectors)
