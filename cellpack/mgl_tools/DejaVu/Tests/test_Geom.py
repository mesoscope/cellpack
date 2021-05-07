## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by

#
#
# $Id: test_Geom.py,v 1.29 2009/09/02 21:15:07 vareille Exp $
#
#
import unittest
import sys, os, math, Tkinter
import numpy
from opengltk.OpenGL import GL
from geomutils.geomalgorithms import TriangleNormals
import numpy.oldnumeric as Numeric, types
from DejaVu.Geom import Geom
from DejaVu.IndexedGeom import IndexedGeom

# import Materials, viewerConst, datamodel, Clip
from DejaVu.colorTool import OneColor
from DejaVu.Transformable import Transformable
from DejaVu.Displayable import Displayable
from DejaVu.viewerFns import checkKeywords
from DejaVu.Camera import Camera
from DejaVu.Viewer import Viewer
from DejaVu import viewerConst
from DejaVu.ViewerGUI import ViewerGUI


class Geom__init__Tests(unittest.TestCase):
    """test keywords for __init__:
    keywords = ['protected', # 0/1 when set geometry cannot be deleted
                'listed',    # 0/1 when set geometry appears in object list
                'vertices',
                'shape']
    all other keywords are handled by Set method"""

    def test_geom_not_protected(self):
        """default for protected False, (default listed is True)"""
        g = Geom()
        self.assertEqual(isinstance(g, Geom), True)

    def test_geom_protected(self):
        """protected True, (default listed is True)"""
        g = Geom(protected=True)
        self.assertEqual(isinstance(g, Geom), True)

    def test_geom_not_listed(self):
        """listed False, (default protected is False)"""
        g = Geom(listed=False)
        self.assertEqual(isinstance(g, Geom), True)

    def test_geom_listed(self):
        """listed False, protected is True"""
        g = Geom(listed=False, protected=True)
        self.assertEqual(isinstance(g, Geom), True)

    def test_geom_vertices(self):
        """vertices"""
        g = Geom(vertices=((0, 0, 0),))
        self.assertEqual(isinstance(g, Geom), True)

    def test_geom_shape(self):
        """shape"""
        g = Geom(shape=(0, 0))
        self.assertEqual(isinstance(g, Geom), True)

    def test_geom_vertices_shape(self):
        """vertices and shape"""
        g = Geom(
            vertices=(
                (0, 0, 0),
                (0, 0, 1),
            ),
            shape=((0, 0),),
        )
        self.assertEqual(isinstance(g, Geom), True)


