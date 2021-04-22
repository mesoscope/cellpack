#!/usr/bin/python
import numpy.oldnumeric as Numeric
import sys, os, os.path, struct, math, string
import Blender
import bpy
from Blender import *
from Blender.Mathutils import *
from Blender import Object
from Blender import Material
from Blender import Mathutils
import math
import copy
import gzip
import types
import popen2
from Blender.Draw import *
from math import *
#from PDB7 import *
#from Haptic import pyQuat

import MolKit
from MolKit.molecule import Atom, AtomSet, BondSet, Molecule , MoleculeSet
from MolKit.protein import Protein, ProteinSet, Residue, Chain, ResidueSet
from MolKit.stringSelector import CompoundStringSelector
from MolKit.tree import TreeNode, TreeNodeSet
from MolKit.molecule import Molecule, Atom
from MolKit.protein import Residue

from types import StringType, ListType
from DejaVu.colorMap import ColorMap
from DejaVu.ColormapGui import ColorMapGUI


GL=Blender.BGL

DGatomIds=['ASPOD1','ASPOD2','GLUOE1','GLUOE2', 'SERHG',
                        'THRHG1','TYROH','TYRHH',
                        'LYSNZ','LYSHZ1','LYSHZ2','LYSHZ3','ARGNE','ARGNH1','ARGNH2',
                        'ARGHH11','ARGHH12','ARGHH21','ARGHH22','ARGHE','GLNHE21',
                        'GLNHE22','GLNHE2',
                        'ASNHD2','ASNHD21', 'ASNHD22','HISHD1','HISHE2' ,
                        'CYSHG', 'HN']

def b_matrix(array):
	return Mathutils.Matrix(array)

def b_toEuler(bmatrix):
	return bmatrix.toEuler()

def rotatePoint(pt,m,ax):
      x=pt[0]
      y=pt[1]
      z=pt[2]
      u=ax[0]
      v=ax[1]
      w=ax[2]
      ux=u*x
      uy=u*y
      uz=u*z
      vx=v*x
      vy=v*y
      vz=v*z
      wx=w*x
      wy=w*y
      wz=w*z
      sa=sin(ax[3])
      ca=cos(ax[3])
      pt[0]=(u*(ux+vy+wz)+(x*(v*v+w*w)-u*(vy+wz))*ca+(-wy+vz)*sa)+ m[0]
      pt[1]=(v*(ux+vy+wz)+(y*(u*u+w*w)-v*(ux+wz))*ca+(wx-uz)*sa)+ m[1]
      pt[2]=(w*(ux+vy+wz)+(z*(u*u+v*v)-w*(ux+vy))*ca+(-vx+uy)*sa)+ m[2]
      return pt

def Decompose4x4(matrix):
    """ takes a matrix in shape (16,) in OpenGL form (sequential values go
    down columns) and decomposes it into its rotation (shape (16,)),
    translation (shape (3,)), and scale (shape (3,)) """
    m = matrix
    transl = Numeric.array((m[12], m[13], m[14]), 'f')
    scale0 = Numeric.sqrt(m[0]*m[0]+m[4]*m[4]+m[8]*m[8])
    scale1 = Numeric.sqrt(m[1]*m[1]+m[5]*m[5]+m[9]*m[9])
    scale2 = Numeric.sqrt(m[2]*m[2]+m[6]*m[6]+m[10]*m[10])
    scale = Numeric.array((scale0,scale1,scale2)).astype('f')
    mat = Numeric.reshape(m, (4,4))
    rot = Numeric.identity(4).astype('f')
    rot[:3,:3] = mat[:3,:3].astype('f')
    rot[:,0] = (rot[:,0]/scale0).astype('f')
    rot[:,1] = (rot[:,1]/scale1).astype('f')
    rot[:,2] = (rot[:,2]/scale2).astype('f')
    rot.shape = (16,)
    #rot1 = rot.astype('f')
    return rot, transl, scale

def Compose4x4BGL(rot,trans,scale):
    import Blender 
    import numpy.oldnumeric as Numeric
    GL=Blender.BGL
    """ compose a matrix of shape (16,) from  a rotation (shape (16,)),
    translation (shape (3,)), and scale (shape (3,)) """
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glPushMatrix()
    GL.glLoadIdentity()
    GL.glTranslatef(float(trans[0]),float(trans[1]),float(trans[2]))
    GL.glMultMatrixf(rot)
    GL.glScalef(float(scale[0]),float(scale[1]),float(scale[2]))
    m = Numeric.array(GL.glGetDoublev(GL.GL_MODELVIEW_MATRIX)).astype('f')
    GL.glPopMatrix()
    return Numeric.reshape(m,(16,))

def norm(A):
        "Return vector norm"
        return Numeric.sqrt(sum(A*A))

def Compose4x4(rot,tr,sc):
    import Blender
    from Blender.Mathutils import * 
    import numpy.oldnumeric as Numeric
    """ compose a matrix of shape (16,) from  a rotation (shape (16,)),
    translation (shape (3,)), and scale (shape (3,)) """
    translation=Vector(tr[0],tr[1],tr[2])
    scale = Vector(sc[0],sc[1],sc[2])
    mat=rot.reshape(4,4)
    mat=mat.transpose()
    mt=TranslationMatrix(translation)
    mr=Matrix(mat[0],mat[1],mat[2],mat[3])
    ms=ScaleMatrix(scale.length, 4, scale.normalize())
    Transformation = mt*mr#*ms
    return Transformation


def dist(A,B):
  return Numeric.sqrt((A[0]-B[0])**2+(A[1]-B[1])**2+(A[2]-B[2])**2)

def normsq(A):
        "Return square of vector norm"
        return abs(sum(A*A))

def normalize(A):
        "Normalize the Vector"
        if (norm(A)==0.0) : return A
	else :return A/norm(A)

class ColorPalette(ColorMap):
    
    FLOAT = 0
    INT = 1

    def __init__(self, name, colorDict={}, readonly=0, colortype=None,
                 info='', sortedkeys=None, lookupMember=None):
        if len(colorDict) > 0:
            if sortedkeys is None:
                labels = list(colorDict.keys())
                values = list(colorDict.values())
            else:
                labels = sortedkeys
                values = []
                for label in labels:
                    values.append(colorDict[label])
        else:
            labels = None
            values = None

        
        #ColorMapGUI.__init__(self, name=name, ramp=values, labels=labels, show=False,
        #                     numOfBlockedLabels = len(labels) )
        ColorMap.__init__(self, name=name, ramp=values, labels=labels)

        self.readonly = readonly
        self.info = info
        #self.viewer = None
        self.sortedkeys = sortedkeys
        if colortype is None:
            self.colortype = self.FLOAT
        self.lookupMember = lookupMember


    def _lookup(self, name):
        try:
            col = ColorMap._lookup(self, name)
            if len(col) == 4:
                return col[:3]
            else:
                return col
        except:
            return (0., 1., 0.)


    def lookup(self, objects):
        # Maybe should try that first in case all the objects don't have the
        # lookup member
        names = objects.getAll(self.lookupMember)
        return list(map( self._lookup, names))


    def display(self,*args, **kw):
        """ Will create an instance of PaletteChooser later on"""
        pass


    def undisplay(self, *args, **kw):
        pass


    def copy(self):
        """make a deep copy of a palette"""
        import copy
        c = copy.copy(self)
        c.readonly = 0
        c.ramp = copy.deepcopy(self.ramp)
        c.labels = copy.deepcopy(self.labels)
        return c


class ColorPaletteFunction(ColorPalette):

    def __init__(self, name, colorDict={}, readonly=0, colortype=None,
                 info='', sortedkeys=None, lookupFunction = None):
        """ lookupFunction : needs to be function or a lambda function"""
        ColorPalette.__init__(self, name, colorDict, readonly,colortype,
                               info, sortedkeys)
        from types import FunctionType
        if not type(lookupFunction) is FunctionType:
            self.lookupFunction = None

        self.lookupFunction = lookupFunction
                     
          
    def lookup(self, objects):
        # maybe should do that in a try to catch the exception in case it
        # doesnt work
        names = list(map(self.lookupFunction, objects))
        return list(map(self._lookup, names))


class pybObject():
	def __init__(self,mesh,obj,name,atms ):
	    self.mesh=mesh
	    self.b_obj=obj
	    self.name=name
	    self.Atoms=atms

class Surface(pybObject):
	def __init__(self,mesh,obj,name,atms,srf ):
	    pybObject.__init__(self, mesh=mesh, obj=obj,name=name,atms=atms)
	    self.msmsAtoms=atms
	    self.msmsSurf=srf
AtmRadi = {"N":"1.54","C":"1.7","CA":"1.7","O":"1.52","S":"1.85","H":"1.2"}
matlist = str(Material.Get ())

if not ('[Material "C"]' in matlist):
	mat = Material.New('C')
	mat.R = 0.8
	mat.G = 0.8
	mat.B = 0.8

if not ('[Material "H"]' in matlist):
	mat = Material.New('H')
	mat.R = 0.6
	mat.G = 0.6
	mat.B = 0.6
	
if not ('[Material "B"]' in matlist):
	mat = Material.New('B')
	mat.R = 0.8
	mat.G = 0.6
	mat.B = 0.1
	
if not ('[Material "P"]' in matlist):
	mat = Material.New('P')
	mat.R = 0.9
	mat.G = 0.95
	mat.B = 0.1
	
if not ('[Material "N"]' in matlist):
	mat = Material.New('N')
	mat.R = 0.2
	mat.G = 0.1
	mat.B = 0.9
	
if not ('[Material "O"]' in matlist):
	mat = Material.New('O')
	mat.R = 1.0
	mat.G = 0.2
	mat.B = 0.1

if not ('[Material "S"]' in matlist):
	mat = Material.New('S')
	mat.R = 1.0
	mat.G = 1.0
	mat.B = 0.0
	
if not ('[Material "anyatom"]' in matlist):
	mat = Material.New('anyatom')
	mat.R = 0.8
	mat.G = 1.0
	mat.B = 1.0
	
if not ('[Material "sticks"]' in matlist):
	mat = Material.New('sticks')
	mat.R = 0.8
	mat.G = 0.8
	mat.B = 0.8


def computeRadius(protein,center=None):
		if center == None : center = protein.getCenter()
		rs = 0.
		for atom in protein.allAtoms:	
			r = dist(center,atom._coords[0])
			if r > rs:
				rs = r
		return rs

