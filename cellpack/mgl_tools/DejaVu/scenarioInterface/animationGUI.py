import os
import Tkinter, Pmw

#from DejaVu.GeomChooser import GeomChooser
from mglutil.util.callback import CallbackFunction

from DejaVu.scenarioInterface.animations import FlyInObjectMAA, FlyOutObjectMAA,\
     FadeInObjectMAA, FadeOutObjectMAA, VisibleObjectMAA, ColorObjectMAA,\
     RotationMAAOptionsGUI, RotationMAA, RockMAA, SnapshotMAAGroup
# from DejaVu.scenarioInterface.animations import FocusMAA

from Scenario2.gui.Tk.clipboard import ClipboardGUI
from Scenario2.sequenceAnimator import SequenceAnimator
from Scenario2.gui.Tk.sequenceAnimator import SequenceAnimatorGUI
from Scenario2 import _clipboard, _MAATargets

from DejaVu.states import setRendering, getRendering, getOrientation
from DejaVu.scenarioInterface.animations import OrientationMAA, RenderingTransitionMAA

class MAAEditor:
    """
    Editor for an MAA

    the base class provides mainly the buttons at the bottom of the form

    the .edit(maa) method will save the maa in self.maa, show the form and
    configure it with the paramters gotten from the maa using maa.getValues().

    when OK or Preview are clicked the execute method has to configure
    self.maa and run the maa for Preview
    
    subclass will implement:

    populateForm() to add gui elements to self.dialog.interior()
    getValues() to return a dictionary of parameter names and values
    setValues() to take a dictionary of parameter names and values show them
                in the editor
    execute(name) to configure self.maa and run it for Preview
    """
    def __init__(self, master=None, title='Editor',
                 buttons=['OK', 'Preview', 'Cancel'],
                 defaultButton='OK'):
        """
        base class bur creating MAA editors

        editorObject <- MAAEditor( maa, master=None, title='Editor',
                 buttons=['OK','Preview', 'Cancel'],
                 defaultButton='OK')

        - maa is the MAA instance for which we want to see and modify params

        - master can be used to specify where to place the GUI.
        If master is None:
            if showOptionForm was called as callback from a Tk event,
            the dialog just below the button that was clicked
            else the dialogue will appear at position 100, 100

        - title is the title of the Editor window
        
        - buttons is a list of string specifying which buttons to create
        at the bottom of the dialog

        - defaultButton is a string that appears in buttons and will be
        set as the default button for the form
        """

        self.master = master
        self.maa = None # will be set in self.edit(maa)

        self.exitStatus = None # will be saet to the name of the button

        # save list of desired buttons
        assert len(buttons)>0
        self.buttons = buttons
        assert defaultButton in buttons
        self.defaultButtons = defaultButton

        # save the title
        assert isinstance(title, str)
        self.title = title
        
        # create the dialog
        self.dialog = self.createGUI()
        self.populateForm()


    def createGUI(self):
        """
        Create the form.
        This base class form is a Pmw dialog containing a set of Radiobuttons
        and a counter to select speed of animation(number of frames)
        """
        self.balloon = Pmw.Balloon(self.master)

        # create the Dialog
        dialog = Pmw.Dialog(
            self.master, buttons=self.buttons, defaultbutton='OK',
            title=self.title, command=self.execute)
        dialog.withdraw()
        # create a frame to hold group to force setting orient and rendering
        bframe = Tkinter.Frame(dialog.interior())

        ##
        ## create group to define if action sets orients
        self.actionGrp = grp = Pmw.Group(bframe, tag_text='Action sets')

        frame = grp.interior()
        
        self.forcew = w = Pmw.RadioSelect(
            frame, selectmode='multiple', orient='horizontal',
            buttontype='checkbutton')

        for text in ['Orientation', 'Rendering']:
            w.add(text)
    
        w.pack(side='left', anchor='w', fill='x', expand=1, padx=8, pady=8)

        grp.pack(side = 'left', fill='x', expand=1)

        self.balloon.bind(grp, "When an action is created the current orientation and rendering are saved.\nCheck these buttons to have the action set the orientation\nand/or Rendering on its first frame during playback")

        ##
        ## create a group of buttons to overwrite 
        self.recordGrp = grp = Pmw.Group(bframe, tag_text='Record:')

        frame = grp.interior()

        b1 = Tkinter.Button(frame, text='Orientation',
                            command=self.recordOrient)
        b1.pack(side='left', anchor='w', fill='x', expand=1, padx=8, pady=8)
        b2 = Tkinter.Button(frame, text='Rendering',
                            command=self.recordRendering)
        b2.pack(side='left', anchor='w', fill='x', expand=1, padx=8, pady=8)

        grp.pack(side = 'bottom', fill='x', expand=1)

        self.balloon.bind(grp, "Record current orientation/rendering for this action")
        bframe.pack( fill='x', expand=1)

        return dialog


    def recordOrient(self, event=None):
        self.maa.recordOrient()


    def recordRendering(self, event=None):
        self.maa.recordRendering()

        
    def edit(self, maa, event=None):
        self.maa = maa

        # configure the editor with current values
        self.setValues( **maa.getValues() )
        
        # activate and place the dialog just below the button that was clicked:
        if event:
            x = event.x_root
            y = event.y_root
            if y + self.master.winfo_height() > self.master.winfo_screenheight():
                y = self.master.winfo_screenheight() - self.master.winfo_height()
              #dialog.activate(globalMode = 'grab', geometry = '+%d+%d' % (x, y )) # does not work
            self.dialog.activate(geometry = '+%d+%d' % (x, y ))
        else:
            self.dialog.activate(geometry = '+%d+%d' % (100, 100 ))

        if self.exitStatus=='OK':
            return self.getValues()

        elif self.exitStatus in ('None', 'Cancel'):
            return None
       

    def _hide(self):
        self.dialog.deactivate()


    def execute(self, name):
        # called when buttons are clicked ot windows is closed
        self.exitStatus = name
        if name in ('None', 'Cancel', 'OK'):
            self._hide()


    ##
    ## the following methods should be subclassed
    ##
    def populateForm(self):
        """
        subclassses will place GUI items for various parameters in this method
        """
        return

    def getValues(self):
        """
        return a dictionary of parameterName:parameterValues
        """
        return {}

    def setValues(self, **kw):
        """
        take a dictionary of parameterName:parameterValues set the editor
        to these values
        """
        return