class Geom_Set_Tests(unittest.TestCase):
    """
    keywords = ['protected', # 0/1 when set geometry cannot be deleted
                'listed',    # 0/1 when set geometry appears in object list
                'tagModified', # use False to avoid toggling _modified
                'vertices',
                'vreshape',
                'shape',
                'texture',            #not done
                'textureCoords',      #not done
                'vnormals',
                'materials',
                'polyFace',
                'matBind',
                'propName',
                'matName',
                'matInd',
                'rawMaterialB',
                'rawMaterialF',
                'matMask',
                'transient',
                'name',
                #'antialiased',
                'lineWidth',
                'pointWidth',
                'lighting',
                'visible',
                'outline',
                'stippleLines',
                'stipplePolygons',
                'culling',
                'pickable',
                'pickableVertices',
                'scissor',
                'scissorX',
                'scissorY',
                'scissorW',
                'scissorH',
                'scissorAspectRatio',
                'opacity',
                'depthMask',
                'blendFunctions',
                'instanceMatrices',
                'inheritMaterial',
                'inheritXform',
                'inheritPointWidth',
                'inheritLineWidth',
                'inheritStippleLines',
                'inheritStipplePolygons',
                'inheritFrontPolyMode',
                'inheritBackPolyMode',
                'inheritShading',
                'inheritCulling',
                'transparent', # is also set when materials are defines
                'immediateRendering', # set to 1 to avoid using dpyList
                'frontPolyMode',
                'backPolyMode',
                'shading',
                'rotation',
                'translation',
                'scale',
                'pivot',
                ]

    """

    def setUp(self):
        self.geom = Geom(name="baseTest")

    def tearDown(self):
        """
        clean-up
        """
        try:
            del self.geom
        except:
            pass

    # protected
    def test_geom_protected_valid(self):
        """valid input for protected"""
        val = False
        self.geom.Set(protected=val)
        self.assertEqual(val, self.geom.getState()["protected"])

    def test_geom_protected_invalid(self):
        """invalid input for protected"""
        self.geom.Set(protected="hai")
        self.assertNotEqual(self.geom.protected, "hai")

    # listed
    #    def test_geom_cannot_set_listed(self):
    #        """NB:CANNOT Set listed even with valid input 'False'
    #        """
    #        self.geom.Set(listed=False)
    #        newstate=self.geom.getState()['listed']
    #        self.assertEqual(newstate, True)

    def test_geom_listed_invalid(self):
        """invalid input for listed"""
        rval = self.geom.Set(listed="hai")
        self.assertNotEqual(self.geom.listed, "hai")

    # tagModified

    def test_geom_tagModified_valid(self):
        """valid input for tagModified"""
        val = True
        self.geom.Set(tagModified=val)
        self.assertEqual(val, self.geom._modified)

    def test_geom_tagModified_invalid(self):
        """invalid input for tagModified"""
        self.assertRaises(AssertionError, self.geom.Set, tagModified="hai")

    # vertices
    def test_geom_vertices(self):
        """valid input for vertices"""
        val = (
            (0, 0, 0),
            (1, 0, 0),
        )
        self.geom.Set(vertices=val)
        flat = Numeric.array([0.0, 0.0, 0.0, 1.0, 0.0, 0.0])
        self.assertEqual(
            True, numpy.alltrue(flat == self.geom.vertexSet.vertices.array.ravel())
        )

    def test_geom_vertices_invalid(self):
        """invalid input for vertices"""
        self.assertRaises(ValueError, self.geom.Set, vertices="hai")

    ##vreshape
    #    def test_geom_vreshape(self):
    #        """valid input for vreshape
    #        """
    #        val = ((0,0,0,1,0,0),)
    #        reshape=True
    #        self.geom.Set(vertices=val, reshape=reshape)
    #        flat = Numeric.array([0.,0.,0.,1.,0.,0.])
    #        self.assertEqual(flat, self.geom.vertexSet.vertices.array.ravel())
    #

    #    def test_geom_vreshape_invalid(self):
    #        """CANNOT FIND invalid input for vreshape
    #        """
    #        self.geom.Set(vertices=((0,0,0),(1,0,0),), vreshape='False')
    #        flat = Numeric.array([0.,0.,0.,1.,0.,0.])
    #        #print self.geom.vertexSet.vertices
    #        self.assertEqual(flat, self.geom.vertexSet.vertices.array.ravel())

    # shape
    def test_geom_shape(self):
        """valid input for shape"""
        val = ((0, 0, 0, 1, 0, 0),)
        shape = (3, 2)
        self.geom.Set(vertices=val, shape=shape)
        flat = Numeric.array([0.0, 0.0, 0.0, 1.0, 0.0, 0.0])
        # self.assertEqual(flat, self.geom.vertexSet.vertices.array.ravel())
        self.assertEqual(
            True, numpy.alltrue(flat == self.geom.vertexSet.vertices.array.ravel())
        )

    #    def test_geom_shape_invalid(self):
    #        """CANNOT FIND invalid input for shape
    #        """
    #        verts =((0,0,0),(1,0,0))
    #        self.geom.Set(vertices=verts, shape=5)
    #        flat = Numeric.array([0.,0.,0.,1.,0.,0.])
    #        self.assertRaises(AttributeError, self.geom.Set,shape=5)

    # texture
    # textureCoords
    # vnormals
    # materials
    def test_geom_materials(self):
        """valid input for materials"""
        val = ((1, 0, 0),)
        self.geom.Set(materials=val)
        self.assertEqual(val, self.geom.materiasl)

    def test_geom_materials(self):
        """invalid input for materials"""
        self.assertRaises(ValueError, self.geom.Set, materials="hai")

    # polyFace
    # matBind
    # propName
    # matName
    # matInd
    # rawMaterial
    # matMask
    # transient

    # name
    def test_geom_name(self):
        """valid input for name"""
        self.geom.Set(name="test")
        newstate = self.geom.getState()["name"]
        self.assertEqual(newstate, "test")

    def xtest_geom_name_invalid(self):
        """invalid input for name
        ###### it seems that we have always been accepting this invalid data ####
        """
        self.geom.Set(name=" ")
        self.assertNotEqual(self.geom.name, " ")

    ##antialiased
    #    def test_geom_antialiased(self):
    #        """valid input for antialiased
    #        """
    #        self.geom.Set(antialiased=True)
    #        newstate=self.geom.getState()['antialiased']
    #        self.assertEqual(newstate,True)
    #
    #
    #    def test_geom_antialiased_invalid(self):
    #        """invalid input for antialiased
    #        """
    #        self.assertRaises(ValueError, self.geom.Set,antialiased='hai')

    # lineWidth
    def test_linewidth_invalid_input(self):
        """invalid input for lineWidth ,"""
        self.assertRaises(AssertionError, self.geom.Set, lineWidth=-10)

    def test_linewidth(self):
        """valid input for lineWidth"""
        self.geom.Set(lineWidth=1)
        newstate = self.geom.getState()["lineWidth"]
        self.assertEqual(newstate, 1)

    def test_linewidth_bad_input(self):
        """badinput for lineWidth ,"""
        self.assertRaises(AssertionError, self.geom.Set, lineWidth="hai")

    # pointWidth
    def test_pointwidth(self):
        """valid input for pointWidth"""
        self.geom.Set(pointWidth=16)
        newstate = self.geom.getState()["pointWidth"]
        self.assertEqual(newstate, 16)

    def test_pointwidth_invalid(self):
        """invalid input for pointWidth"""
        self.assertRaises(AssertionError, self.geom.Set, pointWidth=-1.0)

    def test_pointwidth_bad_input(self):
        """bad input for pointWidth"""
        self.assertRaises(AssertionError, self.geom.Set, pointWidth="hai")

    def test_pointwidth(self):
        """valid input for pointWidth"""
        self.geom.Set(pointWidth=16)
        self.geom.Set(outline=False, backPolyMode=GL.GL_POINT)
        newstate = self.geom.getState()["pointWidth"]
        self.assertEqual(newstate, 16)

    # lighting
    def test_lighting(self):
        """valid input for lighting"""
        self.geom.Set(lighting=True)
        newstate = self.geom.getState()["lighting"]
        self.assertEqual(newstate, True)

    def test_geom_lighting_invalid(self):
        """invalid input for lighting"""
        self.assertRaises(ValueError, self.geom.Set, lighting="hai")

    def test_geom_visible_invalid(self):
        """invalid input for lighting"""
        self.assertRaises(ValueError, self.geom.Set, lighting="hai")

    # visible
    def test_geom_visible(self):
        """valid input for visible"""
        self.geom.Set(visible=False)
        newstate = self.geom.getState()["visible"]
        self.assertEqual(newstate, False)
        # alternatively
        self.assertEqual(self.geom.visible, False)

    def test_geom_visible_invalid(self):
        """invalid input for visible"""
        self.assertRaises(ValueError, self.geom.Set, visible=[2, 3, 4])

    # outline
    def test_outline(self):
        """valid input for outline"""
        self.geom.Set(outline=True)
        newstate = self.geom.getState()["outline"]
        self.assertEqual(newstate, (True, True))

    def test_geom_outline_invalid(self):
        """invalid input for outline"""
        self.assertRaises(ValueError, self.geom.Set, outline="hai")

    # stippleLines
    def test_geom_stippleLines(self):
        """valid input for stippleLines"""
        self.geom.Set(stippleLines=True)
        newstate = self.geom.getState()["stippleLines"]
        self.assertEqual(newstate, True)

    def test_geom_stippleLines_invalid(self):
        """invalid input for stippleLines"""
        self.assertRaises(ValueError, self.geom.Set, stippleLines="hai")

    # stipplePolygons
    def test_geom_stipplePolygons(self):
        """valid input for stipplePolygons"""
        self.geom.Set(stipplePolygons=True)
        newstate = self.geom.getState()["stipplePolygons"]
        self.assertEqual(newstate, True)

    def test_geom_stipplePolygons_invalid(self):
        """invalid input for stipplePolygons"""
        self.assertRaises(ValueError, self.geom.Set, stipplePolygons="hai")

    # cull
    def test_geom_culling_none(self):
        """valid input for culling,none"""
        self.geom.Set(culling=GL.GL_NONE)
        newstate = self.geom.getState()["culling"]
        self.assertEqual(newstate, "none")

    def test_geom_culling_front(self):
        """valid input for culling,front"""
        self.geom.Set(culling=GL.GL_FRONT)
        newstate = self.geom.getState()["culling"]
        self.assertEqual(newstate, "front")

    def test_geom_culling_back(self):
        """valid input for culling,back"""
        self.geom.Set(culling=GL.GL_BACK)
        newstate = self.geom.getState()["culling"]
        self.assertEqual(newstate, "back")

    def test_geom_culling_front_back(self):
        """valid input for culling,front_back"""
        self.geom.Set(culling=GL.GL_FRONT_AND_BACK)
        newstate = self.geom.getState()["culling"]
        self.assertEqual(newstate, "front_and_back")

    def test_geom_culling_invalid(self):
        """invalid input for culling"""
        self.geom.culling = viewerConst.INHERIT
        self.assertRaises(AssertionError, self.geom.Set, culling="hai")

    # pickable
    def test_geom_pickable(self):
        """valid input for pickable"""
        self.geom.Set(pickable=0)
        newstate = self.geom.getState()["pickable"]
        self.assertEqual(newstate, 0)

    def test_geom_pickable_invalid(self):
        """invalid input for pickable"""
        self.assertRaises(ValueError, self.geom.Set, pickable="hai")

    # pickableVertices
    def test_geom_pickableVertices(self):
        """valid input for pickableVertices"""
        self.geom.Set(pickableVertices=True)
        newstate = self.geom.getState()["pickableVertices"]
        self.assertEqual(newstate, True)

    def test_geom_pickableVertices_invalid(self):
        """invalid input for pickableVertices"""
        self.assertRaises(ValueError, self.geom.Set, pickableVertices="hai")

    # scissor
    def test_geom_scissor_invalid(self):
        """invalid input for scissor on/off not working,a box is displayed"""
        self.assertRaises(ValueError, self.geom.Set, scissor="hai")

    # scissorX
    def test_geom_scissorX(self):
        """valid input for scissorX"""
        self.geom.Set(scissorX=1)
        newstate = self.geom.getState()["scissorX"]
        self.assertEqual(newstate, 1)

    def test_geom_scissorX_invalid(self):
        """invalid input for scissorX"""
        self.assertRaises(ValueError, self.geom.Set, scissorX="hai")

    # scissorY
    def test_geom_scissorY(self):
        """valid input for scissorY"""
        self.geom.Set(scissorY=1)
        newstate = self.geom.getState()["scissorY"]
        self.assertEqual(newstate, 1)

    def test_geom_scissorY_invalid(self):
        """valid input for scissorY"""
        self.assertRaises(ValueError, self.geom.Set, scissorY="hai")

    # scissorW
    def test_geom_scissorW(self):
        """valid input for scissorW"""
        self.geom.Set(scissorW=300)
        newstate = self.geom.getState()["scissorW"]
        self.assertEqual(newstate, 300)

    def test_geom_scissorW_invalid(self):
        """invalid input for scissorW"""
        self.assertRaises(ValueError, self.geom.Set, scissorW="hai")

    # scissorH
    def test_geom_scissorH(self):
        """valid input for scissorH"""
        self.geom.Set(scissorH=300)
        newstate = self.geom.getState()["scissorH"]
        self.assertEqual(newstate, 300)

    def test_geom_scissorH_invalid(self):
        """invalid input for scissorH"""
        self.assertRaises(ValueError, self.geom.Set, scissorH="hai")

    # scissorAspectRatio
    def test_geom_scissorAspectRatio(self):
        """valid input for scissorAspectRatio"""
        self.geom.Set(scissorAspectRatio=2.0)
        newstate = self.geom.getState()["scissorAspectRatio"]
        self.assertEqual(newstate, 2.0)

    def test_geom_scissorAspectRatio_invalid(self):
        """invalid input for scissorAspectRatio"""
        self.assertRaises(ValueError, self.geom.Set, scissorAspectRatio="hai")

    # opacity
    #    def test_geom_opacity(self):
    #        """valid input for scissorAspectRatio
    #        NOT AVAILABLE in STATE
    #        """
    #        self.geom.Set(opacity = [.5, .5])
    #        ###THIS IS BURIED SOMEWHERE IN geom.materials[pf]
    #        ###where pf is something like GL.GL_FRONT
    #        print "\nopacity test not completed..."
    #        ###self.assertEqual(self.geom.opacity,2.0)
    #

    #    def test_geom_opacity_invalid(self):
    #        """invalid input for opacity DOES NOT RAISE ERROR
    #        """
    #        val = [.5,.5]
    #        self.geom.Set(opacity=val)
    #        print "\ninvalid opacity test not completed..."
    #        ##self.assertEqual(self.geom.opacity, val)
    #        #self.assertRaises(ValueError, self.geom.Set, opacity=[2,3,4])

    # depthMask
    def test_geom_depthmask(self):
        """valid input for depthmask"""
        self.geom.Set(depthMask=1)
        newstate = self.geom.getState()["depthMask"]
        self.assertEqual(newstate, 1)

    def test_geom_depthmask_invalid(self):
        """invalid input for depthmask"""
        self.assertRaises(ValueError, self.geom.Set, depthMask="hai")

    # blendFunctions
    def test_geom_blend_func_zero(self):
        """valid input for blend func zero"""
        val1 = GL.GL_ZERO
        val2 = GL.GL_ZERO
        self.geom.Set(blendFunctions=(val1, val2))
        newstate = self.geom.getState()["blendFunctions"]
        self.assertEqual(newstate, ("GL_ZERO", "GL_ZERO"))

    def test_geom_blend_func_invalid(self):
        """invalid input for blend func"""
        self.assertRaises(AssertionError, self.geom.Set, blendFunctions="hai")

    def test_geom_blend_func_one(self):
        """valid input for blend func one"""
        val1 = GL.GL_ONE
        val2 = GL.GL_ONE
        self.geom.Set(blendFunctions=(val1, val2))
        newstate = self.geom.getState()["blendFunctions"]
        self.assertEqual(newstate, ("GL_ONE", "GL_ONE"))

    def test_geom_blend_func_color(self):
        """valid input for blend func color"""
        val1 = GL.GL_DST_COLOR
        val2 = GL.GL_SRC_COLOR
        self.geom.Set(blendFunctions=(val1, val2))
        newstate = self.geom.getState()["blendFunctions"]
        self.assertEqual(newstate, ("GL_DST_COLOR", "GL_SRC_COLOR"))

    def test_geom_blend_func_one_minus_color(self):
        """valid input for blend func one minus
        color
        """
        val1 = GL.GL_ONE_MINUS_DST_COLOR
        val2 = GL.GL_ONE_MINUS_SRC_COLOR
        self.geom.Set(blendFunctions=(val1, val2))
        newstate = self.geom.getState()["blendFunctions"]
        self.assertEqual(
            newstate, ("GL_ONE_MINUS_DST_COLOR", "GL.GL_ONE_MINUS_SRC_COLOR")
        )

    def test_geom_blend_func_src_alpha(self):
        """valid input for blend func src_alpha"""
        val1 = GL.GL_SRC_ALPHA
        val2 = GL.GL_SRC_ALPHA
        self.geom.Set(blendFunctions=(val1, val2))
        newstate = self.geom.getState()["blendFunctions"]
        self.assertEqual(newstate, ("GL_SRC_ALPHA", "GL_SRC_ALPHA"))

    def test_geom_blend_func_dst_alpha(self):
        """valid input for blend func dst_alpha"""
        val1 = GL.GL_DST_ALPHA
        val2 = GL.GL_DST_ALPHA
        self.geom.Set(blendFunctions=(val1, val2))
        newstate = self.geom.getState()["blendFunctions"]
        self.assertEqual(newstate, ("GL_DST_ALPHA", "GL_DST_ALPHA"))

    def test_geom_blend_func_dst_one_minus_alpha(self):
        """valid input for blend func dst_one_minus_alpha"""
        val1 = GL.GL_ONE_MINUS_DST_ALPHA
        val2 = GL.GL_ONE_MINUS_DST_ALPHA
        self.geom.Set(blendFunctions=(val1, val2))
        newstate = self.geom.getState()["blendFunctions"]
        self.assertEqual(newstate, ("GL_ONE_MINUS_DST_ALPHA", "GL_ONE_MINUS_DST_ALPHA"))

    def test_geom_blend_func_src_one_minus_alpha(self):
        """valid input for blend func src_one_minus_alpha"""
        val1 = GL.GL_ONE_MINUS_SRC_ALPHA
        val2 = GL.GL_ONE_MINUS_SRC_ALPHA
        self.geom.Set(blendFunctions=(val1, val2))
        newstate = self.geom.getState()["blendFunctions"]
        self.assertEqual(newstate, ("GL_ONE_MINUS_SRC_ALPHA", "GL_ONE_MINUS_SRC_ALPHA"))

    # instanceMatrices
    # inheritMaterial
    def xtest_geom_inheritMaterial_invalid(self):
        """invalid input for inheritMaterial
        ###### it seems that we have always been accepting this invalid data ####
        """
        self.assertRaises(AssertionError, self.geom.Set, inheritMaterial="hai")

    # inheritXform
    def test_geom_inheritXform_invalid(self):
        """invalid input for inheritXform"""
        self.assertRaises(AssertionError, self.geom.Set, inheritXform="hai")

    # inheritPointWidth
    def test_geom_inheritPointWidth_invalid(self):
        """invalid input for inheritPointWidth"""
        self.assertRaises(AssertionError, self.geom.Set, inheritPointWidth="hai")

    # inheritLineWidth
    def test_geom_inheritLineWidth_invalid(self):
        """invalid input for inheritLineWidth"""
        self.assertRaises(AssertionError, self.geom.Set, inheritLineWidth="hai")

    # inheritStippleLines
    def test_geom_inheritStippleLines_invalid(self):
        """invalid input for inheritStippleLines"""
        self.assertRaises(AssertionError, self.geom.Set, inheritStippleLines="hai")

    # inheritStipplePolygons
    def test_geom_inheritStipplePolygons_invalid(self):
        """invalid input for inheritStipplePolygons"""
        self.assertRaises(AssertionError, self.geom.Set, inheritStipplePolygons="hai")

    # inheritBackPolyMode
    def test_geom_inheritBackPolyMode_invalid(self):
        """invalid input for inheritBackPolyMode"""
        self.assertRaises(AssertionError, self.geom.Set, inheritBackPolyMode="hai")

    # inheritShading
    def test_geom_inheritShading_invalid(self):
        """invalid input for inheritShading"""
        self.assertRaises(AssertionError, self.geom.Set, inheritShading="hai")

    # inheritFrontPolyMode
    def test_geom_inheritFrontPolyMode_invalid(self):
        """invalid input for inheritFrontPolyMode"""
        self.assertRaises(AssertionError, self.geom.Set, inheritFrontPolyMode="hai")

    # inheritCulling
    def test_geom_inheritCulling_invalid(self):
        """invalid input for inheritCulling"""
        self.assertRaises(AssertionError, self.geom.Set, inheritCulling="hai")

    def test_geom_culling_inherit(self):
        """valid input for culling, inherit"""
        self.geom.culling = viewerConst.INHERIT
        self.geom.Set(culling=self.geom.culling)
        newstate = self.geom.getState()["culling"]
        self.assertEqual(newstate, "inherit")

    # transparent
    def test_geom_transparent(self):
        """valid input for transparent"""
        self.geom.Set(transparent=True)
        newstate = self.geom.getState()["transparent"]
        self.assertEqual(newstate, True)

    def test_geom_transparent_invalid(self):
        """invalid input for transparent"""
        self.assertRaises(AssertionError, self.geom.Set, transparent="hai")

    # immediateRendering
    def test_geom_immediateRendering(self):
        """valid input for immediateRendering"""
        self.geom.Set(immediateRendering=True)
        newstate = self.geom.getState()["immediateRendering"]
        self.assertEqual(newstate, True)

    def test_geom_immediateRendering_invalid(self):
        """invalid input for immediateRendering"""
        self.assertRaises(AssertionError, self.geom.Set, immediateRendering="hai")

    # frontPolyMode
    def test_geom_front_polymode(self):
        """valid input for front_polymode"""
        self.geom.Set(frontPolyMode="fill")
        newstate = self.geom.getState()["frontPolyMode"]
        self.assertEqual(newstate, "fill")

    def test_geom_front_polymode_invalid(self):
        """invalid input for front_polymode"""
        self.assertRaises(KeyError, self.geom.Set, frontPolyMode="hai")

    # backPolyMode
    def test_geom_back_polymode(self):
        """valid input for back_polymode"""
        self.geom.Set(backPolyMode="line")
        newstate = self.geom.getState()["backPolyMode"]
        self.assertEqual(newstate, "line")

    def test_geom_back_polymode_invalid(self):
        """invalid input for back_polymode"""
        self.assertRaises(KeyError, self.geom.Set, backPolyMode="hai")

    # shading
    def test_geom_shading_mode(self):
        """valid input for shadingmode"""
        self.geom.Set(shading="smooth")
        newstate = self.geom.getState()["shading"]
        self.assertEqual(newstate, "smooth")

    def test_geom_shading_mode_invalid(self):
        """valid input for shadingmode"""
        self.assertRaises(KeyError, self.geom.Set, shading="hai")

    # rotation
    def test_rotation(self):
        """valid input for rotation"""
        old_state = self.geom.getState()["rotation"]
        from mglutil.math.rotax import rotax
        import math

        matRot = rotax((0, 0, 0), (0, 0, 1), math.pi / 2.0)
        self.geom.Set(rotation=matRot)
        new_state = self.geom.getState()["rotation"]
        # hard to compare list with [4][4]array
        # self.assertEqual(new_state[0]-matRot[0][0] < .0000001, True)
        self.assertEqual(old_state != new_state, True)

    def test_rotation_invalid(self):
        """invalid input for rotation invalid"""
        self.assertRaises(ValueError, self.geom.Set, rotation="hai")

    def test_rotation_invalid_array_shape(self):
        """invalid input,bad array shape for rotation"""
        self.assertRaises(ValueError, self.geom.Set, rotation=[1, 1])

    # translation
    def test_translation(self):
        """valid input for translation"""
        self.geom.Set(translation=numpy.ones(3, "f"))
        self.assertEqual(
            numpy.alltrue(self.geom.getState()["translation"] == numpy.ones(3)), True
        )

    def test_translation_invalid(self):
        """invalid input for translation"""
        #        self.geom.Set(translation = 'hai')
        #        self.assertNotEqual(self.geom.translation, 'hai')
        self.assertRaises(ValueError, self.geom.Set, translation="hai")

    def test_translation_invalid_array_shape(self):
        """invalid input,bad array shape  for translation"""
        self.assertRaises(ValueError, self.geom.Set, translation=[1, 1])

    # scale
    def test_scale(self):
        """valid input for scale"""
        self.geom.Set(scale=Numeric.ones(3) * 2)
        self.assertEqual(
            numpy.alltrue(self.geom.getState()["scale"] == Numeric.ones(3) * 2), True
        )

    def test_scale_invalid(self):
        """invalid input for scale"""
        # self.geom.Set(scale = 'hai')
        self.assertRaises(ValueError, self.geom.Set, scale="hai")

    def test_scale_invalid_array_shape(self):
        """invalid input,bad array shape  for scale"""
        self.assertRaises(ValueError, self.geom.Set, scale=[1, 1])

    # pivot
    def test_pivot(self):
        """valid input for pivot"""
        self.geom.Set(pivot=numpy.ones(3) * 0.5)
        self.assertEqual(
            True, numpy.alltrue(self.geom.getState()["pivot"] == numpy.ones(3) * 0.5)
        )

    def test_pivot_invalid(self):
        """invalid input for pivot"""
        self.assertRaises(ValueError, self.geom.Set, pivot="hai")

    def test_pivot_invalid(self):
        """invalid input for pivot"""
        self.assertRaises(ValueError, self.geom.Set, pivot=[1, 1])


