
"""
    Copyright (C) <2010>  Autin L. TSRI
    
    This file git_upy/examples/Sphere.py is part of upy.

    upy is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    upy is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with upy.  If not, see <http://www.gnu.org/licenses/gpl-3.0.html>.
"""
import upy
upy.setUIClass()
from upy import uiadaptor
helperClass = upy.getHelperClass()

class SphereUI(uiadaptor):
    def setup(self,**kw):
        self.helper = helperClass(kw)
        self.initWidget()
        self.setupLayout()
        
    def CreateLayout(self):
        self._createLayout()
        return 1
        
    def Command(self,*args):
        self._command(args)
        return 1
        
    def initWidget(self,id=None):
        #this where we define the buttons
        self.createSphereButton = self._addElemt(name="Sphere",width=80,height=10,
                                     action=self.createSphere,type="button",icon=None,
                                     variable=self.addVariable("int",0))
        #the slider scale the sphere radius
        self.sphereSlider = self._addElemt(name="sphere_scale",width=80,height=10,
                                             action=self.scaleSphere,type="sliders",
                                             variable=self.addVariable("float",1.0),
                                             mini=0.01,maxi=5.,step=0.01)
    def setupLayout(self):
        self._layout = []
        self._layout.append([self.createSphereButton,self.sphereSlider])
        
    def createSphere(self,*args):
        name = "newSphere"
        o = self.helper.getObject(name)
        if o is None : 
            o = self.helper.Sphere(name,res=12)
            
    def scaleSphere(self,*args):
        #get the stat
        scale = self.getReal(self.sphereSlider)
        o = self.helper.getObject("newSphere")
        if o is not None : 
            self.helper.scaleObj(o,scale)

if uiadaptor.host == "tk":
    from DejaVu import Viewer
    vi = Viewer()    
    #require a master
    root = vi
    mygui = SphereUI(master=root,title="SphereUI")
    mygui.setup(master=root)
else :
    mygui = SphereUI(title="SphereUI")
    mygui.setup()
mygui.display()