class MAAEditorWithSpeed(MAAEditor):
    """
    Sub class adding basic animation force orient/rendering and speed GUI
    """
    def __init__(self, master=None, title='Orientation Editor',
                 buttons=['OK', 'Preview', 'Cancel'],
                 defaultButton='OK', speedDict =None):
        """
        Provides a dialog form for setting Orientation actions parameters

           speedDict: dictionary of speed anmes and nbframes (constr only)
           
        The following parameters are handled by getValues and setValues:
           nbFrames: int
        """

        if speedDict is None:
            speedDict = {'slow': 50, 'medium': 30, 'fast': 10}
        self.speedDict = speedDict
        
        self.custom_speed_flag = False
        self.speed = 'medium'

        MAAEditor.__init__(self, master=master, title=title,
                           buttons=buttons, defaultButton=defaultButton)
        


    def populateForm(self):
        """
        added radiobuttons for speed dict and custom speed
        """

        # create group for speed
        parent = self.dialog.interior()

        grp = Pmw.Group(parent, tag_text='speed (in frames)')
        frame = grp.interior()
        self.speedw = sp = Pmw.RadioSelect(
            frame, selectmode='single', orient='horizontal',
            buttontype='radiobutton', command=self.setSpeed_cb)

        for text in ['slow', 'medium', 'fast', 'custom']:
            sp.add(text)
            
        sp.pack(side='left', anchor='w', fill='x', expand=1, padx=8, pady=8)

        for key, val in self.speedDict.items():
            self.balloon.bind(sp.button(key), "%d frames"%val)

        # add counter for overall custom speed
        self.speedcr = cr = Pmw.Counter(
            frame, entry_width=6, entryfield_value=100,
            entryfield_validate = {'validator':'integer', 'min':1 })
        
        self.balloon.bind(cr, "Enter overall number of frames")
        cr.pack(side = 'left', anchor = 'w', fill = 'x', expand = 1)
        grp.pack(side='top', fill='x', expand=1 )


    def setSpeed_cb(self, val=None):
        if val == "custom":
           self.custom_speed_flag = True
        else:
            self.custom_speed_flag = False
        self.setCounterState()


    def setCounterState(self):
        cr = self.speedcr
        entry = cr._counterEntry._entryFieldEntry
        up = cr._upArrowBtn
        down = cr._downArrowBtn
        if self.custom_speed_flag:
            # activate counter
            entry.configure(state='normal')
            down.bind('<Button-1>', cr._countDown)
            up.bind('<Button-1>', cr._countUp)
        else:
            # deactivate:
            entry.configure(state='disabled')
            down.unbind('<Button-1>')
            up.unbind('<Button-1>')


    def getValues(self):

        kw = {'forceOrient':False, 'forceRendering':False}
        sp = self.speedw.getvalue()
        if sp == "None":
            return kw
        if sp == "custom":
            nbFrames = int(self.speedcr.get())
        else:
            nbFrames = self.speedDict[sp]
        
        kw['nbFrames'] = nbFrames

        for val in self.forcew.getvalue():
            if val=='Orientation':
                kw['forceOrient'] = True
            elif val=='Rendering':
                kw['forceRendering'] = True

        return kw
    

    def setValues(self, **kw):
        """
        configure the option form with the values provided in **kw
        keys can be: 'nbFrames', 'easeInOut', 'direction'
        """
        forceList = []

        # if kw has kfpos use last frame in list as nbframes
        kfpos = kw.pop('kfpos', None)
        if kfpos:
            kw['nbFrames'] = kfpos[-1]-kfpos[0]

        for k,v in kw.items():
            if k == 'nbFrames':
                assert int(v)
                assert v>0
                # set speed radio button
                found = False
                for name, speed in self.speedDict.items():
                    if speed==v:
                        self.speedw.invoke(name)
                        found = True
                        break
                if not found:
                    self.speedw.invoke('custom')
                    self.speedcr.setvalue(v)
                    
            elif k == 'forceOrient' and v:
                forceList.append('Orientation')

            elif k == 'forceRendering' and v:
                forceList.append('Rendering')

            #else:
            #    print 'WARNING: unknown key:value',k,v

        self.forcew.setvalue(forceList)


    def execute(self, name):
        # called when buttons are clicked ot windows is closed
        self.exitStatus = name
        if name in ('None', 'Cancel', 'OK'):
            self._hide()
        values = self.getValues()
        self.maa.forceOrient = values['forceOrient']
        self.maa.forceRendering = values['forceRendering']
        