###class Geom_Method_Tests(Geom_Test):
#    """tests for methods of Geom class
# getState
# getGeomMaterialCode
# getGeomClipPlanesCode
# delete   <-abstract method
# getVertices
# getVNormals
# setViewer
# getDepthMask
# isTransparent
# GetFrontPolyMode
# GetShading
# MaterialBindingMode
# AddMaterial
# SetMaterial
# GetNormals
# Add
# SetForChildren
# setTransparency
# updateParentsForImmediateRendering
# _Hide
# _Remove
# BoundingBox
# DisplayFunction
# Draw
# RedoDisplayList
# AddClipPlane
# RemoveClipPlane
# LastParentBeforeRoot
# ApplyParentsTransform
# TransformCoords
# AllVisibleObjects
# AllObjects
# ObjSubTreeBB
# ComputeBB
# _DrawBox
# DrawTreeBoundingBox
# DrawBoundingBox
# RenderMode
# asIndexedPolygons
# sortPoly
# sortPoly_cb
# getFaces
# getFNormals
# _FixedLengthFaces
# _PrimitiveType
# """


class Geom_Viewer_Tests(unittest.TestCase):
    """tests for geom.Set in viewer"""

    def setUp(self):
        self.vi = Viewer(verbose=0)
        self.geom = Geom(name="baseTest")
        self.vi.AddObject(self.geom)
        self.vi.currentObject = self.geom

    def tearDown(self):
        """
        clean-up
        """
        try:
            self.vi.Exit()
        except:
            pass

    def test_geom_protected(self):
        """valid input for protected 0/1"""
        self.geom.Set(protected=True)
        for c in self.vi.GUI.inheritF.children.values():
            if c.__class__ == Tkinter.Menubutton and c.configure("text")[-1] == (
                "Current",
                "geom",
                "properties",
            ):
                self.inheritF_menu = c.menu
        protected_index = self.inheritF_menu.index("protected")
        self.inheritF_menu.invoke(protected_index)
        newstate = self.geom.getState()["protected"]
        self.assertEqual(newstate, False)

    #    def test_geom_lighting(self):
    #        """valid input for lighting
    #        """
    #        self.geom.Set(lighting=False)
    #        for c in self.vi.GUI.inheritF.children.values():
    #            if   c.__class__ == Tkinter.Menubutton \
    #              and c.configure('text')[-1] == ('Current', 'geom', 'properties'):
    #                self.inheritF_menu = c.menu
    #        lighting_index = self.inheritF_menu.index('lighting')
    #        self.geom.viewer.SetCurrentObject(self.geom)
    #        self.inheritF_menu.invoke(lighting_index)
    #        newstate=self.geom.getState()['lighting']
    #        self.assertEqual(newstate,True)

    def test_geom_visible(self):
        """valid input for visible"""
        self.geom.Set(visible=0)
        newstate = self.geom.getState()["visible"]
        self.assertEqual(newstate, 0)
        for c in self.vi.GUI.inheritF.children.values():
            if c.__class__ == Tkinter.Menubutton and c.configure("text")[-1] == (
                "Current",
                "geom",
                "properties",
            ):
                self.inheritF_menu = c.menu
                break
        visible_index = self.inheritF_menu.index("visible")
        self.inheritF_menu.invoke(visible_index)
        newstate = self.geom.getState()["visible"]
        self.assertEqual(newstate, 1)

    def test_geom_outline_front_polymode(self):
        """valid input for outline"""
        self.vi.currentObject.frontPolyMode = "outlines"
        self.geom.Set(outline=1.0)
        mode = viewerConst.INHERIT
        self.geom.Set(outline=True, frontPolyMode=GL.GL_FILL)
        newstate = self.geom.getState()["outline"]
        self.assertEqual(newstate, (True, True))

    def test_geom_outline_back_polymode(self):
        """valid input for outline"""
        self.vi.currentObject.backPolyMode = "outlines"
        self.geom.Set(outline=1.0)
        mode = viewerConst.INHERIT
        self.geom.Set(outline=True, backPolyMode=GL.GL_FILL)
        newstate = self.geom.getState()["outline"]
        self.assertEqual(newstate, (True, True))

    def test_geom_scissor(self):
        """valid input for scissor on/off not working,a box is displayed"""
        self.geom.Set(scissor=True)
        for c in self.vi.GUI.inheritF.children.values():
            if c.__class__ == Tkinter.Menubutton and c.configure("text")[-1] == (
                "Current",
                "geom",
                "properties",
            ):
                self.inheritF_menu = c.menu
        scissor_index = self.inheritF_menu.index("scissor")
        self.inheritF_menu.invoke(scissor_index)
        newstate = self.geom.getState()["scissor"]
        self.assertEqual(newstate, True)

    def test_geom_inheritMaterial(self):
        """valid input for inheritMaterial"""
        for c in self.vi.GUI.inheritF.children.values():
            if c.__class__ == Tkinter.Menubutton and c.configure("text")[-1] == (
                "Current",
                "geom",
                "properties",
            ):
                self.inheritF_menu = c.menu
        inheritMaterial_index = self.inheritF_menu.index("inheritMaterial")
        self.inheritF_menu.invoke(inheritMaterial_index)
        newstate = self.geom.getState()["inheritMaterial"]
        self.assertEqual(newstate, True)

    def test_geom_inheritMaterial_red(self):
        """valid input for inheritMaterial set to red ,after toggle on
        inherits from parent
        """
        self.geom.Set(materials=((1, 0, 0),))
        for c in self.vi.GUI.inheritF.children.values():
            if c.__class__ == Tkinter.Menubutton and c.configure("text")[-1] == (
                "Current",
                "geom",
                "properties",
            ):
                self.inheritF_menu = c.menu
        inheritMaterial_index = self.inheritF_menu.index("inheritMaterial")
        self.inheritF_menu.invoke(inheritMaterial_index)
        newstate = self.geom.getState()["inheritMaterial"]
        self.assertEqual(self.geom.materials == (1, 0, 0), False)

    def test_geom_inheritXform(self):
        """valid input for inheritXform"""
        for c in self.vi.GUI.inheritF.children.values():
            if c.__class__ == Tkinter.Menubutton and c.configure("text")[-1] == (
                "Current",
                "geom",
                "properties",
            ):
                self.inheritF_menu = c.menu
        inheritXform_index = self.inheritF_menu.index("inheritXform")
        self.inheritF_menu.invoke(inheritXform_index)
        newstate = self.geom.getState()["inheritXform"]
        self.assertEqual(newstate, True)