def Trace(x):
    #x is a list of atoms,if CA-> CAtrace
    #deprecated see Tube
    stick=[]  
    #coord1=x[0].atms[(x[0].atms.CApos())].xyz()
    #coord2=x[1].atms[(x[1].atms.CApos())].xyz()
    coord1=x[0]._coords[0]
    coord2=x[1]._coords[0]
    x1 = float(coord1[0])
    y1 = float(coord1[1])
    z1 = float(coord1[2])
    x2 = float(coord2[0])
    y2 = float(coord2[1])
    z2 = float(coord2[2])
    laenge = math.sqrt((x1-x2)*(x1-x2)+(y1-y2)*(y1-y2)+(z1-z2)*(z1-z2))
    wsz = math.atan2((y1-y2), (x1-x2))
    wz = math.acos((z1-z2)/laenge)

    me=Mesh.Primitives.Cylinder(32, 1., laenge)
    #mat = Material.Get('sticks')
    #me.materials=[mat]
    OBJ=Object.New('Mesh')
    stick.append(OBJ)
    stick[0].link(me)
    stick[0].setLocation(float(x1+x2)/2,(y1+y2)/2,(z1+z2)/2)
    stick[0].RotY = wz
    stick[0].RotZ = wsz
    #scn.link(stick[0])

    for i in range(1,len(x)-1):
     #coord1=x[i].atms[x[i].atms.CApos()].xyz() #x.xyz()[i].split()
     #coord2=x[i+1].atms[x[i+1].atms.CApos()].xyz() #x.xyz()[i+1].split()
     coord1=x[i]._coords[0] #x.xyz()[i].split()
     coord2=x[i+1]._coords[0] #x.xyz()[i+1].split()
     x1 = float(coord1[0])
     y1 = float(coord1[1])
     z1 = float(coord1[2])
     x2 = float(coord2[0])
     y2 = float(coord2[1])
     z2 = float(coord2[2])
     laenge = math.sqrt((x1-x2)*(x1-x2)+(y1-y2)*(y1-y2)+(z1-z2)*(z1-z2))
     wsz = math.atan2((y1-y2), (x1-x2))
     wz = math.acos((z1-z2)/laenge)
     me=Mesh.Primitives.Cylinder(32, 1., laenge)
     #mat = Material.Get('sticks')
     #me.materials=[mat]
     OBJ=Object.New('Mesh')
     stick.append(OBJ)
     stick[i].link(me)
     stick[i].setLocation(float(x1+x2)/2,(y1+y2)/2,(z1+z2)/2)
     stick[i].RotY = wz
     stick[i].RotZ = wsz
     #scn.link(stick[i])
     #scn= Scene.GetCurrent()
     #ob = scn.objects.new(stick)
    return stick

def bezFromVecs(vecs0,vecs1):
                       '''
                       Bezier triple from 3 vecs, shortcut functon
                       '''
                         
                       dd=[0.,0.,0.]
                       vecs=[0.,0.,0.]
                       for i in range(3): dd[i]=vecs1[i]-vecs0[i]
                       for i in range(3): vecs[i]=vecs1[i]+dd[i]
                       #vecs2=vecs1+(vecs0*-1)
                       bt= BezTriple.New(vecs0[0],vecs0[1],vecs0[2],vecs1[0],vecs1[1],vecs1[2],vecs[0],vecs[1],vecs[2])
                       bt.handleTypes= (BezTriple.HandleTypes.AUTO, BezTriple.HandleTypes.AUTO)
                       
                       return bt
def bezFromVecs2(vecs0,vecs1,vecs):
                       '''
                       Bezier triple from 3 vecs, shortcut functon
                       '''
                       #projection of v1 on v0->v2
                       #
                       B=Numeric.array([0.,0.,0.])
                       H1=Numeric.array([0.,0.,0.])
                       H2=Numeric.array([0.,0.,0.])
                       for i in range(3): B[i]=vecs1[i]-vecs0[i]                      
                       A=Numeric.array([0.,0.,0.])
                       for i in range(3): A[i]=vecs[i]-vecs0[i]
                       #Projection B on A
                       scalar=(((A[0]*B[0])+(A[1]*B[1])+(A[2]*B[2]))/((A[0]*A[0])+(A[1]*A[1])+(A[2]*A[2])))
                       C=scalar*A
                       #vector C->A
                       dep=A-C
                       for i in range(3):
                            vecs0[i]=(vecs0[i]+dep[i])
                            vecs[i]=(vecs[i]+dep[i])
                       for i in range(3): H1[i]=(vecs[i]-vecs1[i])
                       for i in range(3): H2[i]=(-vecs[i]+vecs1[i])
                       H1=normalize(H1.copy())*3.
                       H2=normalize(H2.copy())*3.
                       vecs0=Vector(vecs1[0]-H1[0],vecs1[1]-H1[1],vecs1[2]-H1[2])
                       vecs=Vector(vecs1[0]-H2[0],vecs1[1]-H2[1],vecs1[2]-H2[2])
                       #vecs2=vecs1+(vecs0*-1)
                       bt= BezTriple.New(vecs0[0],vecs0[1],vecs0[2],vecs1[0],vecs1[1],vecs1[2],vecs[0],vecs[1],vecs[2])
                       bt.handleTypes= (BezTriple.HandleTypes.FREE , BezTriple.HandleTypes.FREE )
                       
                       return bt

def bez2FromVecs(vecs1):
                       
                       bt= BezTriple.New(vecs1[0],vecs1[1],vecs1[2])
                       bt.handleTypes= (BezTriple.HandleTypes.AUTO  , BezTriple.HandleTypes.AUTO  )
                       
                       return bt
                      
def bezFromVecs1(vecs0,vecs1,vecs): #tYPE vECTOR
                       '''
                       Bezier triple from 3 vecs, shortcut functon
                       '''
                       #rotatePoint(pt,m,ax)
                       A=Vector(0.,0.,0.)
                       B=Vector(0.,0.,0.)
                       H2=Vector(0.,0.,0.)
                       A=vecs0-vecs1                     
                       B=vecs-vecs1
                       crP=A.cross(B)
                       crP.normalize()
                       A.normalize()
                       B.normalize()
                       #angleA,B: acos of the dot product of the two (normalised) vectors:
                       dot=A.dot(B)
                       angle=math.acos(dot)
                       print(angle)
                       print(math.degrees(angle))
                       newA=(math.radians(90)-angle/2)
                       nA=rotatePoint(A*1.35,vecs1,[crP[0],crP[1],crP[2],-newA])
                       nB=rotatePoint(B*1.35,vecs1,[crP[0],crP[1],crP[2],newA])
                       vecs0=Vector(nA[0],nA[1],nA[2])
                       vecs=Vector(nB[0],nB[1],nB[2])
                       #vecs2=vecs1+(vecs0*-1)
                       bt= BezTriple.New(vecs0[0],vecs0[1],vecs0[2],vecs1[0],vecs1[1],vecs1[2],vecs[0],vecs[1],vecs[2])
                       bt.handleTypes= (BezTriple.HandleTypes.FREE , BezTriple.HandleTypes.FREE )
                       
                       return bt


    
def bezList2Curve(x,typeC):
               '''
               Take a list or vector triples and converts them into a bezier curve object
               '''
               # Create the curve data with one point
               cu= Curve.New()
               #coord0=x[0].atms[(x[0].atms.Cpos())-1].xyz()
               #coord1=x[0].atms[(x[0].atms.Cpos())].xyz()
   	       coord1=Numeric.array(x[0]._coords[0])
               coord2=Numeric.array(x[1]._coords[0])
               print(coord1)
               print(coord2)
               coord0=coord1-(coord2-coord1)

               if typeC == "tBezier" : cu.appendNurb(bezFromVecs(Vector(coord0[0],coord0[1],coord0[2]),Vector(coord1[0],coord1[1],coord1[2]))) # We must add with a point to start with
               elif typeC == "sBezier" : cu.appendNurb(bez2FromVecs(Vector(coord1[0],coord1[1],coord1[2])))
               else : cu.appendNurb(bezFromVecs1(Vector(coord0[0],coord0[1],coord0[2]),Vector(coord1[0],coord1[1],coord1[2]),Vector(coord2[0],coord2[1],coord2[2]))) # We must add with a point to start with
               
               cu_nurb= cu[0] # Get the first curve just added in the CurveData
               
               
               i= 1 # skip first vec triple because it was used to init the curve
               while i<(len(x)-1):
                       coord0=x[i-1]._coords[0]#atms[(x[i].atms.Cpos())-1].xyz()
                       coord1=x[i]._coords[0]#atms[(x[i].atms.Cpos())].xyz()
                       coord2=x[i+1]._coords[0]
                       bt_vec_tripleAv= Vector(coord0[0],coord0[1],coord0[2])
                       bt_vec_triple  = Vector(coord1[0],coord1[1],coord1[2])
                       bt_vec_tripleAp= Vector(coord2[0],coord2[1],coord2[2])
                       bt= bezFromVecs(bt_vec_tripleAv,bt_vec_triple)

                       if typeC == "tBezier" : cu_nurb.append(bt)
                       elif typeC == "sBezier" : cu_nurb.append(bez2FromVecs(Vector(coord1[0],coord1[1],coord1[2])))
                       else : cu_nurb.append(bezFromVecs1(bt_vec_tripleAv,bt_vec_triple,bt_vec_tripleAp))
                       i+=1              
               # Add the Curve into the scene
   	       coord0=Numeric.array(x[len(x)-2]._coords[0])
               coord1=Numeric.array(x[len(x)-1]._coords[0])
               print(coord1)
               print(coord2)
               coord2=coord1+(coord1-coord0)

               if typeC == "tBezier" : cu_nurb.append(bezFromVecs(Vector(coord0[0],coord0[1],coord0[2]),Vector(coord1[0],coord1[1],coord1[2]))) # We must add with a point to start with
               elif typeC == "sBezier" : cu_nurb.append(bez2FromVecs(Vector(coord1[0],coord1[1],coord1[2])))
               else : cu_nurb.append(bez2FromVecs(Vector(coord1[0],coord1[1],coord1[2])))
               #else : cu_nurb.append(bezFromVecs1(Vector(coord0[0],coord0[1],coord0[2]),Vector(coord1[0],coord1[1],coord1[2]),Vector(coord2[0],coord2[1],coord2[2]))) # We must add with a point to start with
                
               return cu