class SSp_MAAEditor(MAAEditorWithSpeed):
    """
    Editor providing speed, and sortPoly parameters
    """

    def populateForm(self):
        """
        add radio buttons for direction and easeInOut
        """
        MAAEditorWithSpeed.populateForm(self)

        parent = self.dialog.interior()

        grp = Pmw.Group(parent, tag_text='Zsort Polygons')
        frame = grp.interior()

        self.sortPolyw = w = Pmw.RadioSelect(
            frame, selectmode='single', orient='horizontal',
            buttontype='radiobutton')

        for text in ['Never', 'Once', 'Always']:
            w.add(text)

        w.pack(side='left', anchor='w', fill='x', expand=1, padx=8, pady=8)
        grp.pack(side = 'top', fill='x', expand=1)
        self.balloon.bind(w, "Select when to Z-sort polygons for proper trancparency")


    def getValues(self):
        """
        return a dictionary of parameterName:parameterValues
        """
        values = MAAEditorWithSpeed.getValues(self)
        values.update({'sortPoly': self.sortPolyw.getvalue()})
        return values


    def setValues(self, **kw):
        """
        take a dictionary of parameterName:parameterValues set the editor
        to these values
        """
        MAAEditorWithSpeed.setValues(self, **kw)
        self.sortPolyw.setvalue(kw['sortPoly'])



class OrientationMAAEditor(MAAEditorWithSpeed):

    def __init__(self, master=None, title='Orientation Editor',
                 buttons=['OK', 'Preview', 'Cancel'],
                 defaultButton='OK'):
        """
        Provides a dialog form for setting Orientation actions parameters

        parameters:
           keyframes: [0, a,b,c]
        """
        MAAEditorWithSpeed.__init__( self, master=master, title=title,
                          buttons=buttons, defaultButton=defaultButton)
        

    def populateForm(self):
        """
        add entryfield for 3 integers to specify 3 intervals
        """
        MAAEditorWithSpeed.populateForm(self)

        # add 3 custom intervals entry form
        
        parent = self.dialog.interior()
        grp = Pmw.Group(parent, tag_text='Custom intervals')
        frame = grp.interior()

        self._3intw = Pmw.EntryField(
            frame, labelpos = 'w', value = '10 20 30',
            label_text = 'nb frames for zoom out, rotate, zoom in:',
            validate = self.custom_validate)

        self._3intw.pack(side='top')
        self.balloon.bind(self._3intw, "Enter 3 space-separated integers\ndefining the zoom out, rotate, and zoom in intervals\ne.g. 10 20 30 means zoom out for 10 frames, rotate for 10 and zoom in for 10")

        grp.pack(side = 'top', fill='x', expand=1 )


    def custom_validate(self, text):
        words = text.split()
        if len(words)!=3:
            return -1
        a,b,c = map(int, words)
        if a>0 and b > a and c>b:
            return 1
        else:
            return -1


    def setSpeed_cb(self, val=None):
        # set self._3intw based on the selected speed
        
        val = MAAEditorWithSpeed.getValues(self).get('nbFrames',None)
        if val:
            self._3intw.setentry("%d %d %d"%(val/3, 2*val/3, val))


    def getValues(self):
        """
        return a dictionary of parameterName:parameterValues
        """
        a,b,c = map(int, self._3intw.getvalue().split())
        kw = {'keyframes':[0,a,b,c],
              'forceOrient':False,
              'forceRendering':False}
        for val in self.forcew.getvalue():
            if val=='Orientation':
                kw['forceOrient'] = True
            elif val=='Rendering':
                kw['forceRendering'] = True

        return kw


    def setValues(self, **kw):
        """
        take a dictionary of parameterName:parameterValues set the editor
        to these values
        """
        zero, a, b, c = kw['keyframes']
        found = False
        for name, value in self.speedDict.items():
            if c==value:
                self.speedw.invoke(name)
                found = True
                break

        if not found:
            self.speedw.invoke('custom')
            self.speedcr.setvalue(value)
            
        return


    def execute(self, name):
        # configure the MAA with the values from the editor
        MAAEditorWithSpeed.execute(self, name)
        if name in ('OK', 'Preview'):
            self.maa.setKeyframePositions( self.getValues()['keyframes'] )
            if name == 'Preview':
                self.maa.run()