#    def test_geom_inheritPointWidth(self):
#        """valid input for inheritPointWidth
#        """
#        for c in self.vi.GUI.inheritF.children.values():
#            if   c.__class__ == Tkinter.Menubutton \
#              and c.configure('text')[-1] == ('Current', 'geom', 'properties'):
#                self.inheritF_menu = c.menu
#        inheritPointWidth_index = self.inheritF_menu.index('inheritPointWidth')
#        self.inheritF_menu.invoke(inheritPointWidth_index)
#        newstate=self.geom.getState()['inheritPointWidth']
#        self.assertEqual(newstate,True)
#
#
#    def test_geom_inheritLineWidth(self):
#        """valid input for inheritLineWidth
#        """
#        for c in self.vi.GUI.inheritF.children.values():
#            if   c.__class__ == Tkinter.Menubutton \
#              and c.configure('text')[-1] == ('Current', 'geom', 'properties'):
#                self.inheritF_menu = c.menu
#        inheritLineWidth_index = self.inheritF_menu.index('inheritLineWidth')
#        self.inheritF_menu.invoke(inheritLineWidth_index)
#        newstate=self.geom.getState()['inheritLineWidth']
#        self.assertEqual(newstate,True)
#
#
#    def test_geom_inheritStippleLines(self):
#        """valid input for inheritStippleLines
#        """
#        for c in self.vi.GUI.inheritF.children.values():
#            if   c.__class__ == Tkinter.Menubutton \
#              and c.configure('text')[-1] == ('Current', 'geom', 'properties'):
#                self.inheritF_menu = c.menu
#        inheritStippleLines_index = self.inheritF_menu.index('inheritStippleLines')
#        self.inheritF_menu.invoke(inheritStippleLines_index)
#        newstate=self.geom.getState()['inheritStippleLines']
#        self.assertEqual(newstate,True)


