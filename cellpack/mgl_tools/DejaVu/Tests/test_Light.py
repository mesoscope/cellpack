## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by

#
# $Id:
#


import unittest
from opengltk.OpenGL import GL
from opengltk.exception import GLerror
from opengltk.extent.utillib import glCleanRotMat
import numpy.oldnumeric as Numeric
from DejaVu import Viewer
from DejaVu.Spheres import Spheres
import math
from mglutil.math.rotax import rotax
from DejaVu.colorTool import OneColor
from DejaVu.Transformable import Transformable


class Light_BaseTests(unittest.TestCase):
    """
    setUp + tearDown form a fixture: working environment for the testing code
    """

    def setUp(self):
        """
        start Viewer
        """
        if not hasattr(self, "vi"):
            self.vi = Viewer(verbose=False)
            # self.vi.cameras[0].master.master.withdraw()
            self.light = self.vi.currentLight
            self.orig_state = self.light.getState()

    def tearDown(self):
        """
        clean-up
        """
        try:
            self.vi.Exit()
        except:
            pass

    # Name
    def test_Name(self):
        """Name is light0"""
        self.assertEqual(self.light.name, "light 0")

    # end Name

    # AMBIENT
    def test_Set_ambient_attr(self):
        """Set ambient changes light ambient attribute"""
        self.light.Set(ambient=(0.0, 0.5, 0.5, 1.0))
        ambi = self.light.ambient
        self.assertEqual(ambi[0], 0)
        self.assertEqual(round(ambi[1], 1), 0.5)
        self.assertEqual(round(ambi[2], 1), 0.5)
        self.assertEqual(round(ambi[3], 1), 1.0)

    def test_Setambient_GL(self):
        """Set ambient changes GL_AMBIENT"""
        self.light.Set(ambient=(0, 0, 0, 0))
        ambi = GL.glGetLightfv(self.light.num, GL.GL_AMBIENT)
        self.assertEqual(ambi[0], 0)
        self.assertEqual(ambi[1], 0.0)
        self.assertEqual(ambi[2], 0.0)
        self.assertEqual(ambi[3], 0.0)

    def test_Setambient_state(self):
        """Set light changes light's state['ambient']"""
        self.light.Set(ambient=(1, 0, 0, 0))
        state = self.light.getState()
        ambi = state["ambient"]
        self.assertEqual(round(ambi[0], 1), 1.0)
        self.assertEqual(ambi[1], 0.0)
        self.assertEqual(ambi[2], 0.0)
        self.assertEqual(ambi[3], 0.0)

    def test_Setambient_bad_input(self):
        """ValueError raised on bad input to Set ambient"""
        self.assertRaises(ValueError, self.light.Set, ambient=(1, 0))

    def test_Setambient_empty_input(self):
        """ValueError raised on empty input to Set ambient"""
        self.assertRaises(ValueError, self.light.Set, ambient=())

    def test_Setambient_too_much_input(self):
        """ValueError raised on too_much input to Set ambient"""
        self.assertRaises(ValueError, self.light.Set, ambient=(1, 0, 0, 1, 1))

    # end AMBIENT

    # DIFFUSE

    def test_Set_diffuse_attr(self):
        """Set diffuse changes light diffuse attribute"""
        self.light.Set(diffuse=(0.0, 0.5, 0.5, 1.0))
        diffuse = self.light.diffuse
        self.assertEqual(diffuse[0], 0)
        self.assertEqual(round(diffuse[1], 1), 0.5)
        self.assertEqual(round(diffuse[2], 1), 0.5)
        self.assertEqual(round(diffuse[3], 1), 1.0)

    def test_Setdiffuse_GL(self):
        """Set diffuse changes GL_DIFFUSE"""
        self.light.Set(diffuse=(1, 0, 0, 0))
        diffuse = GL.glGetLightfv(self.light.num, GL.GL_DIFFUSE)
        self.assertEqual(round(diffuse[0], 1), 1.0)
        self.assertEqual(diffuse[1], 0.0)
        self.assertEqual(diffuse[2], 0.0)
        self.assertEqual(diffuse[3], 0.0)

    def test_Setdiffuse_state(self):
        """Set light changes light's state['diffuse']"""
        self.light.Set(diffuse=(1, 0, 0, 0))
        state = self.light.getState()
        diffuse = state["diffuse"]
        self.assertEqual(round(diffuse[0], 1), 1.0)
        self.assertEqual(diffuse[1], 0.0)
        self.assertEqual(diffuse[2], 0.0)
        self.assertEqual(diffuse[3], 0.0)

    def test_Setdiffuse_bad_input(self):
        """ValueError raised on bad input to Set diffuse"""
        self.assertRaises(ValueError, self.light.Set, diffuse=(1, 0))

    def test_Setdiffuse_empty_input(self):
        """ValueError raised on empty input to Set diffuse"""
        self.assertRaises(ValueError, self.light.Set, diffuse=())

    def test_Setdiffuse_too_much_input(self):
        """ValueError raised on too_much input to Set diffuse"""
        self.assertRaises(ValueError, self.light.Set, diffuse=(1, 0, 0, 1, 1))

    # end DiFFUSE

    # SPECULAR

    def test_Set_specular_attr(self):
        """Set specular changes light specular attribute"""
        self.light.Set(specular=(0.0, 0.5, 0.5, 1.0))
        specular = self.light.specular
        self.assertEqual(specular[0], 0)
        self.assertEqual(round(specular[1], 1), 0.5)
        self.assertEqual(round(specular[2], 1), 0.5)
        self.assertEqual(round(specular[3], 1), 1.0)

    def test_Setspecular_GL(self):
        """Set specular changes GL_SPECULAR"""
        self.light.Set(specular=(1, 0, 0, 0))
        specular = GL.glGetLightfv(self.light.num, GL.GL_SPECULAR)
        self.assertEqual(round(specular[0], 1), 1.0)
        self.assertEqual(specular[1], 0.0)
        self.assertEqual(specular[2], 0.0)
        self.assertEqual(specular[3], 0.0)

    def test_Setspecular_state(self):
        """Set light changes light's state['specular']"""
        self.light.Set(specular=(1, 0, 0, 0))
        state = self.light.getState()
        specular = state["specular"]
        self.assertEqual(round(specular[0], 1), 1.0)
        self.assertEqual(specular[1], 0.0)
        self.assertEqual(specular[2], 0.0)
        self.assertEqual(specular[3], 0.0)

    def test_Setspecular_bad_input(self):
        """ValueError raised on bad input to Set specular"""
        self.assertRaises(ValueError, self.light.Set, specular=(1, 0))

    def test_Setspecular_empty_input(self):
        """ValueError raised on empty input to Set specular"""
        self.assertRaises(ValueError, self.light.Set, specular=())

    def test_Setspecular_too_much_input(self):
        """ValueError raised on too_much input to Set specular"""
        self.assertRaises(ValueError, self.light.Set, specular=(1, 0, 0, 1, 1))

    # END SPECULAR

    # DIRECTION

    def test_Set_direction_attr(self):
        """Set direction changes light direction attribute"""
        self.light.Set(direction=(1, 1, 1, 0))
        direction = self.light.direction
        self.assertEqual(direction[0], 1)
        self.assertEqual(round(direction[1], 1), 1)
        self.assertEqual(round(direction[2], 1), 1)
        self.assertEqual(round(direction[3], 1), 0)

    def test_Setdirection_state(self):
        """Set light changes light's state['direction']"""
        self.light.Set(direction=(1, 0, 0, 0))
        state = self.light.getState()
        direction = state["direction"]
        self.assertEqual(round(direction[0], 1), 1.0)
        self.assertEqual(direction[1], 0.0)
        self.assertEqual(direction[2], 0.0)
        self.assertEqual(direction[3], 0.0)

    def test_Setdirection_bad_input(self):
        """AssertionError raised on bad input to Set direction"""
        self.assertRaises(AssertionError, self.light.Set, direction=(1, 0))

    def test_Setdirection_empty_input(self):
        """AssertionError raised on empty input to Set direction"""
        self.assertRaises(AssertionError, self.light.Set, direction=())

    def test_Setdirection_too_much_input(self):
        """AssertionError raised on too_much input to Set direction"""
        self.assertRaises(AssertionError, self.light.Set, direction=(1, 0, 0, 1, 1))

    # END DIRECTION

    # POSITION

    def test_Set_position_attr(self):
        """Set position changes light position attribute"""
        self.light.Set(position=(1, 1, 1, 1))
        position = self.light.position
        self.assertEqual(position[0], 1)
        self.assertEqual(round(position[1], 1), 1)
        self.assertEqual(round(position[2], 1), 1)
        self.assertEqual(round(position[3], 1), 1)

    def test_Setposition_state(self):
        """Set position changes light's state['position']"""
        self.light.Set(position=(1, 0, 0, 1))
        state = self.light.getState()
        position = state["position"]
        self.assertEqual(round(position[0], 1), 1.0)
        self.assertEqual(position[1], 0.0)
        self.assertEqual(position[2], 0.0)
        self.assertEqual(position[3], 1.0)

    def test_Setposition_bad_input(self):
        """AssertionError raised on bad input to Set position"""
        self.assertRaises(AssertionError, self.light.Set, position=(1, 0))

    def test_Setposition_empty_input(self):
        """AssertionError raised on empty input to Set position"""
        self.assertRaises(AssertionError, self.light.Set, position=())

    def test_Setposition_too_much_input(self):
        """AssertionError raised on too_much input to Set position"""
        self.assertRaises(AssertionError, self.light.Set, position=(1, 0, 0, 1, 1))

    # END POSITION

    # SPOT DIRECTION
    def test_Set_spotDirection_attr(self):
        """Set spotDirection changes light spotDirection attribute"""
        self.light.Set(spotDirection=(1, 1, -1, 0))
        spotDirection = self.light.spotDirection
        self.assertEqual(spotDirection[0], 1)
        self.assertEqual(round(spotDirection[1], 1), 1)
        self.assertEqual(round(spotDirection[2], 1), -1)
        self.assertEqual(round(spotDirection[3], 1), 0)

    def test_SetspotDirection_state(self):
        """Set light changes light's state['spotDirection']"""
        self.light.Set(spotDirection=(1, 0, 0, 0))
        state = self.light.getState()
        spotDirection = state["spotDirection"]
        self.assertEqual(round(spotDirection[0], 1), 1.0)
        self.assertEqual(spotDirection[1], 0.0)
        self.assertEqual(spotDirection[2], 0.0)
        self.assertEqual(spotDirection[3], 0.0)

    def test_SetspotDirection_bad_input(self):
        """AssertionError raised on bad input to Set spotDirection"""
        self.assertRaises(AssertionError, self.light.Set, spotDirection=(1, 0))

    def test_SetspotDirection_empty_input(self):
        """AssertionError raised on empty input to Set spotDirection"""
        self.assertRaises(AssertionError, self.light.Set, spotDirection=())

    def test_SetspotDirection_too_much_input(self):
        """AssertionError raised on too_much input to Set spotDirection"""
        self.assertRaises(AssertionError, self.light.Set, spotDirection=(1, 0, 0, 1, 1))

    # END SPOT DIRECTION

    # SPOT EXPONENT

    def test_Set_spotExponent_attr(self):
        """Set spotExponent changes light spotExponent attribute"""
        self.light.Set(spotExponent=1.0)
        spotExponent = self.light.spotExponent
        self.assertEqual(spotExponent, 1.0)

    def test_SetspotExponent_state(self):
        """Set light changes light's state['spotExponent']"""
        self.light.Set(spotExponent=1.0)
        state = self.light.getState()
        spotExponent = state["spotExponent"]
        self.assertEqual(round(spotExponent, 1), 1.0)

    def test_SetspotExponent_bad_input(self):
        """ValueError raised on bad input to Set spotExponent"""
        self.assertRaises(ValueError, self.light.Set, spotExponent="shkdj")

    def test_SetspotExponent_empty_input(self):
        """ValueError raised on empty input to Set spotExponent"""
        self.assertRaises(ValueError, self.light.Set, spotExponent=" ")

    def test_SetspotExponent_too_much_input(self):
        """ValueError raised on too_much input to Set
        spotExponent**************
        """
        self.assertRaises(GLerror, self.light.Set, spotExponent=3265467)

    # END SPOT EXPONENT

    # SPOT CUT OFF
    def test_Set_spotCutoff_attr(self):
        """Set spotCutoff changes light spotCutoff attribute"""
        self.light.Set(spotCutoff=180)
        spotCutoff = self.light.spotCutoff
        self.assertEqual(spotCutoff, 180)

    def test_SetspotCutoff_state(self):
        """Set light changes light's state['spotCutoff']"""
        self.light.Set(spotCutoff=180)
        state = self.light.getState()
        spotCutoff = state["spotCutoff"]
        self.assertEqual(round(spotCutoff, 1), 180)

    def test_SetspotCutoff_bad_input(self):
        """ValueError raised on bad input to Set spotCutoff"""
        self.assertRaises(ValueError, self.light.Set, spotCutoff="tuyu")

    def test_SetspotCutoff_empty_input(self):
        """ValueError raised on empty input to Set spotCutoff"""
        self.assertRaises(ValueError, self.light.Set, spotCutoff=" ")

    def test_SetspotCutoff_too_much_input(self):
        """ValueError raised on too_much input to Set spotCutoff"""
        self.assertRaises(ValueError, self.light.Set, spotCutoff=3265467)

    # end SPOT CUT OFF

    # CONSTANT ATTENUATION

    def test_Set_constantAttenuation_attr(self):
        """Set constantAttenuation changes light constantAttenuation attribute"""
        self.light.Set(constantAttenuation=2.0)
        constantAttenuation = self.light.constantAttenuation
        self.assertEqual(constantAttenuation, 2.0)

    def test_SetconstantAttenuation_state(self):
        """Set light changes light's state['constantAttenuation']"""
        self.assertRaises(ValueError, self.light.Set, constantAttenuation=-2.0)

    def test_SetconstantAttenuation_bad_input(self):
        """ValueError raised on bad input to Set constantAttenuation"""
        self.assertRaises(ValueError, self.light.Set, constantAttenuation="hdi")

    def test_SetconstantAttenuation_empty_input(self):
        """ValueError raised on empty input to Set
        constantAttenuation
        """
        self.assertRaises(ValueError, self.light.Set, constantAttenuation=" ")

    # END CONSTANT ATTENUATION

    # LINEAR ATTENUATION

    def test_Set_linearAttenuation_attr(self):
        """Set linearAttenuation changes light linearAttenuation attribute"""
        self.light.Set(linearAttenuation=2.0)
        linearAttenuation = self.light.linearAttenuation
        self.assertEqual(linearAttenuation, 2.0)

    def test_SetlinearAttenuation_state(self):
        """Set light changes light's state['linearAttenuation']"""
        self.assertRaises(ValueError, self.light.Set, linearAttenuation=-2.0)

    def test_SetlinearAttenuation_bad_input(self):
        """ValueError raised on bad input to Set linearAttenuation"""
        self.assertRaises(ValueError, self.light.Set, linearAttenuation="hdi")

    def test_SetlinearAttenuation_empty_input(self):
        """ValueError raised on empty input to Set linearAttenuation"""
        self.assertRaises(ValueError, self.light.Set, linearAttenuation=" ")

    # END LINEAR ATTENUATION

    # QUADRATIC ATTENUATION
    def test_Set_quadraticAttenuation_attr(self):
        """Set quadraticAttenuation changes light quadraticAttenuation attribute"""
        self.light.Set(quadraticAttenuation=2.0)
        quadraticAttenuation = self.light.quadraticAttenuation
        self.assertEqual(quadraticAttenuation, 2.0)

    def test_SetquadraticAttenuation_state(self):
        """Set light changes light's state['quadraticAttenuation']"""
        self.assertRaises(ValueError, self.light.Set, quadraticAttenuation=-2.0)

    def test_SetquadraticAttenuation_bad_input(self):
        """ValueError raised on bad input to Set quadraticAttenuation"""
        self.assertRaises(ValueError, self.light.Set, quadraticAttenuation="hdi")

    def test_SetquadraticAttenuation_empty_input(self):
        """ValueError raised on empty input to Set quadraticAttenuation"""
        self.assertRaises(ValueError, self.light.Set, quadraticAttenuation=" ")

    # END QUADRATIC ATTENUATION

    # POSITIONAL

    def test_Set_positional_attr(self):
        """Set positional changes light positional attribute"""
        self.light.Set(position=[0, 0, 1, 0])
        positional = self.light.positional
        self.assertEqual(positional, True)

    def test_Setpositional_state(self):
        """Set light changes light's state['positional']"""
        self.light.Set(position=[0, 0, 1, 0])
        state = self.light.getState()
        positional = state["positional"]
        self.assertEqual(positional, True)

    def test_Setpositional_bad_input(self):
        """AttributeError raised on bad input to Set positional"""
        self.assertRaises(AttributeError, self.light.Set, positional="hdi")

    def test_Setpositional_empty_input(self):
        """AttributeError raised on empty input to Set positional"""
        self.assertRaises(AttributeError, self.light.Set, positional=" ")

    def test_Setpositional_invalid_input(self):
        """AttributeError raised on invalid input to Set positional"""
        self.assertRaises(AttributeError, self.light.Set, positional=2.0)

    # END POSITIONAL

    # ENABLED
    def test_Set_enabled_attr(self):
        """Set enabled changes light enabled attribute"""
        self.light.Set(enabled=False)

        enabled = self.light.enabled
        self.assertEqual(enabled, False)

    def test_Setenabled_GL(self):
        """Set enabled changes GL_LIGHTi"""
        self.light.Set(enabled=False)
        enabled = GL.glIsEnabled(self.light.num)
        self.assertEqual(enabled, False)

    def test_Setenabled_state(self):
        """Set light changes light's state['enabled']"""
        self.light.Set(enabled=False)
        state = self.light.getState()
        enabled = state["enabled"]
        self.assertEqual(round(enabled, 1), False)

    def test_Setenabled_bad_input(self):
        """AttributeError raised on bad input to Set enabled"""
        self.assertRaises(AttributeError, self.light.Set, enabled="hdi")

    def test_Setenabled_empty_input(self):
        """AttributeError raised on empty input to Set enabled"""
        self.assertRaises(AttributeError, self.light.Set, enabled=" ")

    # END ENABLED

    # VISIBLE
    def test_Set_visible_attr(self):
        """Set visible changes light visible attribute"""
        self.light.Set(visible=True)
        visible = self.light.visible
        self.assertEqual(visible, True)

    def test_Setvisible_state(self):
        """Set light changes light's state['visible']"""
        self.light.Set(visible=True)
        state = self.light.getState()
        visible = state["visible"]
        self.assertEqual(round(visible, 1), True)

    def test_Setvisible_bad_input(self):
        """AttributeError raised on bad input to Set visible"""
        self.assertRaises(AttributeError, self.light.Set, visible=58768)

    def test_Setvisible_empty_input(self):
        """AttributeError raised on empty input to Set visible"""
        self.assertRaises(AttributeError, self.light.Set, visible=" ")

    # END VISIBLE

    # LINE WIDTH
    def test_Set_lineWidth_attr(self):
        """Set lineWidth changes light lineWidth attribute"""
        self.light.Set(lineWidth=4)
        lineWidth = self.light.lineWidth
        self.assertEqual(lineWidth, 4)

    def test_SetlineWidth_state(self):
        """Set light changes light's state['lineWidth']"""
        self.light.Set(lineWidth=3)
        state = self.light.getState()
        lineWidth = state["lineWidth"]
        self.assertEqual(round(lineWidth, 1), 3)

    def test_SetlineWidth_bad_input(self):
        """ValueError raised on bad input to Set lineWidth"""
        self.assertRaises(ValueError, self.light.Set, lineWidth="hdi")

    def test_SetlineWidth_bad_input1(self):
        """AttributeError raised on bad input negative values to Set lineWidth"""
        self.assertRaises(AttributeError, self.light.Set, lineWidth=-8)

    def test_SetlineWidth_empty_input(self):
        """ValueError raised on empty input to Set lineWidth"""
        self.assertRaises(ValueError, self.light.Set, lineWidth=" ")

    # END LINE WIDTH

    # LENGTH
    def test_Set_length_attr(self):
        """Set length changes light length attribute"""
        self.light.Set(length=4.0)
        length = self.light.length
        self.assertEqual(length, 4.0)

    def test_Setlength_state(self):
        """Set light changes light's state['length']"""
        self.light.Set(length=3.0)
        state = self.light.getState()
        length = state["length"]
        self.assertEqual(round(length, 1), 3.0)

    def test_Setlength_bad_input(self):
        """ValueError raised on bad input  negative values to Set length"""
        self.assertRaises(ValueError, self.light.Set, length="hdi")

    def test_Setlength_bad_input1(self):
        """AttributeError raised on bad input to Set length"""
        self.assertRaises(AttributeError, self.light.Set, length=-8)

    def test_Setlength_empty_input(self):
        """ValueAttributeError raised on empty input to Set length"""
        self.assertRaises(ValueError, self.light.Set, length=" ")

    # END LENGTH

    ##ANTIALIASED
    #    def test_Set_antialiased_attr(self):
    #        """ Set antialiased changes light antialiased attribute
    #        """
    #        self.light.Set(antialiased=True)
    #        antialiased = self.light.antialiased
    #        self.assertEqual(antialiased,True)
    #
    #
    #    def test_Setantialiased_state(self):
    #        """ Set light changes light's state['antialiased']
    #        """
    #        self.light.Set(antialiased=True)
    #        state = self.light.getState()
    #        antialiased = state['antialiased']
    #        self.assertEqual(round(antialiased,1), True)
    #
    #
    #    def test_Setantialiased_bad_input(self):
    #        """ ValueError raised on bad input to Set antialiased
    #        """
    #        self.assertRaises(ValueError, self.light.Set ,antialiased='hai')
    #
    #
    #    def test_Setantialiased_empty_input(self):
    #        """ ValueError raised on empty input to Set antialiased
    #        """
    #        self.assertRaises(ValueError, self.light.Set, antialiased=' ')
    ##END ANTIALIASED

    # ROTATION

    def test_Set_rotation_attr(self):
        """Set rotation changes light rotation attribute"""
        self.light.Set(
            rotation=[
                1.0,
                2.0,
                3.0,
                4.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
            ]
        )
        rotation = self.light.rotation
        self.assertEqual(round(rotation[0], 1), 1)
        self.assertEqual(round(rotation[1], 1), 2)
        self.assertEqual(round(rotation[2], 1), 3)
        self.assertEqual(round(rotation[3], 1), 4)

    def test_Setrotation_state(self):
        """Set light changes light's state['rotation']"""
        self.light.Set(
            rotation=[
                1.0,
                2.0,
                3.0,
                4.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
            ]
        )
        state = self.light.getState()
        rotation = state["rotation"]
        self.assertEqual(round(rotation[0], 1), 1.0)
        self.assertEqual(round(rotation[1], 1), 2.0)
        self.assertEqual(round(rotation[2], 1), 3.0)
        self.assertEqual(round(rotation[3], 1), 4.0)

    def test_Setrotation_bad_input(self):
        """ValueError raised on bad input to Set rotation"""
        self.assertRaises(ValueError, self.light.Set, rotation=[1, 0])

    def test_Setrotation_empty_input(self):
        """ValueError raised on empty input to Set rotation"""
        self.assertRaises(ValueError, self.light.Set, rotation=[])

    def test_Setrotation_string_input(self):
        """ValueError raised on string input to Set rotation"""
        self.assertRaises(
            ValueError, self.light.Set, rotation=["a", "c", "b", "n", "s", "j"]
        )

    # END ROTATION

    # TRNSLATION
    def test_Set_translation_attr(self):
        """Set translation changes light translation attribute"""
        self.light.Set(translation=[1, 1, 0])
        translation = self.light.translation
        self.assertEqual(translation[0], 1)
        self.assertEqual(round(translation[1], 1), 1)
        self.assertEqual(round(translation[2], 1), 0)

    def test_Settranslation_state(self):
        """Set light changes light's state['translation']"""
        self.light.Set(translation=[1, 0, 0])
        state = self.light.getState()
        translation = state["translation"]
        self.assertEqual(round(translation[0], 1), 1.0)
        self.assertEqual(translation[1], 0.0)
        self.assertEqual(translation[2], 0.0)

    def test_Settranslation_bad_input(self):
        """ValueError raised on bad input to Set translation"""
        self.assertRaises(ValueError, self.light.Set, translation=[1, 0])

    def test_Settranslation_empty_input(self):
        """ValueError raised on empty input to Set translation"""
        self.assertRaises(ValueError, self.light.Set, translation=[])

    def test_Settranslation_too_much_input(self):
        """ValueError raised on too_much input to Set translation"""
        self.assertRaises(ValueError, self.light.Set, translation=[1, 0, 0, 1, 1])

    # END TRANSLATION

    # SCALE

    def test_Set_scale_attr(self):
        """Set scale changes light scale attribute"""
        self.light.Set(scale=[1, 1, 0])
        scale = self.light.scale
        self.assertEqual(scale[0], 1)
        self.assertEqual(round(scale[1], 1), 1)
        self.assertEqual(round(scale[2], 1), 0)

    def test_Setscale_state(self):
        """Set light changes light's state['scale']"""
        self.light.Set(scale=[1, 0, 0])
        state = self.light.getState()
        scale = state["scale"]
        self.assertEqual(round(scale[0], 1), 1.0)
        self.assertEqual(scale[1], 0.0)
        self.assertEqual(scale[2], 0.0)

    def test_Setscale_bad_input(self):
        """ValueError raised on bad input to Set scale"""
        self.assertRaises(ValueError, self.light.Set, scale=[1, 0])

    def test_Setscale_empty_input(self):
        """ValueError raised on empty input to Set scale"""
        self.assertRaises(ValueError, self.light.Set, scale=[])

    def test_Setscale_too_much_input(self):
        """ValueError raised on too_much input to Set scale"""
        self.assertRaises(ValueError, self.light.Set, scale=[1, 0, 0, 1, 1])

    # END SCALE

    # PIVOT

    def test_Set_pivot_attr(self):
        """Set pivot changes light pivot attribute"""
        self.light.Set(pivot=[1, 1, 0])
        pivot = self.light.pivot
        self.assertEqual(pivot[0], 1)
        self.assertEqual(round(pivot[1], 1), 1)
        self.assertEqual(round(pivot[2], 1), 0)

    def test_Setpivot_state(self):
        """Set light changes light's state['pivot']"""
        self.light.Set(pivot=[1, 0, 0])
        state = self.light.getState()
        pivot = state["pivot"]
        self.assertEqual(round(pivot[0], 1), 1.0)
        self.assertEqual(pivot[1], 0.0)
        self.assertEqual(pivot[2], 0.0)

    def test_Setpivot_bad_input(self):
        """ValueError raised on bad input to Set pivot"""
        self.assertRaises(ValueError, self.light.Set, pivot=[1, 0])

    def test_Setpivot_empty_input(self):
        """ValueError raised on empty input to Set pivot"""
        self.assertRaises(ValueError, self.light.Set, pivot=[])

    def test_Setpivot_too_much_input(self):
        """ValueError raised on too_much input to Set pivot"""
        self.assertRaises(ValueError, self.light.Set, pivot=[1, 0, 0, 1, 1])