class SnapshotMAAGroupEditor(SSp_MAAEditor):
    
    def __init__(self, master=None, title='Snapshot Editor',
                 buttons=['OK', 'Preview', 'Cancel'],
                 defaultButton='OK'):
        """
        Provides a dialog form for setting Snapshot actions parameters

        parameters:
           keyframes: [kf1, kf2]
        """
        SSp_MAAEditor.__init__( self, master=master, title=title,
                          buttons=buttons, defaultButton=defaultButton)
        self.actionGrp._tag.configure(text='Interpolate')
        self.balloon.bind(self.actionGrp, "Check these buttons to interpolate orientation/renderinf during playback.")
        

    def getValues(self):
        """
        return a dictionary of parameterName:parameterValues
        """

        #print "snapshot getValues"
        kw =  SSp_MAAEditor.getValues(self)
        nbframes = kw.get('nbFrames',None)
        if nbframes is not None:
            kw.pop('nbFrames')
            kw['keyframes'] = [0, nbframes]
        orient = kw.get('forceOrient', None)
        if orient is not None:
            kw['forceOrient'] = False
            kw['interpolateOrient'] = orient
        rend = kw.get('forceRendering', None)
        if rend is not None:
            kw['forceRendering'] = False
            kw['interpolateRendering'] = rend
        return kw


    def setValues(self, **kw):
        """
        take a dictionary of parameterName:parameterValues set the editor
        to these values
        """
        k1, k2 = kw['keyframes']
        found = False
        for name, value in self.speedDict.items():
            if k2==value:
                self.speedw.invoke(name)
                found = True
                break

        if not found:
            self.speedw.invoke('custom')
            self.speedcr.setvalue(k2)

        forceList = []
        if kw.get('interpolateOrient'):
            forceList.append('Orientation')
        if kw.get('interpolateRendering'): 
            forceList.append('Rendering')
        self.forcew.setvalue(forceList)
        self.sortPolyw.setvalue(kw['sortPoly'])


    def execute(self, name):
        #print "snapshot execute"
        # configure the MAA with the values from the editor
        MAAEditorWithSpeed.execute(self, name)
        self.maa.sortPoly = sortPoly = self.sortPolyw.getvalue()
        self.maa.renderMaa.sortPoly = sortPoly
        values = self.getValues()
        if values.has_key('interpolateRendering'):
            self.maa.interpolateRendering = values['interpolateRendering']
        if values.has_key('interpolateOrient'):
            self.maa.interpolateOrient = values['interpolateOrient']
        if name in ('OK', 'Preview'):
            self.maa.setKeyframePositions( self.getValues()['keyframes'] )
            if name == 'Preview':
                self.maa.run()


class SE_MAAEditor(MAAEditorWithSpeed):
    """
    Editor providing speed and easeInOut parameters
    """
 
    def populateForm(self):
        """
        add radio buttons for direction and easeInOut
        """
        MAAEditorWithSpeed.populateForm(self)

        parent = self.dialog.interior()
        grp = Pmw.Group(parent, tag_text='Ease In/Out')
        frame = grp.interior()
        
        self.easew = w = Pmw.RadioSelect(
            frame, selectmode='single', orient='horizontal',
            buttontype='radiobutton')

        for text in ['none', 'ease in', 'ease out', 'ease in and out']:
            w.add(text)

        w.pack(side='left', anchor='w', fill='x', expand=1, padx=8, pady=8)
 
        self.balloon.bind(w, "Ease in will slow down the start of the action,\n ease out will slow down then end of the action")

        grp.pack(side = 'top', fill='x', expand=1)


    def getValues(self):
        """
        return a dictionary of parameterName:parameterValues
        """
        values = MAAEditorWithSpeed.getValues(self)
        nbFrames = values.pop('nbFrames')
        values.update( {'kfpos': [0,nbFrames],
                        'easeInOut': self.easew.getvalue()} )
        return values
    

    def setValues(self, **kw):
        """
        take a dictionary of p <arameterName:parameterValues set the editor
        to these values
        """
        MAAEditorWithSpeed.setValues(self, **kw)
        self.easew.setvalue(kw['easeInOut'])


    def execute(self, name):
        # configure the MAA with the values from the editor
        MAAEditorWithSpeed.execute(self, name)
        if name in ('OK', 'Preview'):
            self.maa.configure( **self.getValues() )
            if name == 'Preview':
                self.maa.run()