def bezSquare(r,name):
      kappa=4*((math.sqrt(2)-1)/3)
      l = r * kappa
      pt1=[0.,r,0.]
      pt1h=[-l,r,0.]
      pt2=[r,0.,0.]
      pt2h=[r,l,0.]
      pt3=[0.,-r,0.]
      pt3h=[l,-r,0.]
      pt4=[-r,0.,0.]
      pt4h=[-r,-l,0.]
      cu= Curve.New(name)
      coord1=pt1
      cu.appendNurb(bez2FromVecs(pt1))
      cu_nurb=cu[0]
      coord1=pt2
      cu_nurb.append(bez2FromVecs(pt2))
      coord1=pt3
      cu_nurb.append(bez2FromVecs(pt3))
      coord1=pt4
      cu_nurb.append(bez2FromVecs(pt4))
      cu_nurb.append(bez2FromVecs(pt1))
      #scn= Scene.GetCurrent()
      #ob = scn.objects.new(cu)
      return cu


def bezCircle(r,name):
      kappa=4*((math.sqrt(2)-1)/3)
      l = r * kappa
      pt1=[0.,r,0.]
      pt1h=[-l,r,0.]
      pt2=[r,0.,0.]
      pt2h=[r,l,0.]
      pt3=[0.,-r,0.]
      pt3h=[l,-r,0.]
      pt4=[-r,0.,0.]
      pt4h=[-r,-l,0.]
      cu= Curve.New(name)
      coord1=pt1
      cu.appendNurb(bezFromVecs(pt1h,pt1))
      cu_nurb=cu[0]
      coord1=pt2
      cu_nurb.append(bezFromVecs(pt2h,pt2))
      coord1=pt3
      cu_nurb.append(bezFromVecs(pt3h,pt3))
      coord1=pt4
      cu_nurb.append(bezFromVecs(pt4h,pt4))
      cu_nurb.append(bezFromVecs(pt1h,pt1))
      #scn= Scene.GetCurrent()
      #ob = scn.objects.new(cu)
      return cu

def Centroid(f,P0) : 
  for v in f.v: 
    for n in [0,1,2] : 
       P0[n]+=v.co[n]/len(f.v) 
  return P0

def mean(list):
    """
    Given a list or tuple, will return the mean.
    Usage mean(list)
    """
    
    sum = 0;
    for item in list:
        sum += item
        
    return(sum / len(list))

def makeRuban(x,str_type,r,name,scene):
	#the bezierCurve"tBezier"
	cu=bezList2Curve(x,str_type)
	#the circle
	if name == "Circle" : ob1 = scene.objects.new(bezCircle(r,name))
	if name == "Square" : ob1 = scene.objects.new(bezSquare(r,name))
	#extrude
	cu.setBevOb(ob1)
	cu.setFlag(1)
	#make the object
	ob = scene.objects.new(cu)
	return ob


def armature(name,x,scn):
 armObj = Object.New('Armature', name)
 armData = Armature.New()
 armData.makeEditable()
 armData.autoIK=bool(1)
 armData.vertexGroups=bool(1)
 #N=nbones
 bones= []
 eb = Armature.Editbone()
 eb.roll = 10
 #eb.parent = arm.bones['Bone.003']
 #coord1=x[0].atms[x[0].atms.CApos()].xyz() #x.xyz()[i].split()
 #coord2=x[1].atms[x[1].atms.CApos()].xyz() #x.xyz()[i+1].split()
 coord1=x[0]._coords[0]
 coord2=x[1]._coords[0]		
 eb.head = Vector(coord1[0],coord1[1],coord1[2])
 eb.tail = Vector(coord2[0],coord2[1],coord2[2])
 eb.headRadius=x[0].vdwRadius#0.5
 eb.tailRadius=x[0].vdwRadius#0.5
 eb.deformDist=0.6
 #eb.weight=0.02
 #eb.options = [Armature.NO_DEFORM]
 bones.append(eb)
 armData.bones['bone0'] = bones[0]

 for i in range(1,len(x)-1):
  print(i)
  print(i-1)
  armData.makeEditable()
  eb = Armature.Editbone()
  eb.roll = 10
  print("bone"+str(i-1))
  #coord1=x[i].atms[x[i].atms.CApos()].xyz() #x.xyz()[i].split()
  #coord2=x[i+1].atms[x[i+1].atms.CApos()].xyz() #x.xyz()[i+1].split()
  coord1=x[i]._coords[0] #x.xyz()[i].split()
  coord2=x[i+1]._coords[0] #x.xyz()[i+1].split()
  eb.head = Vector(coord1[0],coord1[1],coord1[2])
  eb.tail = Vector(coord2[0],coord2[1],coord2[2])
  eb.headRadius=x[i].vdwRadius#0.5
  eb.tailRadius=x[i+1].vdwRadius
  eb.deformDist=0.6

 #if ( (i % 2) == 1 ) : eb.options = [Armature.HINGE, Armature.CONNECTED]
 #if ( (i % 2) == 0 ) : eb.options = [Armature.HINGE, Armature.CONNECTED,Armature.NO_DEFORM]
  eb.options = [Armature.HINGE, Armature.CONNECTED]
  eb.parent = bones[i-1]
  bones.append(eb)
  #eb.parent = armData.bones["bone"+str(i-1)]
  armData.bones['bone'+str(i)] = bones[i]

  #for bone in armData.bones.values():
  #   #print bone.matrix['ARMATURESPACE']
  #   print bone.parent, bone.name
  #   print bone.options, bone.name

 armObj.link(armData)
 armData.update()
 scn.objects.link(armObj)
 return armObj

def add_armature(armObj,obj):
     print(obj)
     mods = obj.modifiers
     print(mods)
     mod=mods.append(Modifier.Types.ARMATURE)
     mod[Modifier.Settings.OBJECT] = armObj
     print(mod)
     obj.addVertexGroupsFromArmature(armObj)
     print('done')
	

"""
def Sphere(atom,radius,res):
    	atN=at.name
    	atC=atom._coords[0]
 	me=Mesh.Primitives.UVsphere(64,res,radius)#
	mat = Material.Get(atom.name[0])
	me.materials=[mat]
	OBJ=Object.New('Mesh')
	OB.link(me)
	OB.setLocation(float(atC[0]),float(atC[1]),float(atC[2]))   
	return OB

def createMeshSphere(**kwargs):
		# default the values
		radius = kwargs.get('radius',1.0)
		diameter = radius *2.0
		segments = kwargs.get('segments',8)
		rings = kwargs.get('rings',8)
		loc   = kwargs.get('location',[0,0,0])
		useIco = kwargs.get('useIco',False)
		useUV = kwargs.get('useUV',True)
		subdivisions = kwargs.get('subdivisions',2)
		if useIco:
			sphere = Blender.Mesh.Primitives.Icosphere(subdivisions,diameter)
		else:	
			sphere = Blender.Mesh.Primitives.UVsphere(segments,rings,diameter)
		#ob = self.scene.objects.new(item,name)	
		#ob.setLocation(loc)
		return sphere
"""
def Tube(name,nTube,x,scn,armObj,res=32,size=0.25,sc=2.,join=0):
 print("size sel")
 print(len(x))
 stick=[]
 tube=[]
 size=size*2.
 #coord1=x[0].atms[x[0].atms.CApos()].xyz() #x.xyz()[i].split()
 #coord2=x[1].atms[x[1].atms.CApos()].xyz() #x.xyz()[i+1].split()
 coord1=x[0]._coords[0]
 coord2=x[1]._coords[0]
 x1 = float(coord1[0])
 y1 = float(coord1[1])
 z1 = float(coord1[2])
 x2 = float(coord2[0])
 y2 = float(coord2[1])
 z2 = float(coord2[2])
 laenge = math.sqrt((x1-x2)*(x1-x2)+(y1-y2)*(y1-y2)+(z1-z2)*(z1-z2))
 wsz = atan2((y1-y2), (x1-x2))
 wz = acos((z1-z2)/laenge)
 me=Mesh.Primitives.Cylinder(res, size, laenge/sc) #1. CAtrace, 0.25 regular |sc=1 CATrace, 2 regular
 mat = Material.Get('sticks')
 me.materials=[mat]
 tube.append(me)
 #OBJ=Object.New('Mesh')
 fullname = x[0].full_name()
 OBJ=Object.New('Mesh',"T_"+fullname)
 stick.append(OBJ)
 stick[0].link(me)
 stick[0].setLocation(float(x1+x2)/2,(y1+y2)/2,(z1+z2)/2)
 stick[0].RotY = wz
 stick[0].RotZ = wsz
 if armObj != None : 
     mods = stick[0].modifiers
     mod=mods.append(Modifier.Types.ARMATURE)
     mod[Modifier.Settings.OBJECT] = armObj
 scn.link(stick[0])
 for i in range(1,len(x)-1):
  coord1=x[i]._coords[0] #x.xyz()[i].split()
  coord2=x[i+1]._coords[0] #x.xyz()[i+1].split()
  x1 = float(coord1[0])
  y1 = float(coord1[1])
  z1 = float(coord1[2])
  x2 = float(coord2[0])
  y2 = float(coord2[1])
  z2 = float(coord2[2])
  laenge = math.sqrt((x1-x2)*(x1-x2)+(y1-y2)*(y1-y2)+(z1-z2)*(z1-z2))
  wsz = atan2((y1-y2), (x1-x2))
  wz = acos((z1-z2)/laenge)
  me=Mesh.Primitives.Cylinder(res, size, laenge/sc)
  mat = Material.Get('sticks')
  me.materials=[mat]
  tube.append(me)
  fullname = x[i].full_name()
  OBJ=Object.New('Mesh',"T_"+fullname)
  #OBJ=Object.New('Mesh')
  stick.append(OBJ)
  stick[i].link(me)
  stick[i].setLocation(float(x1+x2)/2,(y1+y2)/2,(z1+z2)/2)
  stick[i].RotY = wz
  stick[i].RotZ = wsz
  if armObj != None : 
     mods = stick[i].modifiers
     mod=mods.append(Modifier.Types.ARMATURE)
     mod[Modifier.Settings.OBJECT] = armObj
  scn.link(stick[i])
 if join==1 : 
 	stick[0].join(stick[1:])
 	for ind in range(1,len(stick)):
		#obj[0].join([obj[ind]])
		scn.unlink(stick[ind])
	#obj[0].setName(name)
 return stick,tube

