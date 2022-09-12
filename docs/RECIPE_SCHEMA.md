# Cellpack Recipe Schema 1.0
## Recipe definition properties

### name

_Required string._

Unique recipe name

### version

_Required string._

Version of the recipe


#### example:

```JSON
"recipe": {
    "version": "1.0",
    "name": "NM_Analysis_FigureA"
    },
```
----

## Options properties


### saveResult
_Optional `boolean`_. Default: `false`. 

Save packing result to .apr file.

### resultfile
_Optional `string`_.

Location of publicly hosted packing result 

### EnviroOnly
_Optional `boolean`_. Default: `false`.

Expect no compartments, only a bounding box volume

### cancelDialog
_Optional `boolean`_. Default: `false`. 

### pickWeightedIngr
_Optional `boolean`_. Default: `true`. 

Prioritize ingredient selection by packingWeight.

### pickRandPt
_Optional `boolean`_. Default: `true`.

Pick drop position point randomly. If `false`, recipe packs in order from origin to opposite corner. 

### ingrLookForNeighbours
_Optional `boolean`_. Default: `false`. 

Look for ingredients attractor and partner.

### overwritePlaceMethod
_Optional `boolean`_. Default: `true`. 

If `true`, the Enviro-level placeMethod will overwrite all of the ingredient-level place method in a recipe


### boundingBox 
_Optional `[[number, number, number], [number, number, number]]`_. Default: `[0, 0, 0], [0.1, 0.1, 0.1]`.

An array of two points that define the corners of the bounding box.

### smallestProteinSize
_Optional `number`_. Default: `15`. 

Smallest ingredient packing radius override (low=accurate | high=fast). As with largestProteinSize, if not defined, this value will be calculated by the algorithm based on the spheretree input file (packing radius) or the packingRadius calculated from ingredients that use primitives for their geometries.

### largestProteinSize
_Optional `number`_

As with smallestProteinSize, if not defined, this value will be calculated by the algorithm based on the spheretree input file (packing radius) or the packingRadius calculated from ingredients that use primitives for their geometries.

### computeGridParams
_Optional `boolean`_. Default: `true`.

### windowsSize
_Optional `number`_. Default: `100`.

### runTimeDisplay
_Optional `boolean`_. Default: `false`.

Display packing in realtime (slow)

### placeMethod

_Optional `enum`_. One of `"jitter"`, `"spheresSST"`, `"pandaBullet"`.. Default: `"jitter"`.

Will be use if placeMethod isn't in an ingredient setup

`"jitter"` uses a simple algorithm developed by GJ, M-A-A, MS, and LA to test if a single sphere, sphere-tree, or other primative (box and cylinder) are colliding with masked/unallowed points on the grid... I can't recall all of the allowed types, but check the input parameters that it accepts. I believe there is also an option to perform simple collisions directly between primatives, e.g. sphere-sphere, sphere-box, sphere-cylinder, cylinder-box, and spheretree-others

`"spheresSST"` gets the sphereTrees of the potential colliding neighbors, and does an efficient sphereTree-sphereTree collision detection of the sphereTree for the object being packed against the sphereTrees of each neighbor- returns false if a collision is detected

`"pandaBullet"`  Python wrapper for Bullet Physics Engine (popular in ~2010 and used by C4D, Maya, Blender, etc) that provides a variety of object-object collision detection, including collision min/max overlap distance, etc. Allows relaxation in its own loop, springs, rejection, meshes, primitives, etc.

### use_gradient
_Optional `boolean`_. Default: `false`.

Use gradients if they are defined. 

### gradients 
_Optional `string[]`_

An array that defines the names of directional gradients to use.

### innerGridMethod
_Optional enum_. One of `"bhtree"`, `"raytrace"`, `"sdf"`, `"pyray"`, `"floodfill"`, `"binvox"`, `"trimesh"`, `"scanline"`. Default: `"raytrace"`.


 `"bhtree"` builds the compartment grid ie surface and inside point using bhtree.
 
 `"raytrace"` builds the compartment grid ie surface and inside point using raytrace
        

`"sdf"` builds the compartment grid ie surface and inside point using signed distance fields
        from the UT package.
         
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
 
 `"trimesh"` uses trimesh voxelize to find surface points
 
 `"scanline"` builds the compartment grid ie surface and inside point using scanline.

### freePtsUpdateThreshold
_Optional `number`_. Default: `0.0`.

Mask grid while packing (0=always | 1=never)

### use_periodicity
_Optional `boolean`_. Default: `false`. 

Whether to consider periodicity when packing objects. If `true` a packed object at the edge of the bounding will wrap to the other side of the bounding box. 

### _timer
_Optional `boolean`_. Default: `false`.

Evaluate time per function.

### _hackFreepts
_Optional `boolean`_. Default: `false`.

no free point update

