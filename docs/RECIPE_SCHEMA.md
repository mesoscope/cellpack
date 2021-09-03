# Cellpack Recipe Schema 1.0
## Recipe definition properties

### name

_Required string._

Unique recipe name

### version

_Required string._

Version of the recipe


#### example of recipe definition:

```JSON
"recipe": {
    "version": "1.0",
    "name": "NM_Analysis_FigureA"
    },
```
----

## Options properties

### cancelDialog

_boolean_

### hackFreepts

### windowsSize
_number_

### use_gradient

_Optional boolean_

### placeMethod

_Optional enum_. One of `"RAPID"`, `"jitter"`, `"spheresBHT"`, `"pandaBullet"`_

Will be use if placeMethod isn't in an ingredient setup

`"RAPID"` uses ["Robust and Accurate Polygon Interference Detection (RAPID)"](http://gamma.cs.unc.edu/OBB/) to test if the ingredient being placed in the packing loop is colliding with any neighboring objects fed into the list of neighbors.


`"jitter"` uses a simple algorithm developed by GJ, M-A-A, MS, and LA to test if a single sphere, sphere-tree, or other primative (box and cylinder) are colliding with masked/unallowed points on the grid... I can't recall all of the allowed types, but check the input parameters that it accepts. I believe there is also an option to perform simple collisions directly between primatives, e.g. sphere-sphere, sphere-box, sphere-cylinder, cylinder-box, and spheretree-others

`"spheresBHT"` gets the sphereTrees of the potential colliding neighbors, and does an efficient sphereTree-sphereTree collision detection of the sphereTree for the object being packed against the sphereTrees of each neighbor- returns false if a collision is detected

`"pandaBullet"`  Python wrapper for Bullet Physics Engine (popular in ~2010 and used by C4D, Maya, Blender, etc) that provides a variety of object-object collision detection, including collision min/max overlap distance, etc. Allows relaxation in its own loop, springs, rejection, meshes, primitives, etc.


### saveResult
_boolean_

### runTimeDisplay
_boolean_

### overwritePlaceMethod
_boolean_
if==true, the Enviro-level placeMethod will overwrite all of the ingredient-level place method in a recipe

### innerGridMethod
_enum_. One of `"bhtree"`, `"jordan"`, `"sdf"`, `"jordan3"`, `"pyray"`, `"floodfill"`, `"binvox"`, `"trimesh"`, `"scanline"`
 `"bhtree"`
 
 `"jordan"`

`"sdf"`

 `"jordan3"`
 
 `"pyray"`
 
 `"floodfill"`
 
 `"binvox"`
 
 `"trimesh"`
 
 `"scanline"`

### boundingBox 
_Required [[number, number, number], [number, number, number]]_

An array of two points that define the corners of the bounding box.

### gradients 
_Optional string[]_

An array that defines the names of directional gradients to use.

### smallestProteinSize
_Required number_

### computeGridParams
_boolean_

### freePtsUpdateThreshold
_number_
### pickWeightedIngr
_boolean_
### \_timer
_boolean_
### ingrLookForNeighbours
_boolean_
### pickRandPt
_boolean_
### largestProteinSize
_Required number_

### resultfile
_Optional string_

Location of publicly hosted packing result 

### use_periodicity
_boolean_

Whether to consider periodicity when packing objects. If `true` a packed object at the edge of the bounding will wrap to the other side of the bounding box. 

### EnviroOnly
_boolean_
expect no compartments, only a bounding box volume

example Options:
```JSON
"options": {
    "cancelDialog": false,
    "\_hackFreepts": false,
    "windowsSize": 10,
    "use_gradient": false,
    "placeMethod": "RAPID",
    "saveResult": false,
    "runTimeDisplay": false,
    "overwritePlaceMethod": true,
    "innerGridMethod": "bhtree",
    "boundingBox": [[0, 0, 0],[1000, 1000, 1]],
    "gradients": [],
    "smallestProteinSize": 0,
    "computeGridParams": true,
    "freePtsUpdateThreshold": 0,
    "pickWeightedIngr": true,
    "\_timer": false,
    "ingrLookForNeighbours": false,
    "pickRandPt": false,
    "largestProteinSize": 200,
    "resultfile": "autoPACKserver/results/NM_Analysis_FigureA1.0.apr.json",
    "use_periodicity": false,
    "EnviroOnly": false
},
```
---


## Ingredient Properties
### overwrite_nbMol_value 
_Optional number_

not sure different with nbMol, might be a complete override, not additive with molarity
### nbJitter
_Required number_

How many times it will attempts to pack before rejecting the ingredient
### molarity
_Optional number_

Concentration. Will default to 0
### partners_position
_Optional number[][]_
### rotRange
_number_

### color
_[number, number, number]_
### meshFile
_Optional string_

Location of mesh file 

### sphereFile
_Optional string_

Location of sphere file 

### weight
_number_
### orientBiasRotRangeMin
_number_
### radii
_Optional number[][]_

Property of a primitive sphere

### cutoff_boundary
_number_
### coordsystem
_Optional enum. One of `"left"` `"right"`._

### jitterMax
_Optional [number, number, number]_

The amount this ingredient can move in x, y and z. If z is set to 0, will be a 2D packing. Defaults to `[1, 1, 1]`
### perturbAxisAmplitude
_number_
### encapsulatingRadius
_Required number_

Smallest radius that completely includes all the geometry. 

### positions2
_Optional_
### useOrientBias
_Optional boolean_
### gradient
### isAttractor
_Optional boolean_
### principalVector
_[number, number, number]_
### properties
_Optional object_
### partners_name
_Optional string[]_
### nbMol
_Optional number_

Number to pack, additive with molarity. 

### name
_Required string_
Name of the ingredient
### orientBiasRotRangeMax
_number_
### packingMode
_Optional enum. One of `"random"`,_
### Type
_Optional enum. One of `"SingleSphere"`,`"SingleCube"`,`"MultiSphere"`,`"MultiCylinder"`,`"Grow"`,`"Mesh"`_

`"SingleSphere"`

`"SingleCube"`

`"MultiSphere"`

`"MultiCylinder"`

`"Grow"`: A spline ingredient

`"Mesh"`

### excluded_partners_name
_Optional string[]_
### rejectionThreshold
_number_

### placeType
_Optional enum. One of `"RAPID"`, `"jitter"`, `"spheresBHT"`, `"pandaBullet"`_

`"RAPID"` uses ["Robust and Accurate Polygon Interference Detection (RAPID)"](http://gamma.cs.unc.edu/OBB/) to test if the ingredient being placed in the packing loop is colliding with any neighboring objects fed into the list of neighbors.


`"jitter"` uses a simple algorithm developed by GJ, M-A-A, MS, and LA to test if a single sphere, sphere-tree, or other primative (box and cylinder) are colliding with masked/unallowed points on the grid... I can't recall all of the allowed types, but check the input parameters that it accepts. I believe there is also an option to perform simple collisions directly between primatives, e.g. sphere-sphere, sphere-box, sphere-cylinder, cylinder-box, and spheretree-others

`"spheresBHT"` gets the sphereTrees of the potential colliding neighbors, and does an efficient sphereTree-sphereTree collision detection of the sphereTree for the object being packed against the sphereTrees of each neighbor- returns false if a collision is detected

`"pandaBullet"`  Python wrapper for Bullet Physics Engine (popular in ~2010 and used by C4D, Maya, Blender, etc) that provides a variety of object-object collision detection, including collision min/max overlap distance, etc. Allows relaxation in its own loop, springs, rejection, meshes, primitives, etc.

### cutoff_surface
_number_
### packingPriority
_Optional number_

Order to pack, largest negative number gets packed first. 

### proba_binding
_number_ 
### rotAxis
_Optional_
### positions
_[number, number, number][]
### proba_not_binding
_number_
### use_mesh_rb
_boolean_
### pdb
_Optional string_

PDB id in the protein database

### useRotAxis
_boolean_


### example ingredient
```JSON
"Sphere_radius_100": {
    "overwrite_nbMol_value": 6, 
    "nbJitter": 6, 
    "molarity": 0,
    "partners_position": [],
    "rotRange": 6.2831,
    "color": [ 0.498, 0.498, 0.498 ],
    "meshFile": null,
    "sphereFile": null,
    "weight": 0.2,
    "orientBiasRotRangeMin": -3.1415927,
    "radii": [[100]], 
    "cutoff_boundary": 0,
    "coordsystem": "left",
    "jitterMax": [ 1, 1, 0], 
    "perturbAxisAmplitude": 0.1,
    "encapsulatingRadius": 100,
    "positions2": null,
    "useOrientBias": false,
    "gradient": "",
    "isAttractor": false,
    "principalVector": [ 1, 0, 0 ],
    "properties": {},
    "partners_name": [],
    "nbMol": 6, 
    "name": "Sphere_radius_100",
    "orientBiasRotRangeMax": -3.1415927,
    "packingMode": "random",
    "Type": "SingleSphere", 
    "excluded_partners_name": [],
    "rejectionThreshold": 60,
    "placeType": "jitter",
    "cutoff_surface": 100,
    "packingPriority": 0, 
    "proba_binding": 0.5,
    "rotAxis": null,
    "positions": [ [ [ 0, 0, 0] ] ],
    "proba_not_binding": 0.5,
    "use_mesh_rb": false,
    "pdb": null,
    "useRotAxis": false
},

```