def pmvTube(name,points,faces,scn,armObj,res=32,size=0.25,sc=2.,join=0):
 stick=[]
 tube=[]
 size=size*2.
 #coord1=x[0].atms[x[0].atms.CApos()].xyz() #x.xyz()[i].split()
 #coord2=x[1].atms[x[1].atms.CApos()].xyz() #x.xyz()[i+1].split()
 print(len(points))
 print(len(faces))
 coord1=points[faces[0][0]]
 coord2=points[faces[0][1]]
 x1 = float(coord1[0])
 y1 = float(coord1[1])
 z1 = float(coord1[2])
 x2 = float(coord2[0])
 y2 = float(coord2[1])
 z2 = float(coord2[2])
 laenge = math.sqrt((x1-x2)*(x1-x2)+(y1-y2)*(y1-y2)+(z1-z2)*(z1-z2))
 wsz = atan2((y1-y2), (x1-x2))
 wz = acos((z1-z2)/laenge)
 me=Mesh.Primitives.Cylinder(res, size, laenge/sc) #1. CAtrace, 0.25 regular |sc=1 CATrace, 2 regular
 mat = Material.Get('sticks')
 me.materials=[mat]
 tube.append(me)
 #OBJ=Object.New('Mesh')
 #fullname = x[0].full_name()
 OBJ=Object.New('Mesh',"T_0")
 stick.append(OBJ)
 stick[0].link(me)
 stick[0].setLocation(float(x1+x2)/2,(y1+y2)/2,(z1+z2)/2)
 stick[0].RotY = wz
 stick[0].RotZ = wsz
 if armObj != None : 
     mods = stick[0].modifiers
     mod=mods.append(Modifier.Types.ARMATURE)
     mod[Modifier.Settings.OBJECT] = armObj
 scn.link(stick[0])
 for i in range(1,len(faces)):
  coord1=points[faces[i][0]]
  coord2=points[faces[i][1]]
  x1 = float(coord1[0])
  y1 = float(coord1[1])
  z1 = float(coord1[2])
  x2 = float(coord2[0])
  y2 = float(coord2[1])
  z2 = float(coord2[2])
  laenge = sqrt((x1-x2)*(x1-x2)+(y1-y2)*(y1-y2)+(z1-z2)*(z1-z2))
  wsz = atan2((y1-y2), (x1-x2))
  wz = acos((z1-z2)/laenge)
  me=Mesh.Primitives.Cylinder(res, size, laenge/sc)
  mat = Material.Get('sticks')
  me.materials=[mat]
  tube.append(me)
  #fullname = x[i].full_name()
  OBJ=Object.New('Mesh',"T_"+str(i))
  #OBJ=Object.New('Mesh')
  stick.append(OBJ)
  stick[i].link(me)
  stick[i].setLocation(float(x1+x2)/2,(y1+y2)/2,(z1+z2)/2)
  stick[i].RotY = wz
  stick[i].RotZ = wsz
  if armObj != None : 
     mods = stick[i].modifiers
     mod=mods.append(Modifier.Types.ARMATURE)
     mod[Modifier.Settings.OBJECT] = armObj
  scn.link(stick[i])
 if join==1 : 
 	stick[0].join(stick[1:])
 	for ind in range(1,len(stick)):
		#obj[0].join([obj[ind]])
		scn.unlink(stick[ind])
	#obj[0].setName(name)
 return stick,tube

AtmRadi = {"N":"1.54","C":"1.7","O":"1.52","S":"1.85","H":"1.2"}

def createBaseTube(quality=0,radius=None):
    #default the values.
    #QualitySph={"0":[64,32],"1":[5,5],"2":[10,10],"3":[15,15],"4":[20,20]"5":[25,25]} 
    segments=quality*5
    rings=quality*5
    if quality == 0 : 
		segments = 25
		rings = 25
    iMe={}	
    for atn in 	list(AtmRadi.keys()):
		if radius==None : radius=AtmRadi[atn]
		iMe[atn]=Mesh.Primitives.UVsphere(int(segments),int(rings),float(radius)*2.)
		mat = Material.Get(atn)
		iMe[atn].materials=[mat]
		#iMe[atn].smooth()
		print(atn,iMe[atn])
    return iMe



def createBaseSphere(quality=0,radius=None):
    AtmRadi = {"N":"1.54","C":"1.7","O":"1.52","S":"1.85","H":"1.2"}
    #default the values.
    #QualitySph={"0":[64,32],"1":[5,5],"2":[10,10],"3":[15,15],"4":[20,20]"5":[25,25]} 
    segments=quality*5
    rings=quality*5
    if quality == 0 : 
		segments = 25
		rings = 25
    iMe={}
    for atn in 	list(AtmRadi.keys()):
		rad=AtmRadi[atn]
		if radius !=None : rad=radius
		iMe[atn]=Mesh.Primitives.UVsphere(int(segments),int(rings),float(rad)*2.)
		mat = Material.Get(atn)
		iMe[atn].materials=[mat]
		#iMe[atn].smooth()
		print(atn,iMe[atn])
    return iMe
	
def instanceMesh(name,iMe,x,scn,armObj,scale,Res=32,R=None,join=0):
 obj=[]
 k=0
 n='S'
 if name.find('balls') != (-1) : n='B'
 for j in range(len(x)):
    at=x[j]
    atN=at.name
    print(atN)
    fullname = at.full_name()
    atC=at._coords[0]
    OBJ=scn.objects.new(iMe[atN[0]],n+"_"+fullname)
    OBJ.setLocation(float(atC[0]),float(atC[1]),float(atC[2]))
    #OBJ=Object.New('Mesh',"S_"+fullname)   
    obj.append(OBJ)
    #print iMe[atN[0]]
    #print OBJ
    #print atC
    #obj[k].link(iMe[atN[0]])
    #obj[k].setLocation(float(atC[0]),float(atC[1]),float(atC[2]))  
 if join==1 : 
	obj[0].join(obj[1:])
	for ind in range(1,len(obj)):
		scn.unlink(obj[ind])
	obj[0].setName(name)
 #vdwObj=pybObject(mesh=iMe,obj=obj[0],name=name,atms=x)
 return  obj

def AtomMesh(name,typMes,x,scn,armObj,scale,Res=32,R=None,join=0):
 #pr=Group.New(name)
 if scale == 0.0 : scale =1.
 scale = scale *2.
 Rsph=[]
 Robj=[]
 #resGr=[]
 mod=[]
 spher=[]
 obj=[]
 if Res == 0 : Res = 10.
 else : Res = Res *5.
 if typMes == "Mb" : 
    #bball =  Blender.Object.New("Mball","mb")
    metab = Blender.Metaball.New()
    #ob_mb = scn.objects.new(metab)
 k=0
 #for i in range(len(x)):
 # res=x[i]
 # resN=res.name
 # resG=Group.New(resN+str(i))
  #resGr.append(resG)
 # t=len(res.atoms)
 for j in range(len(x)):
    #at=res.atoms[j]
    at=x[j]
    atN=at.name
    fullname = at.full_name()
    print(fullname)
    atC=at._coords[0]
    #at.colors[name] = (1.,1.,1.)
    #at.opacities[name] = 1.0
    if R !=None : rad=R
    elif atN[0] in AtmRadi : rad=AtmRadi[atN[0]]
    else : rad=AtmRadi['H']
    if typMes == "Cube" : me=Mesh.Primitives.Cube(float(rad)*scale) #Cylinder(verts, diameter, length)
    elif typMes == "Sphere" : 
	print("SPHERE"+str(j))
    	me=Mesh.Primitives.UVsphere(64,int(Res),float(rad)*scale)
    elif typMes == "Empty2" : 
    	me=Mesh.Primitives.UVsphere(64,int(Res),0.1)
    elif typMes == "Mb":
       me=metab.elements.add()
       me.radius=float(rad)*3     
    elif typMes == "Empty" : 
       me = Blender.Object.New('Empty', 'Empty-'+fullname)
       #me.co = atC[0], atC[1], atC[2]
       obj.append(me)
       obj[k].setLocation(float(atC[0]),float(atC[1]),float(atC[2]))  	
       scn.link(obj[k])
       if armObj != None : 
     		mods = obj[k].modifiers
		mod=mods.append(Modifier.Types.ARMATURE)
		mod[Modifier.Settings.OBJECT] = armObj
    if atN[0] in AtmRadi : mat = Material.Get(atN[0])
    else : mat = Material.Get('H')
    if typMes == "Mb" : 
		me.co = Blender.Mathutils.Vector(atC[0], atC[1], atC[2])	
		me.materials=[mat]
    elif typMes != "Empty" : 
	me.materials=[mat]
	spher.append(me)
	OBJ=Object.New('Mesh',typMes[0]+"_"+fullname)
	#resG.objects.link(OBJ)
	obj.append(OBJ)
	obj[k].link(spher[k])
	obj[k].setLocation(float(atC[0]),float(atC[1]),float(atC[2]))   
    #print obj[k]
    	#resGr[i].objects=obj
    #mods = obj[k].modifiers
    #mod=mods.append(Modifier.Types.ARMATURE)
    #mod[Modifier.Settings.OBJECT] = armObj
    	#scn.link(obj[k])
	if armObj != None : 
     		mods = obj[i].modifiers
		mod=mods.append(Modifier.Types.ARMATURE)
		mod[Modifier.Settings.OBJECT] = armObj
    k=k+1
    #obj[i].link(mat)
  #Rsph.append(spher) 
  #Robj.append(obj)
  #pr.objects.link(resG)
 if typMes == "Mb":
   #bball.link(metab)
   ob_mb = scn.objects.new(metab)
   if armObj != None :
    modi=ob_mb.modifiers
    mo=modi.append(Modifier.Types.ARMATURE)
    mo[Modifier.Settings.OBJECT] = armObj
    obj=ob_mb
    #scn.link(bball)
 #join the mesh..
 if typMes != "Mb" and typMes != "Empty"  and join==1 : 
	obj[0].join(obj[1:])
	for ind in range(1,len(obj)):
		#obj[0].join([obj[ind]])
		scn.unlink(obj[ind])
	obj[0].setName(name)
 vdwObj=pybObject(mesh=spher,obj=obj,name=name,atms=x)
 return  vdwObj,obj,spher 