class SED_MAAEditor(SE_MAAEditor):
    """
    Editor providing speed, easeInOut and direction parameters
    """
    def __init__(self, master=None, title='Editor',
                 directions=['left', 'right'],
                 buttons=['OK', 'Preview', 'Cancel'],
                 defaultButton='OK', speedDict=None):
        """
        Provides a dialog form for setting Fly actions parameters

        parameters:
           kfpos: [a,b] 2 integer key frame positions
           direction: can be 'left', 'right', 'top', or 'bottom'
           easeInOut: can be 'none', 'ease in', 'ease out', 'ease in and out'
           speedDict: dictionary of speed anmes and nbframes (constr. only)
        """
        self.directions = directions
        SE_MAAEditor.__init__(
            self, master=master, title=title, buttons=buttons,
            defaultButton=defaultButton, speedDict=speedDict)


    def populateForm(self):
        """
        add radio buttons for direction and easeInOut
        """
        SE_MAAEditor.populateForm(self)

        parent = self.dialog.interior()
        grp = Pmw.Group(parent, tag_text='Direction')
        frame = grp.interior()

        self.directionw = w = Pmw.RadioSelect(
            frame, selectmode='single', orient='horizontal',
            buttontype='radiobutton')

        for text in self.directions:
            w.add(text)

        w.pack(side='left', anchor='w', fill='x', expand=1, padx=8, pady=8)
        grp.pack(side = 'top', fill='x', expand=1)
        self.balloon.bind(w, "Select the action direction")


    def getValues(self):
        """
        return a dictionary of parameterName:parameterValues
        """
        values = MAAEditorWithSpeed.getValues(self)
        nbFrames = values.pop('nbFrames')
        values.update( {'kfpos': [0,nbFrames],
                        'direction': self.directionw.getvalue(),
                        'easeInOut': self.easew.getvalue()} )
        return values


    def setValues(self, **kw):
        """
        take a dictionary of parameterName:parameterValues set the editor
        to these values
        """
        MAAEditorWithSpeed.setValues(self, **kw)
        self.directionw.setvalue(kw['direction'])
        self.easew.setvalue(kw['easeInOut'])



class SESp_MAAEditor(SE_MAAEditor):
    """
    Editor providing speed, easeInOut and sortPoly parameters
    """

    def populateForm(self):
        """
        add radio buttons for direction and easeInOut
        """
        SE_MAAEditor.populateForm(self)

        parent = self.dialog.interior()

        grp = Pmw.Group(parent, tag_text='Zsort Polygons')
        frame = grp.interior()

        self.sortPolyw = w = Pmw.RadioSelect(
            frame, selectmode='single', orient='horizontal',
            buttontype='radiobutton')

        for text in ['Never', 'Once', 'Always']:
            w.add(text)

        w.pack(side='left', anchor='w', fill='x', expand=1, padx=8, pady=8)
        grp.pack(side = 'top', fill='x', expand=1)
        self.balloon.bind(w, "Select when to Z-sort polygons for proper trancparency")


    def getValues(self):
        """
        return a dictionary of parameterName:parameterValues
        """
        values = MAAEditorWithSpeed.getValues(self)
        nbFrames = values.pop('nbFrames')
        values.update({'kfpos': [0,nbFrames],
                       'sortPoly': self.sortPolyw.getvalue(),
                       'easeInOut': self.easew.getvalue()} )
        return values


    def setValues(self, **kw):
        """
        take a dictionary of parameterName:parameterValues set the editor
        to these values
        """
        MAAEditorWithSpeed.setValues(self, **kw)
        self.sortPolyw.setvalue(kw['sortPoly'])
        self.easew.setvalue(kw['easeInOut'])


from mglutil.gui.BasicWidgets.Tk.colorWidgets import ColorChooser

class SECol_MAAEditor(SE_MAAEditor):
    
    """
    Editor providing speed, easeInOut parameters and ColorChooser widget
    """
    def __init__(self, master=None, title='Colors Editor',
                 buttons=['OK', 'Preview', 'Cancel'],
                 defaultButton='OK', speedDict =None, choosecolor = False):
        
        self.choosecolor = choosecolor
        self.color = None
        SE_MAAEditor.__init__(
            self, master=master, title=title, buttons=buttons,
            defaultButton=defaultButton, speedDict=speedDict)


    def populateForm(self):
        """
        add radio buttons for direction and easeInOut
        """
        SE_MAAEditor.populateForm(self)
        if self.choosecolor:
            parent = self.dialog.interior()
            self.colorChooser = ColorChooser(master = parent,
                                             commands = self.setColor_cb)
            self.colorChooser.pack(side = "top")


    def setColor_cb(self, colors):
        self.color = colors


    def getValues(self):
        """
        return a dictionary of parameterName:parameterValues
        """
        values = MAAEditorWithSpeed.getValues(self)
        nbFrames = values.pop('nbFrames')
        values.update( {'kfpos': [0,nbFrames],
                        'easeInOut': self.easew.getvalue()} )
        if self.choosecolor:
            if self.color:
                values['color'] = [self.color,]
        return values
    

