from DejaVu import Viewer
from DejaVu.Spheres import Spheres
import numpy


def test_views001():
    """
    Test that:
       we can create a view,
       add it to a director,
       move the scene toa  new place,
       save the new place as a second view
       use the director to go back to the initial view
       add the second view to the director at position 40
       move to a new position
       play the animation going from the current position to the initial view
       and the to the second view
    """
    vi = Viewer()
    sph = Spheres(
        "sph",
        centers=[(0, 0, 0), (10, 0, 0), (0, 10, 0), (0, 0, 10)],
        materials=[(1, 1, 1), (1, 0, 0), (0, 1, 0), (0, 0, 1)],
        inheritMaterial=False,
    )
    vi.AddObject(sph)
    root = vi.rootObject
    cam = vi.currentCamera
    mat1g = root.GetMatrix()
    mat1c = cam.GetMatrix()

    # create view with identity transformation
    from DejaVu.scenarioInterface.animations import OrientationMAA
    from DejaVu.states import getRendering, getOrientation

    # orient = getOrientation(root)
    orient = None
    rendering = getRendering(vi)
    maa1 = OrientationMAA(root, "temp", orient, rendering)

    # create a director
    ##     from Scenario2.director import Director
    ##     d = Director()
    from Scenario2.director import MAADirector

    d = MAADirector()
    # add the maa1 to the director
    # val = d.addMultipleActorsActionsAt(maa1)
    val = d.addMAAat(maa1, 0)
    assert val == True

    # check the animation
    names, posLabel, posStr, actStr, fullStr = maa1.getStringRepr()
    redrawActor = maa1.actors[0]

    ## check that we have this:

    ##                          1         2         3
    ##                0         0         0         0
    ##                |    :    |    :    |    :    |
    ##  root.rotation x-----------------------------x
    ## root.translati x-----------------------------x
    ##     root.scale x-----------------------------x
    ##     root.pivot x-----------------------------x
    ## Camera0.fieldO x---------x---------x---------x
    ## Camera0.lookFr x-----------------------------x
    ## redraw_******* No Keyframes

    ##     testStr = "                         1         2         3\n               0         0         0         0\n               |    :    |    :    |    :    |\n root.rotation x-----------------------------x\nroot.translati x-----------------------------x\n    root.scale x-----------------------------x\n    root.pivot x-----------------------------x\nCamera0.fieldO x---------x---------x---------x\nCamera0.lookFr x-----------------------------x\n%014s No Keyframes\n" % redrawActor.name[:14]

    ##     assert fullStr == testStr

    # translate the scene to (10, 0, 0)
    root.SetTranslation(numpy.array((10, 0, 0)))
    vi.OneRedraw()

    # save this position as our second view
    # orient = getOrientation(root)
    orient = None
    rendering = getRendering(vi)
    maa2 = OrientationMAA(root, "temp2", orient, rendering)
    # maa2 = OrientationMAA(root, "Viewer", 'view1')
    mat2g = root.GetMatrix()
    mat2c = cam.GetMatrix()
    # play the director. We shoudl move from current position to identity tranformation
    # d.actors[1].printValuesWhenSetting = True
    # d.run()
    d.play()
    # maa1.run()
    # check that transformation matrices are correctly returned to identity
    mat3g = root.GetMatrix()
    mat3c = cam.GetMatrix()
    assert numpy.sum(mat1g - mat3g) == 0.0
    assert numpy.sum(mat1c - mat3c) == 0.0

    # add second view to director at 40
    # val = d.addMultipleActorsActionsAt(maa2, 40)
    val = d.addMAAat(maa2, 40)
    assert val == True

    # move to other position
    root.SetTranslation(numpy.array((-10, 0, 0)))
    vi.OneRedraw()

    # play back motion from this position to origin and then to view1
    # d.run()
    d.play()
    mat4g = root.GetMatrix()
    mat4c = cam.GetMatrix()
    assert numpy.sum(mat4g - mat2g) == 0.0
    assert numpy.sum(mat4c - mat2c) == 0.0

    maa3 = None
    viewer = vi
    showwarning = 0
    # check if we can reproduce MAA from it's source
    maasrc = maa2.getSourceCode("maa3")
    exec(maasrc)
    assert maa3 != None
    # replace the original MAA (maa2) with the one created from source
    d.removeMAA(maa2, 40)
    d.addMAAat(maa3, 40)

    # move to other position and play :
    root.SetTranslation(numpy.array((-10, 0, 0)))
    vi.OneRedraw()
    d.play()
    # check the values
    mat5g = root.GetMatrix()
    mat5c = cam.GetMatrix()
    assert numpy.sum(mat5g - mat2g) == 0.0
    assert numpy.sum(mat5c - mat2c) == 0.0
    vi.Exit()