#    def test_geom_inheritStipplePolygons(self):
#        """valid input for inheritStipplePolygons
#        """
#        for c in self.vi.GUI.inheritF.children.values():
#            if   c.__class__ == Tkinter.Menubutton \
#              and c.configure('text')[-1] == ('Current', 'geom', 'properties'):
#                self.inheritF_menu = c.menu
#        inheritStipplePolygons_index = self.inheritF_menu.index('inheritStipplePolygons')
#        self.inheritF_menu.invoke(inheritStipplePolygons_index)
#        newstate=self.geom.getState()['inheritStipplePolygons']
#        self.assertEqual(newstate,True)


#    def test_geom_inheritFrontPolyMode(self):
#        """valid input for inheritFrontPolyMode
#        """
#        self.geom.Set(inheritFrontPolyMode = True)
#        for c in self.vi.GUI.inheritF.children.values():
#            if c.__class__==Tkinter.Menubutton:
#                self.inheritF_menu = c.menu
#        inheritFrontPolyMode_index = self.inheritF_menu.index('inheritFrontPolyMode')
#        self.inheritF_menu.invoke(inheritFrontPolyMode_index)
#        newstate=self.geom.getState()['inheritFrontPolyMode']
#        self.assertEqual(newstate,True)


#    def test_geom_inheritBacktPolyMode(self):
#        """valid input for inheritBackPolyMode
#        """
#        for c in self.vi.GUI.inheritF.children.values():
#            if c.__class__==Tkinter.Menubutton:
#                self.inheritF_menu = c.menu
#        inheritBackPolyMode_index = self.inheritF_menu.index('inheritBackPolyMode')
#        self.inheritF_menu.invoke(inheritBackPolyMode_index)
#        newstate=self.geom.getState()['inheritBackPolyMode']
#        self.assertEqual(newstate,True)