def ball(name, type, x, y, z):
	global structmode, scatom, sumatom, refineballs, refinesticks, balls, sticks, scsticks
	# Objekt erstellen
	ob = Object.New('Mesh', name)
	# Mesh erstellen
	me = Mesh.New(name)
	# Ball erstellen
	a = 0.0000	
	b = 0.0000
	vcount = 0
	da = 360.00 / refineballs.val
	db = 360.00 / refineballs.val
	#da = 30.0
	#db = 30.0
	dx = 0.0
	dy = 0.0
	dz = 0.0
	pi = asin(1)
	if type == "C":	
		radius = 0.772
		mat = Material.Get('C')
	elif type == "H": 
		radius = 0.373
		mat = Material.Get('H')
	elif type == "B": 
		radius = 0.83
		mat = Material.Get('B')
	elif type == "N": 
		radius = 0.71
		mat = Material.Get('N')
	elif type == "O": 
		radius = 0.604
		mat = Material.Get('O')
	elif type == "P": 
		radius = 0.93
		mat = Material.Get('P')
	else: 
		radius = 0.8
		mat = Material.Get('anyatom')
		
	me.materials = [mat]
	
	radius = radius * scatom.val + sumatom.val
	
	
	# erster Punkt
	me.verts.extend(0, 0, radius)
	a = a + da
	
	# Kappe
		
	while b < 360:
		dz = radius*cos(a/90*pi)
		dx = radius*sin(a/90*pi)*sin(b/90*pi)
		dy = radius*sin(a/90*pi)*cos(b/90*pi)
		b = b + db
		me.verts.extend(dx, dy, dz)
		vcount = vcount + 1
		if vcount > 1:
			me.faces.extend([me.verts[0],me.verts[vcount],me.verts[vcount-1]])
	
	me.faces.extend([me.verts[0],me.verts[1],me.verts[vcount]])
	
	b = 0.00
	kcount = 0
	vvcount = 0
	a = a + da
	
	
	while a < 180:
		while b < 360:
			dz = radius*cos(a/90*pi)
			dx = radius*sin(a/90*pi)*sin(b/90*pi)
			dy = radius*sin(a/90*pi)*cos(b/90*pi)
			me.verts.extend(dx, dy, dz)
			vcount = vcount + 1
			vvcount = vvcount + 1
			if vvcount > 1:
				me.faces.extend([me.verts[vcount],me.verts[vcount-1],me.verts[vcount-int(360/db)-1],me.verts[vcount-int(360/db)]])
				if b == 360-db:
					me.faces.extend([me.verts[vcount],me.verts[vcount-int(360/db)],me.verts[vcount-2*int(360/db)+1],me.verts[vcount-int(360/db)+1]])
			b = b + db
		kcount = kcount + 1
		b = 0
		vvcount = 0
		a = a + da
		
	# letzter Punkt
	me.verts.extend(0, 0, -radius)
	vcount = vcount + 1
	b = 0
	while b < 360-db:
		me.faces.extend([me.verts[vcount],me.verts[vcount-int(b/db)-2],me.verts[vcount-int(b/db)-1]])
		b = b + db
	
	me.faces.extend([me.verts[vcount],me.verts[vcount-1],me.verts[vcount-int((360-db)/db)-1]])
	eins = 1
	for face in me.faces:
		face.smooth=1
	

	ob.link (me)
	ob.loc = (x,y,z)
	scene.link (ob)
	
def stick1(x1, y1, z1, x2, y2, z2, radius):
	global structmode, scatom, sumatom, refineballs, refinesticks, balls, sticks, scsticks
	# Objekt erstellen
	ob = Object.New('Mesh')
	# Mesh erstellen
	me = Mesh.New()
	mat = Material.Get('sticks')
	me.materials = [mat]
	# Stick erstellen
	a = 0.0000	
	b = 0.0000
	vcount = 0
	da = 360.00 / refinesticks.val
	db = 360.00 / refinesticks.val
	dx = 0.0
	dy = 0.0
	dz = 0.0
	pi = asin(1)
	laenge = sqrt((x1-x2)*(x1-x2)+(y1-y2)*(y1-y2)+(z1-z2)*(z1-z2))
	wsz = atan2((y1-y2), (x1-x2))
	wz = acos((z1-z2)/laenge)
	
	
	# erster Punkt
	me.verts.extend(0, 0, laenge/2+radius)
	a = a + da
	
	# Kappe
		
	while b < 360:
		dz = radius*cos(a/90*pi)
		dx = radius*sin(a/90*pi)*sin(b/90*pi)
		dy = radius*sin(a/90*pi)*cos(b/90*pi)
		b = b + db
		me.verts.extend(dx, dy, dz+laenge/2)
		vcount = vcount + 1
		if vcount > 1:
			me.faces.extend([me.verts[0],me.verts[vcount],me.verts[vcount-1]])
	
	me.faces.extend([me.verts[0],me.verts[1],me.verts[vcount]])
	
	b = 0.00
	kcount = 0
	vvcount = 0
	a = a + da
	
	
	while a < 90:
		while b < 360:
			dz = radius*cos(a/90*pi)
			dx = radius*sin(a/90*pi)*sin(b/90*pi)
			dy = radius*sin(a/90*pi)*cos(b/90*pi)
			me.verts.extend(dx, dy, dz+laenge/2)
			vcount = vcount + 1
			vvcount = vvcount + 1
			if vvcount > 1:
				me.faces.extend([me.verts[vcount],me.verts[vcount-1],me.verts[vcount-int(360/db)-1],me.verts[vcount-int(360/db)]])
				if b == 360-db:
					me.faces.extend([me.verts[vcount],me.verts[vcount-int(360/db)],me.verts[vcount-2*int(360/db)+1],me.verts[vcount-int(360/db)+1]])
			b = b + db
		kcount = kcount + 1
		b = 0
		vvcount = 0
		a = a + da
		
	a = 90
	b = 0.00
	vvcount = 0
	
	while b < 360:
		dx = radius*sin(b/90*pi)
		dy = radius*cos(b/90*pi)
		me.verts.extend(dx, dy, laenge/2)
		vcount = vcount + 1
		vvcount = vvcount + 1
		if vvcount > 1:
			me.faces.extend([me.verts[vcount],me.verts[vcount-1],me.verts[vcount-int(360/db)-1],me.verts[vcount-int(360/db)]])
			if b == 360-db:
				me.faces.extend([me.verts[vcount],me.verts[vcount-int(360/db)],me.verts[vcount-2*int(360/db)+1],me.verts[vcount-int(360/db)+1]])
		b = b + db
	kcount = kcount + 1
	b = 0.00
	vvcount = 0	
	
	while b < 360:
		dx = radius*sin(b/90*pi)
		dy = radius*cos(b/90*pi)
		me.verts.extend(dx, dy, -laenge/2)
		vcount = vcount + 1
		vvcount = vvcount + 1
		if vvcount > 1:
			me.faces.extend([me.verts[vcount],me.verts[vcount-1],me.verts[vcount-int(360/db)-1],me.verts[vcount-int(360/db)]])
			if b == 360-db:
				me.faces.extend([me.verts[vcount],me.verts[vcount-int(360/db)],me.verts[vcount-2*int(360/db)+1],me.verts[vcount-int(360/db)+1]])
		b = b + db
	kcount = kcount + 1
	b = 0.00
	vvcount = 0	
	
	while a < 180:
		while b < 360:
			dz = radius*cos(a/90*pi)
			dx = radius*sin(a/90*pi)*sin(b/90*pi)
			dy = radius*sin(a/90*pi)*cos(b/90*pi)
			me.verts.extend(dx, dy, dz-laenge/2)
			vcount = vcount + 1
			vvcount = vvcount + 1
			if vvcount > 1:
				me.faces.extend([me.verts[vcount],me.verts[vcount-1],me.verts[vcount-int(360/db)-1],me.verts[vcount-int(360/db)]])
				if b == 360-db:
					me.faces.extend([me.verts[vcount],me.verts[vcount-int(360/db)],me.verts[vcount-2*int(360/db)+1],me.verts[vcount-int(360/db)+1]])
			b = b + db
		kcount = kcount + 1
		b = 0.00
		vvcount = 0
		a = a + da
		
	# letzter Punkt
	me.verts.extend(0, 0, -laenge/2-radius)
	vcount = vcount + 1
	b = 0
	while b < 360-db:
		me.faces.extend([me.verts[vcount],me.verts[vcount-int(b/db)-2],me.verts[vcount-int(b/db)-1]])
		b = b + db
	
	me.faces.extend([me.verts[vcount],me.verts[vcount-1],me.verts[vcount-int((360-db)/db)-1]])
	eins = 1
	for face in me.faces:
		face.smooth=1
	
	
	ob.link (me)
	x1 = float(x1)
	y1 = float(y1)
	z1 = float(z1)
	x2 = float(x2)
	y2 = float(y2)
	z2 = float(z2)
	ob.loc = (float(x1+x2)/2,(y1+y2)/2,(z1+z2)/2)
	ob.RotY = wz
	ob.RotZ = wsz
	scene.link (ob)

def stick2(x1, y1, z1, x2, y2, z2, radius):
	global structmode, scatom, sumatom, refineballs, refinesticks, balls, sticks, scsticks
	# Objekt erstellen
	ob = Object.New('Mesh')
	# Mesh erstellen
	me = Mesh.New()
	mat = Material.Get('sticks')
	me.materials = [mat]
	# Stick erstellen
	b = 0.0000
	vcount = -1
	db = 360.00 / refinesticks.val
	dx = 0.0
	dy = 0.0
	dz = 0.0
	pi = asin(1)
	laenge = sqrt((x1-x2)*(x1-x2)+(y1-y2)*(y1-y2)+(z1-z2)*(z1-z2))
	wsz = atan2((y1-y2), (x1-x2))
	wz = acos((z1-z2)/laenge)
	
	
	# erster Punkt
	
	# Kappe	
	
	while b < 360:
		dx = radius*sin(b/90*pi)
		dy = radius*cos(b/90*pi)
		me.verts.extend(dx, dy, laenge/2)
		me.verts.extend(dx, dy, -laenge/2)
		vcount = vcount + 2
		if vcount > 2:
			me.faces.extend([me.verts[vcount],me.verts[vcount-1],me.verts[vcount-3],me.verts[vcount-2]])
			if b == 360-db:
				me.faces.extend([me.verts[0],me.verts[vcount-1],me.verts[vcount],me.verts[1]])
		b = b + db
	
	for face in me.faces:
		face.smooth=1
	
	ob.link (me)
	x1 = float(x1)
	y1 = float(y1)
	z1 = float(z1)
	x2 = float(x2)
	y2 = float(y2)
	z2 = float(z2)
	ob.loc = (float(x1+x2)/2,(y1+y2)/2,(z1+z2)/2)
	ob.RotY = wz
	ob.RotZ = wsz
	scene.link (ob)


