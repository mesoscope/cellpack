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


### saveResult
_Optional boolean_ Defaults to `false`. 

Save packing result to .apr file.

### resultfile
_Optional string_

Location of publicly hosted packing result 

### EnviroOnly
_Optional boolean_ Defaults to `false`.

Expect no compartments, only a bounding box volume

### cancelDialog
_Optional boolean_ Defaults to `false`. 

### pickWeightedIngr
_Optional boolean_ Defaults to `true`. 

Prioritize ingredient selection by packingWeight.

### pickRandPt
_Optional boolean_ Defaults to `true`.

Pick drop position point randomly.

### ingrLookForNeighbours
_Optional boolean_ Defaults to `false`. 

Look for ingredients attractor and partner.

### overwritePlaceMethod
_Optional boolean_ Defaults to `true`. 
If `true`, the Enviro-level placeMethod will overwrite all of the ingredient-level place method in a recipe


### boundingBox 
_Optional [[number, number, number], [number, number, number]]_ Defaults to `[0, 0, 0], [0.1, 0.1, 0.1]`.

An array of two points that define the corners of the bounding box.

### smallestProteinSize
_Optional number_ Defaults to `15`. 

Smallest ingredient packing radius override (low=accurate | high=fast). As with largestProteinSize, if not defined, this value will be calculated by the algorithm based on the spheretree input file (packing radius) or the packingRadius calculated from ingredients that use primitives for their geometries.

### largestProteinSize
_Optional number_

As with smallestProteinSize, if not defined, this value will be calculated by the algorithm based on the spheretree input file (packing radius) or the packingRadius calculated from ingredients that use primitives for their geometries.

### computeGridParams
_Optional boolean_ Defaults to `true`.

### windowsSize
_Optional number_ Defaults to `100`.

### runTimeDisplay
_Optional boolean_ Defaults to `false`.

Display packing in realtime (slow)

### placeMethod

_Optional enum_. One of `"RAPID"`, `"jitter"`, `"spheresBHT"`, `"pandaBullet"`. Defaults to `"jitter"`.

Will be use if placeMethod isn't in an ingredient setup

