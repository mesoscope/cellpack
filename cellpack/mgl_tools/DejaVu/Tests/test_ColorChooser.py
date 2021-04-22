## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#
#
# $Id: test_ColorChooser.py,v 1.4 2007/12/28 22:50:04 vareille Exp $
#
#
import Tkinter
import numpy
import numpy.oldnumeric as Numeric
import math
import unittest
from copy import deepcopy

from DejaVu.ColorChooser import ColorChooser
from DejaVu.colorTool import ToRGB,ToHSV

def MyCallback(col):
	print 'col', col

class ColorChooser_BaseTests(unittest.TestCase):

    def test_colorchooser_visible(self):
        """tests color chooser is visible
        """
        root = Tkinter.Tk()
        cc = ColorChooser(root)    
        cc.AddCallback(MyCallback)
        root.wait_visibility(cc.hsWheel.canvas)
        self.assertEqual(cc.hsWheel.canvas.master.winfo_ismapped(),1)
        self.assertEqual(root.winfo_ismapped(),True)
        cc.RemoveCallback(MyCallback)
        root.destroy()

    def test_color_chooser_save(self):
        """tests colorchooser,save button
        """
        root = Tkinter.Tk()
        cc = ColorChooser(root)
        cc.value.Set(0.75)
        cc.save.invoke()
        root.wait_visibility(cc.hsWheel.canvas)
        lColor = cc.hsWheel.Get()
        self.assertEqual(cc.savedHsvColor[0],lColor[0])
        self.assertEqual(cc.savedHsvColor[1],lColor[1])
        self.assertEqual(cc.savedHsvColor[2],lColor[2])
        self.assertEqual(cc.value.val,0.75)
        root.destroy()
         
    def test_color_chooser_restore(self):
        """tests color chooser restore button(when invoked displays stored
        value as current one)
        """
        root = Tkinter.Tk()
        cc = ColorChooser(root)
        #get color before setting value
        old_color = deepcopy(cc.hsWheel.Get())
        #get cursor coords before setting value
        old_cursorx = cc.hsWheel.cursorX
        old_cursory = cc.hsWheel.cursorY
        #set value to 0.75
        cc.value.Set(0.75)
        #invoke restore button
        cc.restore.invoke()
        #get color after setting value & invoking restore button
        new_color = cc.hsWheel.Get()
        #get cursor coords after setting value & invoking restore button
        new_cursorx = cc.hsWheel.cursorX
        new_cursory = cc.hsWheel.cursorY
        root.wait_visibility(cc.hsWheel.canvas)
        self.assertEqual(cc.value.val,1.0)
        #colors,cursor,coords before,after setting values  
        #invoking restore button shows previous values
        self.assertTrue(numpy.alltrue(old_color == new_color))
        self.assertEqual(old_cursorx == new_cursorx,True)
        self.assertEqual(old_cursory == new_cursory,True)
        root.destroy()
         
    def test_color_chooser_swap(self):
        """tests color chooser ,swap button(when invoked shows stored
        value,invoked again shows current one)
        """
        root = Tkinter.Tk()
        cc = ColorChooser(root)
        cc.value.Set(0.75)
        #get color before invoking swap button
        old_color = cc.hsWheel.Get()
        #get cursor coords before invoking swap button
        old_cursorx = cc.hsWheel.cursorX
        old_cursory = cc.hsWheel.cursorY
        #invoke swap button
        cc.swap.invoke()
        self.assertEqual(cc.value.val,1.0)
        #invoke swap button
        cc.swap.invoke()
        #get color after setting value & invoking swap button
        new_color = cc.hsWheel.Get()
        #get cursor coords after setting value & invoking swap button
        new_cursorx = cc.hsWheel.cursorX
        new_cursory = cc.hsWheel.cursorY
        root.wait_visibility(cc.hsWheel.canvas)
        self.assertEqual(cc.value.val,0.75)
        #colors,cursor,coords before,after setting values
        #invoking swap button twice shows first value
        self.assertTrue(numpy.alltrue(old_color == new_color))
        self.assertEqual(old_cursorx == new_cursorx,True)
        self.assertEqual(old_cursory == new_cursory,True)
        root.destroy()
         
    def test_colorchooser_cursor(self):
        """tests color chooser, moving cursor
        """
        root = Tkinter.Tk()
        cc = ColorChooser(root)
        old_x = cc.hsWheel.cursorX        
        old_y = cc.hsWheel.cursorY
        cc.hsWheel._MoveCursor(25,25)
        new_x = cc.hsWheel.cursorX
        new_y = cc.hsWheel.cursorY
        root.wait_visibility(cc.hsWheel.canvas)
        self.assertEqual(old_x != new_x,True)
        self.assertEqual(old_y != new_y,True)
        root.destroy()

    def test_color_chooser_current(self):
        """tests color chooser ,current:
        checks back ground color of current changes when value is changed
        """
        root = Tkinter.Tk()
        cc = ColorChooser(root)
        old_color = cc.currentColor.config()['background'][-1]
        cc.value.Set(0.75)
        new_color = cc.currentColor.config()['background'][-1]
        root.wait_visibility(cc.hsWheel.canvas)
        self.assertEqual(old_color != new_color,True)
        root.destroy()
         
    def test_color_chooser_saved (self):
        """tests color chooser ,saved:
        checks back ground color of saved changes when value is changed
        """
        root = Tkinter.Tk()
        cc = ColorChooser(root)
        old_color = cc.savedColor.config()['background'][-1]
        cc.value.Set(0.75)
        cc.save.invoke()
        new_color = cc.savedColor.config()['background'][-1]
        root.wait_visibility(cc.hsWheel.canvas)
        self.assertEqual(old_color != new_color,True)
        root.destroy()

    def test_colorchooser_color_1(self):
        """tests colorchooser ,color wheel colors
        """
        root = Tkinter.Tk()
        cc = ColorChooser(root)    
        old_color = cc.hsWheel.hsvColor
        cc.hsWheel._MoveCursor(100,50)
        new_color = cc.hsWheel.hsvColor
        root.wait_visibility(cc.hsWheel.canvas)
        #self.assertEqual(old_color,new_color)
        self.assertTrue(numpy.alltrue(old_color==new_color))
        cc.hsWheel.Set((1.0,0.0,0.0),mode = 'RGB')
        mycolor = ToRGB(cc.hsWheel.Get())
        mycol = []
        for i in range(0,len(mycolor)):
            mycol.append(round(mycolor[i]))
        self.assertEqual(mycol,[1.0, 0.0, 0.0, 1.0])
        root.destroy()

    def test_colorchooser_color_HSV(self):
        """tests colorchooser ,color wheel hsvcolors
        """
        root = Tkinter.Tk()
        cc = ColorChooser(root)
        cc.hsWheel.Set((1.0,0.0,0.0),mode = 'HSV')
        root.wait_visibility(cc.hsWheel.canvas)
        self.assertEqual(cc.hsWheel.hsvColor,[1.0, 0.0, 0.0, 1.0])
        self.assertEqual(cc.hsWheel.cursorX,50)
        self.assertEqual(cc.hsWheel.cursorY,50)
        root.destroy()


    def test_colorchooser_color_RGB(self):
        """tests colorchooser ,color wheel RGB colors
        """
        root = Tkinter.Tk()
        cc = ColorChooser(root)
        cc.hsWheel.Set((1.0,0.0,0.0),mode = 'RGB')
        root.wait_visibility(cc.hsWheel.canvas)
        self.assertEqual(cc.hsWheel.cursorX,100)
        self.assertEqual(cc.hsWheel.cursorY,50)
        self.assertEqual(cc.hsWheel.hsvColor[:3] != [1.0, 0.0, 0.0],True)
        root.destroy()
        
    def test_colorchooser_Wysiwyg(self):
        """tests colorchooser ,colorwheel setWysiwyg
        """
        root = Tkinter.Tk()
        cc = ColorChooser(root)
        cc.hsWheel.Set((1.0,0.0,0.0),mode = 'HSV')    
        #when On chooser colors are recomputed
        cc.hsWheel.setWysiwyg(1)
        root.wait_visibility(cc.hsWheel.canvas)
        self.assertEqual(cc.hsWheel.hsvColor == [1.0, 0.0, 0.0, 1.0],True)
        cc.hsWheel.setWysiwyg(0)
        self.assertEqual(cc.hsWheel.hsvColor[:3] != [1.0, 0.0, 0.0],True)
        root.destroy()        
    
    def test_colorchooser_value(self):
        """tests colorchooser,setting value
        """
        root = Tkinter.Tk()
        cc = ColorChooser(root)
        cc.Set([0.5,0.5,0.])
        self.assertEqual(cc.value.val,0.5)
        root.destroy()

    def test_color_add_remove_callback(self):
        """tests add,remove callback functions
        """
        root = Tkinter.Tk()
        cc= ColorChooser(root)
        cc.hsWheel.AddCallback(MyCallback)
        root.wait_visibility(cc.hsWheel.canvas)
        self.assertEqual(len(cc.hsWheel.callbacks)>0,True)
        cc.hsWheel.RemoveCallback(MyCallback)
        cc.hsWheel.RemoveCallback(cc.UpdateCurrentColor)
        self.assertEqual(len(cc.hsWheel.callbacks),0) 
        root.destroy()
    
    

if __name__ == '__main__':
    unittest.main()        