class Rotation_MAAEditor(SED_MAAEditor):
    """
    Editor providing Rotation animation parameters
    """
    def __init__(self, master=None, title='Rotation Editor',
                 directions=['counter clockwise', 'clockwise'],
                 buttons=['OK', 'Preview', 'Cancel'],
                 defaultButton='OK', speedDict=None):
        """
        Provides a dialog form for setting Rotation action parameters

        parameters:
           nbFrames: number of keyframes
           angle: rotation angular amplitude in degrees
           vector: rotation axis
           direction: can be 'counter clockwise' or 'clockwise'
           easeInOut: can be 'none', 'ease in', 'ease out', 'ease in and out'
        """

        SED_MAAEditor.__init__(
            self, master=master, title=title, buttons=buttons,
            defaultButton=defaultButton, directions=directions,
            speedDict=speedDict)


    def populateForm(self):
        """
        add counter for angle and GUI for rotation vector
        """
        SED_MAAEditor.populateForm(self)

        parent = self.dialog.interior()

        # Create and pack the dropdown ComboBox for axis
        grp = Pmw.Group(parent, tag_text='rotation axis')
        axes = self.axes = ('X', 'Y', 'Z', 'XY', 'XZ', 'YZ', 'XYZ')
        self.axisDropdownw = w = Pmw.ComboBox(
            grp.interior(), scrolledlist_items=axes)
        w.pack(side='left', anchor='n', fill='x', expand=1, padx=8, pady=8)
        w.selectitem('Y')
        grp.pack(side = 'top', fill='x', expand=1)

        grp = Pmw.Group(parent, tag_text='rotation angle')
        self.anglew = w = Pmw.Counter(
            grp.interior(), entry_width=6, entryfield_value = 360,
            entryfield_validate = {'validator':'integer', 'min' : 1 } )

        w.pack(side='left', anchor='w', fill='x', expand=1, padx=8, pady=8)
        grp.pack(side = 'top', fill='x', expand=1)

        #self.balloon.bind(w, "Select when to Z-sort polygons for proper trancparency")

    def getVector(self):
        """
        return (x, y, z) vector according to axis widget value
        """
        
        axis = self.axisDropdownw.getvalue()[0]
        if axis=='X':
            vector = (1., 0., 0.)
        elif axis=='Y':
            vector = (0., 1., 0.)
        elif axis=='Z':
            vector = (0., 0., 1.)
        elif axis=='XY':
            vector = (1., 1., 0.)
        elif axis=='XZ':
            vector = (1., 0., 1.)
        elif axis=='YZ':
            vector = (0., 1., 1.)
        elif axis=='XYZ':
            vector = (1., 1., 1.)
        return vector


    def getAxis(self, vector):
        """
        return axis anme based in (x, y, z) vector
        """
        x,y,z = vector
        if x==1 and y==0 and z==0:
            return 'X'
        elif x==0 and y==1 and z==0:
            return 'Y'
        elif x==0 and y==0 and z==1:
            return 'Z'
        elif x==1 and y==1 and z==0:
            return 'XY'
        elif x==0 and y==1 and z==1:
            return 'YZ'
        elif x==1 and y==0 and z==1:
            return 'XZ'
        elif x==1 and y==1 and z==1:
            return 'XYZ'
        else:
            return 'custom'
        
    
    def getValues(self):
        """
        return a dictionary of parameterName:parameterValues
        """
        values = SED_MAAEditor.getValues(self)
        nbFrames = values.pop('kfpos')[-1]
        values.update({'nbFrames':nbFrames,
                       'angle': int(self.anglew.get()),
                       'vector': self.getVector(),
                       } )
        return values


    def setValues(self, **kw):
        """
        take a dictionary of parameterName:parameterValues set the editor
        to these values
        """
        SED_MAAEditor.setValues(self, **kw)
        self.axisDropdownw.selectitem(self.getAxis(kw['vector']))
        self.anglew.setvalue(kw['angle'])



class Rock_MAAEditor(Rotation_MAAEditor):
    """
    Editor providing Rock animation paramters
    """
    def __init__(self, master=None, title='Rock Editor',
                 directions=['counter clockwise', 'clockwise'],
                 buttons=['OK', 'Preview', 'Cancel'],
                 defaultButton='OK'):
        """
        Provides a dialog form for setting Rotation action parameters

        parameters:
           nbFrames: number of keyframes
           angle: rotation angular amplitude in degrees
           vector: rotation axis
           direction: can be 'counter clockwise' or 'clockwise'
           easeInOut: can be 'none', 'ease in', 'ease out', 'ease in and out'
        """

        Rotation_MAAEditor.__init__(
            self, master=master, title=title, buttons=buttons,
            defaultButton=defaultButton, directions=directions,
            speedDict={'slow': 60, 'medium': 30, 'fast': 10})