def stick3(x1, y1, z1, type1, x2, y2, z2, type2, radius):
	global structmode, scatom, sumatom, refineballs, refinesticks, balls, sticks, scsticks
	# Objekt erstellen
	ob = Object.New('Mesh')
	# Mesh erstellen
	me = Mesh.New()
	if type1 in ['C', 'H', 'B', 'N', 'O', 'P']:
		mat = Material.Get(type1)
	else: mat = Material.Get('anyatom')
	me.materials = [mat]
	# Stick erste Haelfte erstellen
	a = 0.0000	
	b = 0.0000
	vcount = 0
	da = 360.00 / refinesticks.val
	db = 360.00 / refinesticks.val
	dx = 0.0
	dy = 0.0
	dz = 0.0
	pi = asin(1)
	laenge = sqrt((x1-x2)*(x1-x2)+(y1-y2)*(y1-y2)+(z1-z2)*(z1-z2))
	wsz = atan2((y1-y2), (x1-x2))
	wz = acos((z1-z2)/laenge)
	
	
	# erster Punkt
	me.verts.extend(0, 0, laenge/2+radius)
	a = a + da
	
	# Kappe
		
	while b < 360:
		dz = radius*cos(a/90*pi)
		dx = radius*sin(a/90*pi)*sin(b/90*pi)
		dy = radius*sin(a/90*pi)*cos(b/90*pi)
		b = b + db
		me.verts.extend(dx, dy, dz+laenge/2)
		vcount = vcount + 1
		if vcount > 1:
			me.faces.extend([me.verts[0],me.verts[vcount],me.verts[vcount-1]])
	
	me.faces.extend([me.verts[0],me.verts[1],me.verts[vcount]])
	
	b = 0
	kcount = 0
	vvcount = 0
	a = a + da
	
	
	while a < 90:
		while b < 360:
			dz = radius*cos(a/90*pi)
			dx = radius*sin(a/90*pi)*sin(b/90*pi)
			dy = radius*sin(a/90*pi)*cos(b/90*pi)
			me.verts.extend(dx, dy, dz+laenge/2)
			vcount = vcount + 1
			vvcount = vvcount + 1
			if vvcount > 1:
				me.faces.extend([me.verts[vcount],me.verts[vcount-1],me.verts[vcount-int(360/db)-1],me.verts[vcount-int(360/db)]])
				if b == 360-db:
					me.faces.extend([me.verts[vcount],me.verts[vcount-int(360/db)],me.verts[vcount-2*int(360/db)+1],me.verts[vcount-int(360/db)+1]])
			b = b + db
		kcount = kcount + 1
		b = 0
		vvcount = 0
		a = a + da
		
	a = 90
	b = 0
	vvcount = 0
	
	while b < 360:
		dx = radius*sin(b/90*pi)
		dy = radius*cos(b/90*pi)
		me.verts.extend(dx, dy, laenge/2)
		vcount = vcount + 1
		vvcount = vvcount + 1
		if vvcount > 1:
			me.faces.extend([me.verts[vcount],me.verts[vcount-1],me.verts[vcount-int(360/db)-1],me.verts[vcount-int(360/db)]])
			if b == 360-db:
				me.faces.extend([me.verts[vcount],me.verts[vcount-int(360/db)],me.verts[vcount-2*int(360/db)+1],me.verts[vcount-int(360/db)+1]])
		b = b + db
	kcount = kcount + 1
	b = 0
	vvcount = 0	
	
	while b < 360:
		dx = radius*sin(b/90*pi)
		dy = radius*cos(b/90*pi)
		me.verts.extend(dx, dy, 0)
		vcount = vcount + 1
		vvcount = vvcount + 1
		if vvcount > 1:
			me.faces.extend([me.verts[vcount],me.verts[vcount-1],me.verts[vcount-int(360/db)-1],me.verts[vcount-int(360/db)]])
			if b == 360-db:
				me.faces.extend([me.verts[vcount],me.verts[vcount-int(360/db)],me.verts[vcount-2*int(360/db)+1],me.verts[vcount-int(360/db)+1]])
		b = b + db
	kcount = kcount + 1
	b = 0
	vvcount = 0	
	
	for face in me.faces:
		face.smooth=1
	
	
	ob.link (me)
	x1 = float(x1)
	y1 = float(y1)
	z1 = float(z1)
	x2 = float(x2)
	y2 = float(y2)
	z2 = float(z2)
	ob.loc = (float(x1+x2)/2,(y1+y2)/2,(z1+z2)/2)
	ob.RotY = wz
	ob.RotZ = wsz
	scene.link (ob)
	
	#zweite Haelfte vom Stick
	ob = Object.New('Mesh')
	# Mesh erstellen
	me = Mesh.New()
	if type2 in ['C', 'H', 'B', 'N', 'O', 'P']:
		mat = Material.Get(type2)
	else: mat = Material.Get('anyatom')
	me.materials = [mat]
	vcount = -1
			
	while b < 360:
		dx = radius*sin(b/90*pi)
		dy = radius*cos(b/90*pi)
		me.verts.extend(dx, dy, 0)
		vcount = vcount + 1
		
		b = b + db
	
	kcount = kcount + 1
	b = 0
	vvcount = 0	
	
	while b < 360:
		dx = radius*sin(b/90*pi)
		dy = radius*cos(b/90*pi)
		me.verts.extend(dx, dy, -laenge/2)
		vcount = vcount + 1
		vvcount = vvcount + 1
		if vvcount > 1:
			me.faces.extend([me.verts[vcount],me.verts[vcount-1],me.verts[vcount-int(360/db)-1],me.verts[vcount-int(360/db)]])
			if b == 360-db:
				me.faces.extend([me.verts[vcount],me.verts[vcount-int(360/db)],me.verts[vcount-2*int(360/db)+1],me.verts[vcount-int(360/db)+1]])
		b = b + db
	kcount = kcount + 1
	b = 0
	vvcount = 0	
	
	while a < 180:
		while b < 360:
			dz = radius*cos(a/90*pi)
			dx = radius*sin(a/90*pi)*sin(b/90*pi)
			dy = radius*sin(a/90*pi)*cos(b/90*pi)
			me.verts.extend(dx, dy, dz-laenge/2)
			vcount = vcount + 1
			vvcount = vvcount + 1
			if vvcount > 1:
				me.faces.extend([me.verts[vcount],me.verts[vcount-1],me.verts[vcount-int(360/db)-1],me.verts[vcount-int(360/db)]])
				if b == 360-db:
					me.faces.extend([me.verts[vcount],me.verts[vcount-int(360/db)],me.verts[vcount-2*int(360/db)+1],me.verts[vcount-int(360/db)+1]])
			b = b + db
		kcount = kcount + 1
		b = 0
		vvcount = 0
		a = a + da
		
	# letzter Punkt
	me.verts.extend(0, 0, -laenge/2-radius)
	vcount = vcount + 1
	b = 0
	while b < 360-db:
		me.faces.extend([me.verts[vcount],me.verts[vcount-int(b/db)-2],me.verts[vcount-int(b/db)-1]])
		b = b + db
	
	me.faces.extend([me.verts[vcount],me.verts[vcount-1],me.verts[vcount-int((360-db)/db)-1]])
	eins = 1
	for face in me.faces:
		face.smooth=1
	
	
	ob.link (me)
	x1 = float(x1)
	y1 = float(y1)
	z1 = float(z1)
	x2 = float(x2)
	y2 = float(y2)
	z2 = float(z2)
	ob.loc = (float(x1+x2)/2,(y1+y2)/2,(z1+z2)/2)
	ob.RotY = wz
	ob.RotZ = wsz
	scene.link (ob)

def getGeomName(geom):
        g = geom
        name = "Pmv_"
        while g != geom.viewer.rootObject:
            # g.name can contain whitespaces which we have to get rid of
            gname = string.split(g.name)
            ggname = "" 
            for i in gname:
                ggname = ggname + i
            name = name + string.strip(ggname)+"AT"+\
                   string.strip(str(g.instanceMatricesIndex))+ '_'
            g = g.parent
        name=string.replace(name,"-","_")
	return name

def getMaterial(geom,bname,colorPerVertexFlag=True):
	from DejaVu.IndexedPolygons import IndexedPolygons
	from DejaVu.GleObjects import GleExtrude
        blender=[]
	#name = getGeomName(geom)
        mat = geom.materials[GL.GL_FRONT].prop[:]
        geom.materials[GL.GL_FRONT].colorIndex = None # will be used later on
        colors = None

        # if only 1 color present, skip this all and use the ambient definition
        # below
        if len(mat[1])> 1:
            colors = mat[1]

            # The ZCorp printer software doesn't support color_per_face,
            # but Pmv does. So, we create a colorIndex list for special cases
            # However, the user can still choose between coloring
            # per face and per vertex

            # FIXME: test for primitive type, i.e. tri_strip or quad_strip
            # currently this works only for tri_strips
            if isinstance(geom, GleExtrude): # special case!
                faces = geom.faceSet.faces.array # triangle_strips
                ifaces = geom.getFaces() # indexed geom

                # if the user forces to save color per vertex:
                if colorPerVertexFlag is True:
                    colorIndex = Numeric.zeros( (ifaces.shape[0], \
                                                 ifaces.shape[1]) )
                    c = 0
                    cc = 0
                    for face in faces:
                        for j in range(len(face)-2): # -2 because of tri_strip
                            colorIndex[cc] = c
                            cc = cc + 1
                        c = c + 1
                    geom.materials[GL.GL_FRONT].colorIndex = colorIndex
                    
            elif isinstance(geom, IndexedPolygons):
                mat[1]=[mat[1][0]]
                vertices = geom.getVertices()
                faces = geom.getFaces()

                # if current colors are per face:
                if len(colors) != len(vertices) and len(colors) == len(faces):
                    # if the user forces colors per vertices:
                    if colorPerVertexFlag is True:
                        colorIndex = Numeric.zeros( (faces.shape[0], \
                                                     faces.shape[1]) )
                        c = 0
                        for face in faces:
                            for f in face:
                                colorIndex[c] = c 
                            c = c + 1
                        geom.materials[GL.GL_FRONT].colorIndex = colorIndex

                # if current colors are per vertex
                else:
                    # if the user forces colors per face:
                    if colorPerVertexFlag is False:
                        # code from Michel Sanner follows (thanks Michel!):
                        vcol = geom.materials[1028].prop[1]
                        tri = geom.faceSet.faces.array
                        verts= geom.vertexSet.vertices.array
                        colors = []
                        for t in tri:
                            s1,s2,s3 = t
                            col = ( (vcol[s1][0]+vcol[s2][0]+vcol[s3][0])/3.,
                                    (vcol[s1][1]+vcol[s2][1]+vcol[s3][1])/3.,
                                    (vcol[s1][2]+vcol[s2][2]+vcol[s3][2])/3. )
                            colors.append( col)
	else : colors = [mat[1][0],]
        ambInt =  mat[0][0][0]
        difCol =  mat[1][0]
        emCol =   mat[2][0]
        specCol = mat[3][0][0]                 
        shin =    mat[4][0]
        trans =   1-mat[5][0]

	mat = Material.New("mat"+bname)
	mat.R = difCol[0]
	mat.G = difCol[1]
	mat.B = difCol[2]

	#vrml2.append("          material        Material {\n")
        #vrml2.append("            ambientIntensity      "+ambInt+"\n")
        #vrml2.append("            diffuseColor          "+difCol+"\n")
        #vrml2.append("            emissiveColor         "+emCol+"\n")
        #vrml2.append("            specularColor         "+specCol+"\n")
        #vrml2.append("            shininess             "+shin+"\n")
        #vrml2.append("            transparency          "+trans+"\n")
        #vrml2.append("          }\n")
        return mat, colors