#    def test_geom_inheritShading(self):
#        """valid input for inheritShading
#        """
#        for c in self.vi.GUI.inheritF.children.values():
#            if c.__class__==Tkinter.Menubutton:
#                self.inheritF_menu = c.menu
#        inheritShading_index = self.inheritF_menu.index('inheritShading')
#        self.inheritF_menu.invoke(inheritShading_index)
#        newstate=self.geom.getState()['inheritShading']
#        self.assertEqual(newstate,True)


#    def test_geom_inheritCulling(self):
#        """valid input for inheritCulling
#        """
#        self.geom.inheritCulling=True
#        for c in self.vi.GUI.inheritF.children.values():
#            if c.__class__==Tkinter.Menubutton:
#                self.inheritF_menu = c.menu
#        inheritCulling_index = self.inheritF_menu.index('inheritCulling')
#        self.inheritF_menu.invoke(inheritCulling_index)
#        newstate=self.geom.getState()['inheritCulling']
#        self.assertEqual(newstate,True)


class IndexedGeom_Set_Tests(unittest.TestCase):
    """
    keywords = Geom.keywords + [
     'type',
     'faces',
     'fnormals',
     'freshape',
     ]
    """

    def setUp(self):
        self.geom = IndexedGeom(name="indexed_baseTest")

    def tearDown(self):
        """
        clean-up
        """
        try:
            del self.geom
        except:
            pass

    # type
    def test_IndexedGeom_types_invalid(self):
        """invalid input for types"""
        self.assertRaises(AttributeError, self.geom, primitiveType="hai")

    # GL_TRIANGLES, GL_QUADS... are the same as type?????
    def test_IndexedGeom_types_GL_TRIANGLES(self):
        """valid input GL_TRIANGLES"""
        self.geom.primitiveType = GL.GL_TRIANGLES
        self.assertEqual(self.geom.primitiveType, 4)

    def test_IndexedGeom_types_GL_QUADS(self):
        """valid input GL_QUADS"""
        self.geom.primitiveType = GL.GL_QUADS
        self.assertEqual(self.geom.primitiveType, 7)

    def test_IndexedGeom_types_GL_POLYGONS(self):
        """valid input GL_POLYGONS"""
        self.geom.primitiveType = GL.GL_POLYGON
        self.assertEqual(self.geom.primitiveType, 9)

    # faces
    def test_IndexedGeom_faces(self):
        """test faces"""
        self.geom.Set(vertices=[[0, 0, 0], [1, 0, 0]], faces=((0, 1),))
        self.assertEqual(len(self.geom.faceSet.faces.array), 1)

    def test_IndexedGeom_faces_invalid_not_sequence(self):
        """invalid input for faces, afces should be list of lists of integers"""
        self.assertRaises(TypeError, self.geom.Set, faces=20)

    def test_IndexedGeom_faces_invalid_indices(self):
        """invalid input for faces, -20 not a good index"""
        self.assertRaises(ValueError, self.geom.Set, faces=[[-20, 3, 4]])

    def test_IndexedGeom_faces_set(self):
        """valid input for faces"""
        self.geom.Set(
            vertices=[[0, 0, 0], [1, 0, 0]],
            faces=(
                (0, 1),
                (1, 0),
            ),
        )
        self.assertEqual(len(self.geom.faceSet.faces.array), 2)

    # fnormals
    def test_IndexedGeom_fnormals(self):
        """test fnormals"""
        self.geom.Set(vertices=[[0, 0, 0], [1, 0, 0]], faces=((0, 1),))
        self.assertEqual(self.geom.faceSet.normals.GetProperty(), None)

    def test_IndexedGeom_fnormals_invalid(self):
        """invalid input fnormals"""
        self.geom.Set(vertices=[[0, 0, 0], [1, 0, 0]], faces=((0, 1),))
        self.assertRaises(ValueError, self.geom.Set, fnormals="hai")

    # normals
    def test_IndexedGeom_normals(self):
        """valid input for normals"""
        self.geom.faceSet.normals.SetValues([(0, 1), (1, 0)])
        self.assertEqual(len(self.geom.faceSet.normals), 2)


# freshape !!!!!!NOT DONE!!!!!!!

###class IndexedGeom_Method_Tests(Geom_Test):
###    """tests for methods of IndexedGeom class
# methods:
# getFaces
# getFNormals
# _FixedLengthFaces
# _PrimitiveType
# Add
# Set
# ComputeVertexNormals
# ComputeFaceNormals
# VertexNormalFunction
# FaceNormalFunction
# sortPoly
# DisplayFunction
# Draw
# RedoDisplayList
# removeDuplicatedVertices


if __name__ == "__main__":
    test_cases = [
        "Geom__init__Tests",
        "Geom_Set_Tests",
        "Geom_Viewer_Tests",
        "IndexedGeom_Set_Tests",
    ]

    unittest.main(
        argv=(
            [
                __name__,
            ]
            + test_cases
        )
    )
    # remove the -v flag to make output cleaner
    # unittest.main( argv=([__name__ ,'-v'] + test_cases) )
    # unittest.main()