## def expandGeoms(geoms):
##     newgeoms = []
##     for g in geoms:
##         for child in g.AllObjects():
##             if len(child.getVertices())>0 and child.visible:
##                 newgoms.append( child )
##     return newgeoms


    
class orientationGUI:
    """
    Scrolled frame holding orientations (snapshots)
    """
    def __init__(self, viewer, viewerName, master=None):
        """
        orientationGUI constructor

        orientationGUIObject <- orientationGUI(viewer, viewerName, master=None)
        """
        self.viewer = viewer
        self.viewerName = viewerName
        #self.orientations = {}  
        self.snapshots = {}
        self.nbOrients = 0
        self.master = master
	self.row = 0
	self.col = 0
        self.speedDict = {'slow': 50, 'medium': 30, 'fast': 10}

        #self.editor = OrientationMAAEditor(master=master)
        self.editor = SnapshotMAAGroupEditor(master=master)
        self.modifyOrient = Tkinter.IntVar()
        self.modifyOrient.set(1)
        self.modifyRendering = Tkinter.IntVar()
        self.modifyRendering.set(1)
        self.forceRendering = Tkinter.BooleanVar()
        self.forceRendering.set(False)
        self.createGUI()
        self._animNB = None # will become a reference to the AnimationNotebook instance


    def createGUI(self):
        """
        Create a ScrolledFrame to old orientations entries
        """
        if self.master is None:
            self.master = master = Tkinter.Toplevel()
            self.ownsMaster = True
        else:
            self.ownsMaster = False

        self.balloon = Pmw.Balloon(self.master)

        # create a group with a button to record an orientation
        w = self.orientsContainer = Pmw.Group(
            self.master, tag_pyclass = Tkinter.Button,
            tag_text='Record Snapshot')
        w.configure(tag_command = self.recordOrient)

        # create a scrolled frame to display recorded orientation
        
        w1 = self.MAAContainer = Pmw.ScrolledFrame(
            w.interior(), usehullsize=0, hull_width=40, hull_height=200,
            vscrollmode='dynamic', hscrollmode='none')

        w1.pack(padx=5, pady=3, fill='both', expand=1)
       

        w.pack(fill='both', expand=1, padx = 6, pady = 6)

        # bind right button to show option form editor
        button = w.component('tag')
        button.bind('<Button-3>', self.startEditor)


    def startEditor(self, event=None):
        objString = self.viewerName+'.rootObject'
        #orient = getOrientation(object)
        orient = None
        rendering = getRendering(self.viewer, checkAnimatable=True)
        orientMaa = OrientationMAA(self.viewer.rootObject, 'temp', orient, rendering,
                                   objectFromString=objString)
        kfpos = [orientMaa.firstPosition, orientMaa.lastPosition]
        renderMaa = RenderingTransitionMAA(self.viewer, rendering,
                                           kfpos=kfpos, startFlag = "with previous")
        maa = SnapshotMAAGroup(orientMaa, renderMaa,"snapshot%d"% (self.nbOrients+1, ) )

        values = self.editor.edit(maa)
        if values:
            self.nbOrients += 1
            self.saveMAA(maa)
            

    def recordOrient(self, event=None):
        """
        build default orientation transition (left clicks)
        """
        self.nbOrients += 1
        object = self.viewer.rootObject
        #orient = getOrientation(object)
        orient = None
        rendering = getRendering(self.viewer, checkAnimatable=True)
        #maa1 = OrientationMAA(object, 'orient%d'% self.nbOrients, orient, rendering,
        #                     objectFromString=self.viewerName+'.rootObject')
        orientMaa = OrientationMAA(object, 'temp', orient, rendering,
                             objectFromString=self.viewerName+'.rootObject')
        kfpos = [orientMaa.firstPosition, orientMaa.lastPosition]
        renderMaa = RenderingTransitionMAA(self.viewer, rendering,
                                           kfpos=kfpos, startFlag = "with previous")
        maa = SnapshotMAAGroup(orientMaa, renderMaa,"snapshot%d"%self.nbOrients )
        self.saveMAA(maa)


    def saveMAA(self, maagroup):
        """
        adds MAA to the list and adds a button for it in the panel
        """

        assert isinstance(maagroup, SnapshotMAAGroup)
        if not maagroup.name:
            maagroup.name = "snapshot%d"%self.nbOrients
        snName = self.checkName(maagroup.name)
        if maagroup.name != snName: maagroup.name = snName
        
        orientMaa = maagroup.orientMaa
        renderMaa = maagroup.renderMaa
        renderMaa._animNB = self._animNB
        orientMaa.name = snName+"orient"
        renderMaa.name = snName+"rendering"
        self.snapshots[snName] = maagroup
        self.addOrientButton(maagroup)
        
    def checkName(self, name):
        """check if the name exists in the self.snapshots or in the sequence player.
        If exists - create unique name"""
        allnames = self.snapshots.keys()
        if self._animNB:
            for maa, pos in  self._animNB().seqAnim.maas:
                if maa.name not in allnames:
                    allnames.append(maa.name)
        if name in allnames:
            i = 1
            while(name in allnames):
                name = name+"_%d"%i
                i = i+1
        return name
        
        
    def addOrientButton(self, maa):
        master = self.MAAContainer.interior()
        self.viewer.master.lift()
        self.viewer.master.master.lift()
        self.viewer.OneRedraw()
        photo = self.viewer.GUI.getButtonIcon()

        b = Tkinter.Button(master=master ,compound='left', image=photo,
                           command=CallbackFunction(self.runMaa, maa))
        b.photo = photo
        b.name = maa.name
        b.grid(row = self.row, column = self.col, sticky = 'nsew')
        b.bind('<Button-3>', CallbackFunction( self.showOrientMenu_cb, maa))

        self.balloon.bind(b, maa.name)
        if self.col == 7:
	    self.col = 0
	    self.row = self.row + 1
	else:
	    self.col = self.col + 1

    def runMaa(self, maagroup):
        orient = maagroup.orientMaa
        render = maagroup.renderMaa
        #print "run maa:", maagroup.name, 'force rendering:',  orient.forceRendering       
        if orient.forceRendering:
            setRendering(orient.viewer, orient.rendering)
            orient.run()
        else:
            #modify (morph) rendering
            #render.setValuesAt(0)
            #render.run()
            #orient.run()
            maagroup.run()


    def editMaa_cb(self, maagroup):
        values = self.editor.edit(maagroup)
        #check if the maa has been added to the sequence animator:
        animNB = self._animNB()
        for i , _maa in enumerate(animNB.seqAnim.maas):
            if _maa[0] == maagroup:
                position = _maa[1]
                animNB.seqAnimGUI.update(i, position)
                return


    def setForceRendering(self, orient, event = None):
        #print "setForceRendering", self.forceRendering.get()
        orient.forceRendering = self.forceRendering.get()

 
    def showOrientMenu_cb(self, maagroup, event=None):
        """
        Create button menu and post it
        """
        # create the button menu
        orient = maagroup.orientMaa
        render = maagroup.renderMaa
        #orient, render = maagroup.maas
        menu = Tkinter.Menu(self.master, title = orient.name)
        
        #cb = CallbackFunction(self.setForceRendering, orient)

        #self.forceRendering.set(orient.forceRendering)
        #menu.add_checkbutton(label="Force Rendering",
        #                     var = self.forceRendering,
        #                     command=cb)
        
        from Scenario2 import addTargetsToMenu
        #addTargetsToMenu(menu, [orient, render])
        #addTargetsToMenu(menu, maagroup)
        cb = CallbackFunction(self.addAsTransition_cb, maagroup)
        #menu.add_command(label="Add to animation as transition", command = cb)
        menu.add_command(label="Add to animation", command = cb)
        #cb = CallbackFunction(self.addAsKeyframe_cb, maagroup)
        #menu.add_command(label="Add to animation as keyframe", command = cb)
        
        cb = CallbackFunction(self.editMaa_cb, maagroup)
        menu.add_command(label="Edit", command = cb)
        
        cb = CallbackFunction(self.renameOrient_cb, maagroup)
        menu.add_command(label="Rename", command = cb)

        cb = CallbackFunction(self.removeOrient_cb, maagroup)
        menu.add_command(label="Remove", command = cb)

        menu.add_command(label="Dismiss")
        menu.post(event.x_root, event.y_root)


    def addToClipboard(self, orient, render=None):
        """
        adds this orientation animation to the clipboard
        """
        _clipboard.addMaa(orient)
        if render is not None:
            _clipboard.addMaa(render)

    def addAsTransition_cb(self, maagroup):
        kf1, kf2 = maagroup.kfpos
        #if kf2 - kf1 <=1:
        #    values = self.editor.edit(maagroup)
        self._animNB().seqAnim.addMAA(maagroup)

    def addAsKeyframe_cb(self, maagroup):
        maagroup.setKeyframePositions([0, 1])
        self._animNB().seqAnim.addMAA(maagroup)
        


    def renameOrient_cb(self, maagroup):
        name = maagroup.name
        container = self.MAAContainer.interior()
        from tkSimpleDialog import askstring
        newname = askstring("Rename %s"%name, "Enter new name:", initialvalue = name,
                            parent = container)
        if newname != None and newname != name:
            if self.snapshots.has_key(newname):
                from tkMessageBox import showwarning
                showwarning("Warning", "Name %s already exists"%newname,parent = self.master)
                return
            #find cooresponding button, rename it and update the bindings:
            self.snapshots.pop(name)
            self.snapshots[newname] = maagroup
            maagroup.name = newname
            orient = maagroup.orientMaa
            render = maagroup.renderMaa
            #orient, render = maagroup.maas
            orient.name = newname+"orient"
            render.name = newname+"rendering"
            for b in container.grid_slaves():
                if hasattr(b, "name"):
                    if b.name == name:
                       b.name = newname
                       self.balloon.bind(b, newname)
                       break 


    def removeOrient_cb(self, maagroup):
        orientB = None
        name = maagroup.name
        frame = self.MAAContainer.interior()
        for b in frame.grid_slaves():
            if hasattr(b, "name"):
                if b.name == name:
                    orientB = b
                    break
        if orientB:
            orientB.destroy()
            # regrid the buttons to fill the space freed by the removed button :
            buttons = frame.grid_slaves() # the widgets in this list
            # seem to be stored in "last created, first in the list" order
            buttons.reverse()
            col = 0
            row = 0
            for i, b in enumerate(buttons):
                b.grid(row=row, column= col, sticky='nsew')
                if col == 7:
                   col = 0
                   row = row + 1
                else:
                   col = col + 1
            self.col = col
            self.row = row
            # remove the orient entry from self.orientations
            self.snapshots.pop(name)


    def getSavedMaas(self):
        maas = []
        for b in reversed(self.MAAContainer.interior().grid_slaves()):
            if hasattr(b, "name"):
                name = b.name
                if self.snapshots.has_key(name):
                    maas.append(self.snapshots[name])
        return maas