# END PIVOT
class LightModel_BaseTests(unittest.TestCase):
    """
    setUp + tearDown form a fixture: working environment for the testing code
    """

    def setUp(self):
        """
        start Viewer
        """
        if not hasattr(self, "vi"):
            self.vi = Viewer(verbose=False)
            # self.vi.cameras[0].master.master.withdraw()
            self.lightModel = self.vi.lightModel
            self.orig_state = self.lightModel.getState()

    def tearDown(self):
        """
        clean-up
        """
        try:
            self.vi.Exit()
        except:
            pass

    # AMBI
    def test_Set_ambi_attr(self):
        """Set ambi changes light ambi attribute"""
        self.lightModel.Set(ambient=(0.0, 0.5, 0.5, 1.0))
        ambi = self.lightModel.ambient
        self.assertEqual(ambi[0], 0)
        self.assertEqual(round(ambi[1], 1), 0.5)
        self.assertEqual(round(ambi[2], 1), 0.5)
        self.assertEqual(round(ambi[3], 1), 1.0)

    def test_Setambi_GL(self):
        """Set ambi changes GL_AMBI"""
        self.lightModel.Set(ambient=(0.0, 0.5, 0.5, 1.0))
        ambi = GL.glGetFloatv(GL.GL_LIGHT_MODEL_AMBIENT)
        self.assertEqual(ambi[0], 0.0)
        self.assertEqual(round(ambi[1], 1), 0.5)
        self.assertEqual(round(ambi[2], 1), 0.5)
        self.assertEqual(round(ambi[3], 1), 1.0)

    def test_Setambi_state(self):
        """Set light changes light's state['ambi']"""
        self.lightModel.Set(ambient=(1, 0, 0, 0))
        state = self.lightModel.getState()
        ambi = state["ambient"]
        self.assertEqual(round(ambi[0], 1), 1.0)
        self.assertEqual(ambi[1], 0.0)
        self.assertEqual(ambi[2], 0.0)
        self.assertEqual(ambi[3], 0.0)

    def test_Setambi_bad_input(self):
        """ValueError raised on bad input to Set ambi"""
        self.assertRaises(ValueError, self.lightModel.Set, ambient=(1, 0))

    def test_Setambi_empty_input(self):
        """ValueError raised on empty input to Set ambi"""
        self.assertRaises(ValueError, self.lightModel.Set, ambient=())

    def test_Setambi_too_much_input(self):
        """ValueError raised on too_much input to Set ambi"""
        self.assertRaises(ValueError, self.lightModel.Set, ambient=(1, 0, 0, 1, 1))

    # end AMBI

    # LOCAL VIEWER
    def test_Set_localViewer_attr(self):
        """Set localViewer changes light localViewer attribute"""
        self.lightModel.Set(localViewer=True)
        localViewer = self.lightModel.localViewer
        self.assertEqual(localViewer, True)

    def test_Set_localViewer_attr(self):
        """Set localViewer changes light localViewer attribute"""
        self.lightModel.Set(localViewer=True)
        localViewer = self.lightModel.localViewer
        self.assertEqual(localViewer, True)

    def test_SetlocalViewer_GL(self):
        """Set local viewer changes GL_AMBI"""
        self.lightModel.Set(localViewer=True)
        localViewer = GL.glGetBooleanv(GL.GL_LIGHT_MODEL_LOCAL_VIEWER)
        self.assertEqual(localViewer, True)

    def test_SetlocalViewer_state(self):
        """Set light changes light's state['localViewer']"""
        self.lightModel.Set(localViewer=True)
        state = self.lightModel.getState()
        localViewer = state["localViewer"]
        self.assertEqual(round(localViewer, 1), True)

    def test_SetlocalViewer_bad_input(self):
        """AttributeError raised on bad input to Set localViewer"""
        self.assertRaises(AttributeError, self.lightModel.Set, localViewer="hdi")

    def test_SetlocalViewer_empty_input(self):
        """AttributeError raised on empty input to Set localViewer"""
        self.assertRaises(AttributeError, self.lightModel.Set, localViewer=" ")

    # END LOCAL VIEWER

    # TWO SIDE

    def test_Set_twoSide_attr(self):
        """Set twoSide changes light twoSide attribute"""
        self.lightModel.Set(twoSide=True)
        twoSide = self.lightModel.twoSide
        self.assertEqual(twoSide, True)

    def test_Set_twoSide_attr(self):
        """Set twoSide changes light twoSide attribute"""
        self.lightModel.Set(twoSide=True)
        twoSide = self.lightModel.twoSide
        self.assertEqual(twoSide, True)

    def test_SettwoSide_GL(self):
        """Set two side changes GL_AMBI"""
        self.lightModel.Set(twoSide=True)
        twoSide = GL.glGetBooleanv(GL.GL_LIGHT_MODEL_TWO_SIDE)
        self.assertEqual(twoSide, True)

    def test_SettwoSide_state(self):
        """Set light changes light's state['twoSide']"""
        self.lightModel.Set(twoSide=True)
        state = self.lightModel.getState()
        twoSide = state["twoSide"]
        self.assertEqual(round(twoSide, 1), True)

    def test_SettwoSide_bad_input(self):
        """AttributeError raised on bad input to Set twoSide"""
        self.assertRaises(AttributeError, self.lightModel.Set, twoSide="hdi")

    def test_SettwoSide_empty_input(self):
        """AttributeError raised on empty input to Set twoSide"""
        self.assertRaises(AttributeError, self.lightModel.Set, twoSide=" ")


if __name__ == "__main__":
    unittest.main()