def createsNmesh(name,vertices,vnormals,faces,color=None,smooth=False):
	vlist = []
	#mesh = Blender.Mesh.New()
	me=bpy.data.meshes.new(name)
	
	me.verts.extend(vertices)	# add vertices to mesh
	me.faces.extend(faces)          # add faces to the mesh (also adds edges)
	#smooth face : the vertex normals are averaged to make this face look smooth
	if smooth:
		for face in me.faces:
			face.smooth=1
	me.calcNormals()
	#for f in faces : 
	#    for ind in f :
	#	face=[]
	#	face.append(mesh.addVert(vertices[ind]))
	#    mesh.addFace(face1)
        mat = Material.New("mat"+name[:4])
	me.materials=[mat]
	if color != None :
		changeColor(me,color)
	ob = Blender.Object.New("Mesh","Mesh_"+name)
	ob.link(me)
	return ob,me

def blenderColor(col):
	    if max(col)<=1.0: col = [x*255 for x in col]
	    return col


def changeColor(mesh,colors,perVertex=True):
	mesh.vertexColors = 1  # enable vertex colors
	#verfify perVertex flag
	if len(colors) != len(mesh.verts) and len(colors) == len(mesh.faces): perVertex=False
	if len(colors) == len(mesh.verts) and len(colors) != len(mesh.faces): perVertex=True
	unic=False
	ncolor=None
	if len(colors)==1 : 
		#print colors	
		unic=True
		ncolor = blenderColor(colors[0])
	for f in mesh.faces:
		if not unic and not perVertex : ncolor = blenderColor(colors[f.index])
		for i, v in enumerate(f):
			col= f.col[i]
			if not unic and perVertex : ncolor = blenderColor(colors[v.index])
			col.r= int(ncolor[0])
			col.g= int(ncolor[1])
			col.b= int(ncolor[2])
		mesh.materials[0].setMode("VColPaint")
	if unic :
		mesh.materials[0].R=int(ncolor[0])
		mesh.materials[0].G=int(ncolor[1])
		mesh.materials[0].B=int(ncolor[2])

def changeSticksColor(mesh,colors):#1 or 2 colors
	mesh.vertexColors = 1  # enable vertex colors
	unic=False
	ncolor=None
	if len(colors)==1 : 
		#print colors	
		unic=True
		ncolor = blenderColor(colors[0])
	nbV=len(mesh.verts)
 	split=(nbV-2)/2
	a=list(range(0,split))
	b=list(range(split,(nbV-2)))
	for f in mesh.faces:
		for i, v in enumerate(f):
			col= f.col[i]
			if not unic : 
			  if v.index in a or v.index == (nbV-2):    ncolor = blenderColor(colors[0])
			  elif 	v.index in b or v.index == (nbV-1): ncolor = blenderColor(colors[1])
			col.r= int(ncolor[0])
			col.g= int(ncolor[1])
			col.b= int(ncolor[2])
	mesh.materials[0].setMode("VColPaint")
	if unic :
		mesh.materials[0].R=int(ncolor[0])
		mesh.materials[0].G=int(ncolor[1])
		mesh.materials[0].B=int(ncolor[2])

def atomPropToVertices(obj,name,srf,atoms, propName, propIndex=None):#propIndex:surfName
        """Function called to map atomic properties to the vertices of the
        geometry"""
        if len(atoms)==0: return None

        geomC = obj
        surfName = name
        surf = srf
        surfNum = 1
        # array of colors of all atoms for the msms.
        prop = []
        if propIndex is not None:
            for a in geomC.msmsAtoms.data:
                d = getattr(a, propName)
                prop.append( d[surfName] )
        else:
            for a in geomC.msmsAtoms.data:
                prop.append( getattr(a, propName) )
        # find indices of atoms with surface displayed
        atomIndices = []
        indName = '__surfIndex%d__'%surfNum
        for a in atoms.data:
            atomIndices.append(getattr(a, indName))
        # get the indices of closest atoms
        dum1, vi, dum2 = surf.getTriangles(atomIndices, keepOriginalIndices=1)
        # get lookup col using closest atom indicies
        mappedProp = Numeric.take(prop, vi[:, 1]-1).astype('f')
        if hasattr(obj,'apbs_colors'):
            colors = []
            for i in range(len(geom.apbs_dum1)):
                ch = geom.apbs_dum1[i] == dum1[0]
                if not 0 in ch:
                    tmp_prop = mappedProp[0]
                    mappedProp = mappedProp[1:]
                    dum1 = dum1[1:]
                    if    (tmp_prop[0] == [1.5]) \
                      and (tmp_prop[1] == [1.5]) \
                      and (tmp_prop[2] == [1.5]):
                        colors.append(geom.apbs_colors[i][:3])
                    else:
                        colors.append(tmp_prop)
                    if dum1 is None:
                        break
            mappedProp = colors            
        return mappedProp


def coarseMolSurface(mv,molFrag,XYZd,isovalue=7.0,resolution=-0.3,padding=0.0,name='CoarseMolSurface'):
	from MolKit.molecule import Atom
	atoms = molFrag.findType(Atom)
	coords = atoms.coords
	radii = atoms.vdwRadius
	from UTpackages.UTblur import blur
	import numpy.oldnumeric as Numeric
	volarr, origin, span = blur.generateBlurmap(coords, radii, XYZd,resolution, padding = 0.0)
        volarr.shape = (XYZd[0],XYZd[1],XYZd[2])
        volarr = Numeric.ascontiguousarray(Numeric.transpose(volarr), 'f')
	#print volarr

	weights =  Numeric.ones(len(radii), typecode = "f")
	h = {}
	from Volume.Grid3D import Grid3DF
    	maskGrid = Grid3DF( volarr, origin, span , h)
	h['amin'], h['amax'],h['amean'],h['arms']= maskGrid.stats()
	#(self, grid3D, isovalue=None, calculatesignatures=None, verbosity=None)
	from UTpackages.UTisocontour import isocontour
       	isocontour.setVerboseLevel(0)

	data = maskGrid.data

        origin = Numeric.array(maskGrid.origin).astype('f')
        stepsize = Numeric.array(maskGrid.stepSize).astype('f')
        # add 1 dimension for time steps amd 1 for multiple variables
        if data.dtype.char!=Numeric.Float32:
            print('converting from ', data.dtype.char)
            data = data.astype('f')#Numeric.Float32)

        newgrid3D = Numeric.ascontiguousarray(Numeric.reshape( Numeric.transpose(data),
                                          (1, 1)+tuple(data.shape) ), data.dtype.char)
           
        ndata = isocontour.newDatasetRegFloat3D(newgrid3D, origin, stepsize)

 
        isoc = isocontour.getContour3d(ndata, 0, 0, isovalue,
                                       isocontour.NO_COLOR_VARIABLE)
        vert = Numeric.zeros((isoc.nvert,3)).astype('f')
        norm = Numeric.zeros((isoc.nvert,3)).astype('f')
        col = Numeric.zeros((isoc.nvert)).astype('f')
        tri = Numeric.zeros((isoc.ntri,3)).astype('i')
        isocontour.getContour3dData(isoc, vert, norm, col, tri, 0)
	#print vert

        if maskGrid.crystal:
            vert = maskGrid.crystal.toCartesian(vert)
	
	from DejaVu.IndexedGeom import IndexedGeom
	from DejaVu.IndexedPolygons import IndexedPolygons
	g=IndexedPolygons(name=name)
	#print g
	inheritMaterial = None
	g.Set(vertices=vert, faces=tri, materials=None, 
              tagModified=False, 
              vnormals=norm, inheritMaterial=inheritMaterial )
	mv.bindGeomToMolecularFragment(g, atoms, log=0)
	#print len(g.getVertices())
	return g
        #GeometryNode.textureManagement(self, image=image, textureCoordinates=textureCoordinates)


