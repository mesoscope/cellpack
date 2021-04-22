"""
do not add any dependancy on this file
"""
import unittest
from opengltk.OpenGL import GL
from DejaVu.Viewer import Viewer


class MaterialEditor_BaseTests(unittest.TestCase):
    def test_MaterialEditorDependancies(self):

        vi = Viewer()
        mated = vi.materialEditor
        mated.show()
        obj = vi.currentObject
        mated.setObject(obj, GL.GL_FRONT)
        mated.defineMaterial(obj.materials[GL.GL_FRONT].prop, GL.GL_FRONT)
        assert mated


if __name__ == "__main__":
    unittest.main()