#### example `Options`:
```JSON
"options": {
    "cancelDialog": false,
    "\_hackFreepts": false,
    "windowsSize": 10,
    "use_gradient": false,
    "placeMethod": "jitter",
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
_Required `string`_

Name of the ingredient.

### molarity
_Optional `number`_. Default: `0`.

Concentration of the ingredient. 

### count
_Optional `number`_

Number to pack, additive with molarity.. Default: `0`. 

### encapsulating_radius
_Optional `number`_. Default: `5`.

Smallest radius that completely includes all the geometry. 

### radii
_Optional `number[][]`_

Property of a primitive sphere. 

### positions
_Optional `[number, number, number][]`_

### positions2
_Optional `[number, number, number][]`_

### sphereFile
_Optional `string`_

Location of sphere file 

### packing_priority
_Optional `number`_ Default to `0.0`.

Order to pack, largest negative number gets packed first. 

### pdb
_Optional `string`_

PDB id in the protein database

### color
_[number, number, number]_

### meshFile
_Optional `string`_

Location of mesh file 

### meshName
_Optional `string`_

Name of the mesh file. 

### coordsystem
_Optional `enum.` One of `"left"` `"right"`_. Default: `"left"`.

### principal_vector
_Optional `[number, number, number]`_. Default: `[0.0, 0.0, 0.0]`.

### type
_Optional `enum`. One of `"SingleSphere"`,`"SingleCube"`,`"MultiSphere"`,`"MultiCylinder"`,`"Grow"`,`"Mesh"`_


`"SingleSphere"`

`"SingleCube"`

`"MultiSphere"`

`"MultiCylinder"`

`"Grow"`: A spline ingredient

`"Mesh"`

### offset 
_Optional  `[number, number, number]`_. Default: `[0.0, 0.0, 0.0]`.

### max_jitter
_Optional `[number, number, number]`_. Default: `[1, 1, 1]`.

### jitter_attempts
_Required `number`_ . Default: `5`.

How many times it will attempts to pack before rejecting the ingredient.

### perturb_axis_amplitude
_Optional `number`_. Default: `0.1`.

### use_rotation_axis
_Optional `boolean`_. Default: `false`.

### rotation_axis 
_Optional [number, number, number]_. Default: `[0.0, 0.0, 0.0]`.

### rotation_range
_Optional `number`_. Default: `6.2831`.

### use_orient_bias
_Optional `boolean`_. Default: `false`.

### orientBiasRotRangeMin
_Optional `number`_. Default: `-pi`.

### orientBiasRotRangeMax
_`number`_. Default: `pi`.

### cutoff_boundary
_Optional `number`_. Default: `1.0`.

The amount this ingredient can move in x, y and z. If z is set to 0, will be a 2D packing. 

### cutoff_surface
_Optional `number`_. Default: `5.0`.

### place_type
_Optional enum. One of `"jitter"`, `"spheresSST"`, `"pandaBullet"`_. Default: `"jitter"`.


`"jitter"` uses a simple algorithm developed by GJ, M-A-A, MS, and LA to test if a single sphere, sphere-tree, or other primative (box and cylinder) are colliding with masked/unallowed points on the grid... I can't recall all of the allowed types, but check the input parameters that it accepts. I believe there is also an option to perform simple collisions directly between primatives, e.g. sphere-sphere, sphere-box, sphere-cylinder, cylinder-box, and spheretree-others

`"spheresSST"` gets the sphereTrees of the potential colliding neighbors, and does an efficient sphereTree-sphereTree collision detection of the sphereTree for the object being packed against the sphereTrees of each neighbor- returns false if a collision is detected

`"pandaBullet"`  Python wrapper for Bullet Physics Engine (popular in ~2010 and used by C4D, Maya, Blender, etc) that provides a variety of object-object collision detection, including collision min/max overlap distance, etc. Allows relaxation in its own loop, springs, rejection, meshes, primitives, etc.

### rejection_threshold
_Optional `number`_. Default: `30`.

### packing_mode
_Optional enum. One of `"random"`, `"close"`, `"closePartner"`, `"randomPartner"`, `"gradient"`, `"hexatile"`, `"squaretile"`, `"triangletile"`_. Default: `"random"`.

### gradient
_Optional_ 
Gradient name to use if `use_gradient` is `true`. 

### proba_binding
_Optional `number` between `0` and `1`_. Default: `0.5`.

### proba_not_binding
_`number`_

### is_attractor
_Optional `boolean`_. Default: `false`.

### weight
_Optional `number`_. Default: `0.2`.

### partners_name
_Optional `string[]`_

### excluded_partners_name
_Optional `string[]`_

### partners_position
_Optional `number[][]`_

### partners_weight
_Optional `number`_. Default: `0.5`.

### properties
_Optional object_. Default: `{}`.

### score
_Optional `string`_

### organism
_Optional `string`_

### example ingredient
```JSON
"Sphere_radius_100": {
    "jitter_attempts": 6, 
    "molarity": 0,
    "partners_position": [],
    "rotation_range": 6.2831,
    "color": [ 0.498, 0.498, 0.498 ],
    "meshFile": null,
    "sphereFile": null,
    "weight": 0.2,
    "orientBiasRotRangeMin": -3.1415927,
    "radii": [[100]], 
    "cutoff_boundary": 0,
    "coordsystem": "left",
    "max_jitter": [ 1, 1, 0], 
    "perturb_axis_amplitude": 0.1,
    "encapsulating_radius": 100,
    "positions2": null,
    "use_orient_bias": false,
    "gradient": "",
    "is_attractor": false,
    "principal_vector": [ 1, 0, 0 ],
    "properties": {},
    "partners_name": [],
    "count": 6, 
    "name": "Sphere_radius_100",
    "orientBiasRotRangeMax": -3.1415927,
    "packing_mode": "random",
    "type": "SingleSphere", 
    "excluded_partners_name": [],
    "rejection_threshold": 60,
    "place_type": "jitter",
    "cutoff_surface": 100,
    "packing_priority": 0, 
    "proba_binding": 0.5,
    "rotation_axis": null,
    "positions": [ [ [ 0, 0, 0] ] ],
    "proba_not_binding": 0.5,
    "pdb": null,
    "use_rotation_axis": false
},

```