def msms(nodes, surfName='MSMS-MOL', pRadius=1.5, density=1.0,
             perMol=True, display=True,  hdensity=6.0):
        """Required Arguments:\n        
        nodes   ---  current selection\n
        surfName --- name of the surfname which will be used as the key in
                    mol.geomContainer.msms dictionary.\n
        \nOptional Arguments:  \n      
        pRadius  --- probe radius (1.5)\n
        density  --- triangle density to represent the surface. (1.0)\n
        perMol   --- when this flag is True a surface is computed for each 
                    molecule having at least one node in the current selection
                    else the surface is computed for the current selection.
                    (True)\n
        display  --- flag when set to True the displayMSMS will be executed with
                    the surfName else not.\n
        hdset    --- Atom set for which high density triangualtion 
                     will be generated
        hdensity --- vertex density for high density
        """
        from mslib import MSMS
        if nodes is None or not nodes:
            return
        # Check the validity of the input
        if not type(density) in [int, float] or \
           density < 0: return 'ERROR'
        if not type(pRadius) in [int, float] or \
           pRadius <0: return 'ERROR'
              
        # get the set of molecules and the set of atoms per molecule in the
        # current selection
        if perMol:
            molecules = nodes.top.uniq()
            atmSets = [x.allAtoms for x in molecules]
	     
        #else:
        #    molecules, atmSets = self.vf.getNodesByMolecule(nodes, Atom)

        for mol, atms in map(None, molecules, atmSets):
            if not surfName:
                surfName = mol.name + '-MSMS'
            # update the existing geometry
	    print(mol)
            for a in mol.allAtoms:
                    a.colors[surfName] = (1.,1.,1.)
                    a.opacities[surfName] = 1.0
            i=0  # atom indices are 1-based in msms
            indName = '__surfIndex%d__'% 1
            hd = []
            surf = []
	    atmRadii=[]
            for a in atms:
                setattr(a, indName, i)
                i = i + 1
                surf.append(1)
                hd.append(0)
            	atmRadii.append(a.vdwRadius)
            # build an MSMS object and compute the surface
            srf = MSMS(coords=atms.coords, radii=atmRadii, surfflags=surf,
                       hdflags=hd )
            srf.compute(probe_radius=pRadius, density=density,
                        hdensity=hdensity)
	    vf, vi, f = srf.getTriangles()
	    vertices=vf[:,:3]
	    vnormals=vf[:,3:6]
	    faces=f[:,:3]
	    ob,mesh=createsNmesh(surfName,vertices,vnormals,faces)
	    surface=Surface(mesh,ob,surfName,mol.allAtoms,srf)
        return surface

def expandNodes(nodes,mols):
        """Takes nodes as string or TreeNode or TreeNodeSet and returns
a TreeNodeSet
If nodes is a string it can contain a series of set descriptors with operators
separated by / characters.  There is always a first set, followed by pairs of
operators and sets.  All sets ahve to describe nodes of the same level.

example:
    '1crn:::CA*/+/1crn:::O*' describes the union of all CA ans all O in 1crn
    '1crn:::CA*/+/1crn:::O*/-/1crn::TYR29:' 
"""	
	from MolKit.stringSelector import CompoundStringSelector
	from MolKit.tree import TreeNode, TreeNodeSet

        if isinstance(nodes,TreeNode):
            result = nodes.setClass([nodes])
            result.setStringRepr(nodes.full_name())

        elif type(nodes)==StringType:
            stringRepr = nodes
            css = CompoundStringSelector()
            result = css.select(mols, stringRepr)[0]
##            setsStrings = stringRepr.split('/')
##            getSet = self.Mols.NodesFromName
##            result = getSet(setsStrings[0])
##            for i in range(1, len(setsStrings), 2):
##                op = setsStrings[i]
##                arg = setsStrings[i+1]
##                if op=='|': # or
##                    result += getSet(arg)
##                elif op=='-': # subtract
##                    result -= getSet(arg)
##                elif op=='&': # intersection
##                    result &= getSet(arg)
##                elif op=='^': # xor
##                    result ^= getSet(arg)
##                elif op=='s': # sub select (i.e. select from previous result)
##                    result = result.get(arg)
##                else:
##                    raise ValueError, '%s bad operation in selection string'%op
##            result.setStringRepr(stringRepr)

        elif isinstance(nodes,TreeNodeSet):
            result = nodes
        else:
            raise ValueError('Could not expand nodes %s\n'%str(nodes))
        
        return result

def colorByAtomType(nodes,obj):
	from Pmv.pmvPalettes import AtomElements
	#from Pmv.colorPalette import ColorPalette, ColorPaletteFunction
	
	c = 'Color palette for atom type'
	palette = ColorPalette('AtomElements', colorDict=AtomElements,
                                    readonly=0, info=c,
                                    lookupMember='element')
	
	#molecules, nodes = self.getNodes(nodes)
	#molecules, atms, nodes = self.getNodes(nodes, returnNodes=True)
	molecules = nodes.top.uniq()
	atms = [x.allAtoms for x in molecules]
	#nodes = expandNodes(nodes,molecules)

	colors = palette.lookup( atms[0] )
	#print colors
	
	for a, c in map(None, atms[0], colors):
		a.colors[obj.name] = tuple(c)
	"""
        if len(colors)==len(nodes) and not isinstance(nodes[0], Atom):
            #expand colors from nodes to atoms
            newcolors = []
            for n,c in map(None,nodes,colors):
                newcolors.extend( [c]*len(n.findType(Atom)) )
            colors = newcolors
            
        if len(colors)==1 or len(colors)!=len(atms):
                for a in atms:
                    if not a.colors.has_key(obj.name): continue
                    a.colors[obj.name] = tuple( colors[0] )
        else:
                for a, c in map(None, atms, colors):
                    if not a.colors.has_key(obj.name): continue
                    #a.colors[g] = tuple(c[:3])
                    a.colors[obj.name] = tuple(c)
	"""
	#vcolors=atomPropToVertices(obj,obj.name,obj.msmsSurf,obj.msmsAtoms,'colors',propIndex=obj.name)
	#changeColor(obj.mesh,vcolors)

def lookupDGFunc(atom):
        assert isinstance(atom, Atom)
        if atom.name in ['HN']:
            atom.atomId = atom.name
        else:
            atom.atomId=atom.parent.type+atom.name
        if atom.atomId not in DGatomIds: 
            atom.atomId=atom.element
        return atom.atomId


def colorByDG(nodes,obj):
	#from Pmv.colorPalette import ColorPalette, ColorPaletteFunction
	from Pmv.pmvPalettes import DavidGoodsell, DavidGoodsellSortedKeys
	c = 'Color palette for DG'
        palette = ColorPaletteFunction('DavidGoodsell',
                                            DavidGoodsell, readonly=0,
                                            info=c,
                                            sortedkeys=DavidGoodsellSortedKeys,
                                            lookupFunction=lookupDGFunc)

	#molecules, nodes = self.getNodes(nodes)
	#molecules, atms, nodes = self.getNodes(nodes, returnNodes=True)
	molecules = nodes.top.uniq()
	atms = [x.allAtoms for x in molecules]
	#nodes = expandNodes(nodes,molecules)

	colors = palette.lookup( atms[0] )
	#print colors
	
	for a, c in map(None, atms[0], colors):
		a.colors[obj.name] = tuple(c)
	#vcolors=atomPropToVertices(obj,obj.name,obj.msmsSurf,obj.msmsAtoms,'colors',propIndex=obj.name)
	#changeColor(obj.mesh,vcolors)

def colorByResidueType(nodes,obj):
        from Pmv.pmvPalettes import RasmolAmino, RasmolAminoSortedKeys
        c = 'Color palette for Rasmol like residues types'
        palette = ColorPalette('RasmolAmino', RasmolAmino, readonly=0,
                                    info=c,
                                    sortedkeys = RasmolAminoSortedKeys,
                                    lookupMember='type')


	#molecules, nodes = self.getNodes(nodes)
	#molecules, atms, nodes = self.getNodes(nodes, returnNodes=True)
	molecules = nodes.top.uniq()
	atms = [x.allAtoms for x in molecules]
	#nodes = expandNodes(nodes,molecules)
        print(nodes.findType(Residue))
	colors = palette.lookup( nodes.findType(Residue) )
	#print colors
	
	for r, c in map(None, nodes.findType(Residue), colors):
            for a in r.atoms :
		a.colors[obj.name] = tuple(c)
	#vcolors=atomPropToVertices(obj,obj.name,obj.msmsSurf,obj.msmsAtoms,'colors',propIndex=obj.name)
	#changeColor(obj.mesh,vcolors)

def color(Type,nodes,obj):
	if Type == "AtomType" : colorByAtomType(nodes,obj)
	if Type == "DG" : colorByDG(nodes,obj)
	if Type == "ResidueType" : colorByResidueType(nodes,obj)
	#else : return
	if obj.name[0:8]=='MSMS-MOL' : 
		vcolors=atomPropToVertices(obj,obj.name,obj.msmsSurf,obj.msmsAtoms,'colors',propIndex=obj.name)
		changeColor(obj.mesh,vcolors)
	else :
		atoms=nodes.findType(Atom)
		k=0
		for o,me in map(None,obj.b_obj,obj.mesh):#blender object and mesh
			vcolors = [atoms[k].colors[obj.name],] #(0,0,0)
			changeColor(me,vcolors)
			k=k+1




def prepareMesh2Pmv(mesh,molname=None):
	print("Dans PrepareMesh")
	msg=""
	msg+='from DejaVu.IndexedGeom import IndexedGeom\n'
	msg+='from DejaVu.IndexedPolygons import IndexedPolygons\n'
	msg+='import numpy.oldnumeric as Numeric\n'
	msg+='g=IndexedPolygons(name="'+mesh.name+'")\n'
	msg+='inheritMaterial = None\n'
	
	#vertex and vnormal array
	print("vertex")
	vnorm='vnorm=Numeric.array([\n'
	vert='verts=Numeric.array([\n'
	for v in mesh.verts :
		vert+='['+str(v.co[0])+','+str(v.co[1])+','+str(v.co[2])+'],\n'
		vnorm+='['+str(v.no[0])+','+str(v.no[1])+','+str(v.no[2])+'],\n'
	vert+='])\n\n'
	vnorm+='])\n\n'
	msg+=vert
	msg+=vnorm	
	print(vert)
	print("Face")
	#faces array
	faces='faces=Numeric.array([\n'
	for f in mesh.faces :
	    ind=[]
	    for i, v in enumerate(f):
		ind.append(v.index)
	    faces+=str(ind)+',\n'
	faces+='])\n\n'
	msg+=faces
	print(faces)
	#set the dejavu geom
	msg+='g.Set(vertices=verts, faces=faces, materials=None, tagModified=False,vnormals=vnorm, inheritMaterial=None)\n'
	#if a molecule name is provided, call the bindGeomToMol command
	if molname != None :
		msg+='molFrag=self.getMolFromName("'+molname+'",log=0)\n'
		msg+='from MolKit.molecule import Atom\n'
		msg+='atoms = molFrag.findType(Atom)\n'
		msg+='self.bindGeomToMolecularFragment(g, atoms, log=0)\n'
	msg+='self.GUI.VIEWER.AddObject(g)\n'
	return msg