`"RAPID"` uses ["Robust and Accurate Polygon Interference Detection (RAPID)"](http://gamma.cs.unc.edu/OBB/) to test if the ingredient being placed in the packing loop is colliding with any neighboring objects fed into the list of neighbors.

`"jitter"` uses a simple algorithm developed by GJ, M-A-A, MS, and LA to test if a single sphere, sphere-tree, or other primative (box and cylinder) are colliding with masked/unallowed points on the grid... I can't recall all of the allowed types, but check the input parameters that it accepts. I believe there is also an option to perform simple collisions directly between primatives, e.g. sphere-sphere, sphere-box, sphere-cylinder, cylinder-box, and spheretree-others

`"spheresBHT"` gets the sphereTrees of the potential colliding neighbors, and does an efficient sphereTree-sphereTree collision detection of the sphereTree for the object being packed against the sphereTrees of each neighbor- returns false if a collision is detected

`"pandaBullet"`  Python wrapper for Bullet Physics Engine (popular in ~2010 and used by C4D, Maya, Blender, etc) that provides a variety of object-object collision detection, including collision min/max overlap distance, etc. Allows relaxation in its own loop, springs, rejection, meshes, primitives, etc.

### use_gradient
_Optional boolean_ Defaults to `false`.

Use gradients if they are defined. 

### gradients 
_Optional string[]_

An array that defines the names of directional gradients to use.

### innerGridMethod
_enum_. One of `"bhtree"`, `"jordan"`, `"sdf"`, `"jordan3"`, `"pyray"`, `"floodfill"`, `"binvox"`, `"trimesh"`, `"scanline"`. Defaults to `"jordan3"`.


 `"bhtree"` build sthe compartment grid ie surface and inside point using bhtree.
 
 `"jordan"` builds the compartment grid ie surface and inside point using jordan theorem and host raycast.  Only computes the inner point. No grid.
        This is independent from the packing. Help build ingredient sphere tree and representation.
        - Uses BHTree to compute surface points
        - Uses Jordan raycasting to determine inside/outside (defaults to 1 iteration, can use 3 iterations)
        

`"sdf"` builds the compartment grid ie surface and inside point using signed distance fields
        from the UT package.
        

 `"jordan3"` builds the compartment grid ie surface and inside point using jordan theorem and host raycast, with ray set to `3`.
 
 `"pyray"`
 
 `"floodfill"` builds the compartment grid ie surface and inside point using flood filling algo from kevin. Takes a polyhedron, and builds a grid. In this grid:
            - Projects the polyhedron to the grid.
            - Determines which points are inside/outside the polyhedron
            - Determines point's distance to the polyhedron.
        superFine provides the option doing a super leakproof test when determining
        which points are inside or outside. Instead of raycasting to nearby faces to
        determine inside/outside, setting this setting to true will force the algorithm
        to raycast to the entire polyhedron. This usually not necessary, because the
        built-in algorithm has no known leakage cases, even in extreme edge cases.
        It is simply there as a safeguard.
 
 `"binvox"` 
 
 `"trimesh"` 
 
 `"scanline"` builds the compartment grid ie surface and inside point using scanline.

### freePtsUpdateThreshold
_Optional number_ Defaults to `0.0`.

Mask grid while packing (0=always | 1=never)

### use_periodicity
_Optional boolean_ Defaults to `false`. 

Whether to consider periodicity when packing objects. If `true` a packed object at the edge of the bounding will wrap to the other side of the bounding box. 

### _timer
_Optional boolean_ Defaults to `false`.

Evaluate time per function.

### _hackFreepts
_Optional boolean_ Defaults to `false`.

no free point update

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

### name
_Required string_

Name of the ingredient.

### overwrite_nbMol_value 
_Optional number_ Defaults to `0`.

A complete override of concentration and nbMol, not additive with molarity.

### molarity
_Optional number_ Defaults to `0`.

Concentration of the ingredient. 

### nbMol
_Optional number_

Number to pack, additive with molarity. Defaults to `0`. 

### encapsulatingRadius
_Optional number_ Defaults to `5`.

Smallest radius that completely includes all the geometry. 

### radii
_Optional number[][]_

Property of a primitive sphere. 

### positions
_Optional [number, number, number][]_

### positions2
_Optional [number, number, number][]_

### sphereFile
_Optional string_

Location of sphere file 

### packingPriority
_Optional number_ Default to `0.0`.

Order to pack, largest negative number gets packed first. 

### pdb
_Optional string_

PDB id in the protein database

### color
_[number, number, number]_

### meshFile
_Optional string_

Location of mesh file 

### meshName
_Optional string_

Name of the mesh file. 

### coordsystem
_Optional enum. One of `"left"` `"right"`._ Defaults to `"left"`.

### principalVector
_[number, number, number]_ Defaults to `[0.0, 0.0, 0.0]`.

### Type
_Optional enum. One of `"SingleSphere"`,`"SingleCube"`,`"MultiSphere"`,`"MultiCylinder"`,`"Grow"`,`"Mesh"`_

`"SingleSphere"`

`"SingleCube"`

`"MultiSphere"`

`"MultiCylinder"`

`"Grow"`: A spline ingredient

`"Mesh"`

### offset 
_Optional [number, number, number]_ Defaults to `[0.0, 0.0, 0.0]`.

### jitterMax
_Optional [number, number, number]_ Defaults to `[1, 1, 1]`.

### nbJitter
_Required number_  Defaults to `5`.

How many times it will attempts to pack before rejecting the ingredient.

### perturbAxisAmplitude
_Optional number_ Defaults to `0.1`.

### useRotAxis
_Optional boolean_ Defaults to `false`.

### rotAxis 
_Optional [number, number, number]_ Defaults to `[0.0, 0.0, 0.0]`.

### rotRange
_Optional number_ Defaults to `6.2831`.

### useOrientBias
_Optional boolean_ Defaults to `false`.

### orientBiasRotRangeMin
_Optional number_ Defaults to `-pi`.

### orientBiasRotRangeMax
_number_ Defaults to `pi`.

### cutoff_boundary
_Optional number_ Defaults to `1.0`.

The amount this ingredient can move in x, y and z. If z is set to 0, will be a 2D packing. 

### cutoff_surface
_Optional number_ Defaults to `5.0`.

### placeType
_Optional enum. One of `"RAPID"`, `"jitter"`, `"spheresBHT"`, `"pandaBullet"`_. Defaults to `"jitter"`.

`"RAPID"` uses ["Robust and Accurate Polygon Interference Detection (RAPID)"](http://gamma.cs.unc.edu/OBB/) to test if the ingredient being placed in the packing loop is colliding with any neighboring objects fed into the list of neighbors.


`"jitter"` uses a simple algorithm developed by GJ, M-A-A, MS, and LA to test if a single sphere, sphere-tree, or other primative (box and cylinder) are colliding with masked/unallowed points on the grid... I can't recall all of the allowed types, but check the input parameters that it accepts. I believe there is also an option to perform simple collisions directly between primatives, e.g. sphere-sphere, sphere-box, sphere-cylinder, cylinder-box, and spheretree-others

`"spheresBHT"` gets the sphereTrees of the potential colliding neighbors, and does an efficient sphereTree-sphereTree collision detection of the sphereTree for the object being packed against the sphereTrees of each neighbor- returns false if a collision is detected

`"pandaBullet"`  Python wrapper for Bullet Physics Engine (popular in ~2010 and used by C4D, Maya, Blender, etc) that provides a variety of object-object collision detection, including collision min/max overlap distance, etc. Allows relaxation in its own loop, springs, rejection, meshes, primitives, etc.

### use_mesh_rb
_Optional boolean_ Defaults to `false`.

### rejectionThreshold
_Optional number_ Defaults to `30`.

### packingMode
_Optional enum. One of `"random"`, `"close"`, `"closePartner"`, `"randomPartner"`, `"gradient"`, `"hexatile"`, `"squaretile"`, `"triangletile"`_ Defaults to `"random"`.

### gradient
_Optional_ 
Gradient name to use if `use_gradient` is `true`. 

### proba_binding
_Optional number between `0` and `1`_ Defaults to `0.5`.

### proba_not_binding
_number_

### isAttractor
_Optional boolean_ Defaults to `false`.

### weight
_Optional number_ Defaults to `0.2`.

### partners_name
_Optional string[]_

### excluded_partners_name
_Optional string[]_

### partners_position
_Optional number[][]_

### partners_weight
_Optional number_ Defaults to `0.5`.

### properties
_Optional object_ Defaults to `{}`.

### score
_Optional string_

### organism
_Optional string_

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


