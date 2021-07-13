# convert to simularium
# load model or traj and recipe and export to simularium
# traj from lammps or flex e.g. thats the plan
from simulariumio import CustomConverter, CustomData, AgentData
import json
import numpy as np
from collections import OrderedDict
import transformation as tr
import os


def AdjustBounds(bounds, X):
    """
    Check if a coordinate lies within the box boundary.
    If not, update the box boundary.
    """
    assert len(bounds) == 2
    assert len(bounds[0]) == len(bounds[1]) == len(X)

    for d in range(0, len(X)):
        if bounds[1][d] < bounds[0][d]:
            bounds[0][d] = bounds[1][d] = X[d]
        else:
            if np.isnan(X[d]):
                print(X)
            if X[d] < bounds[0][d]:
                bounds[0][d] = X[d]
            if bounds[1][d] < X[d]:
                bounds[1][d] = X[d]


def FromToRotation(dir1, dir2):
    r = 1.0 + np.dot(np.array(dir1), np.array(dir2))
    w = [0, 0, 0]
    if r < 1e-6:
        r = 0
        if abs(dir1[0]) > abs(dir1[2]):
            w = [-dir1[1], dir1[0], 0]
        else:
            w = [0.0, -dir1[2], dir1[1]]
    else:
        w = np.cross(np.array(dir1), np.array(dir2))
    q = np.array([w[0], w[1], w[2], r])
    q /= tr.vector_norm(q)
    return q


def QuaternionTransform(q, v):
    qxyz = np.array([q[0], q[1], q[2]])
    t = 2.0 * np.cross(qxyz, np.array(v))
    return v + q[3] * t + np.cross(qxyz, t)


def toGfVec3f(a):
    return [a[0], a[1], a[2]]


def GetModelData(model_in):
    # change to latest format
    import struct

    f = open(model_in, "rb")
    ninst = struct.unpack("<i", f.read(4))[0]
    ncurve = struct.unpack("<i", f.read(4))[0]
    pos = []
    quat = []
    ctrl_pts = []
    ctrl_normal = []
    ctrl_info = []
    if ninst != 0:
        data = f.read(ninst * 4 * 4)
        pos = np.frombuffer(data, dtype="f").reshape((ninst, 4))
        data = f.read(ninst * 4 * 4)
        quat = np.frombuffer(data, dtype="f").reshape((ninst, 4))
    if ncurve != 0:
        data = f.read(ncurve * 4 * 4)
        ctrl_pts = np.frombuffer(data, dtype="f").reshape((ncurve, 4))
        data = f.read(ncurve * 4 * 4)
        ctrl_normal = np.frombuffer(data, dtype="f").reshape((ncurve, 4))
        data = f.read(ncurve * 4 * 4)
        ctrl_info = np.frombuffer(data, dtype="f").reshape((ncurve, 4))
    f.close()
    return {
        "pos": pos,
        "quat": quat,
        "cpts": ctrl_pts,
        "cnorm": ctrl_normal,
        "cinfo": ctrl_info,
    }


def ingredientToAsset(ingr_node, compId):
    # //need to transform with pcp and offset. using Quat.Rotate - Vec3 rpos = Rotate(rotation, localPos);
    # proxyname;
    LevelPoints = []
    ingr_source = ingr_node["source"]
    pcpalVector = ingr_node["principalVector"]
    if pcpalVector == [0, 0, 0]:
        pcpalVector = [0, 0, 1]
    offsetnode = ingr_source["transform"]["offset"]
    offset = [
        0,
        0,
        0,
    ]  # //should be ingr_node["source"]["transform"]["offset"] if exist
    if offsetnode is not None:
        offset = np.array(offsetnode) * main_scale
        if compId <= 0:
            offset = offset * -1
    # parse the proxy and create a rigid body asset
    # check if "Type":"Grow"
    # IngredientSphereTree ingr_spheres;
    if ingr_node["ingtype"] == "Grow" or ingr_node["ingtype"] == "fiber":
        pnames_fiber.append(ingr_node["name"])
        pnames_fiber_nodes.append(ingr_node)
    else:
        p = lodproxy_to_use
        jsonpos = ingr_node["positions"][p]["coords"]
        radii = ingr_node["radii_lod"][p]["radii"]
        raxe = FromToRotation([0, 0, 1], pcpalVector)
        # if (pcpalVector == Vec3(0, 0, 1)) raxe = Quat(0, 0, 0, 1);
        # std::cout << "ingr raxe  : " << raxe.x << " " << raxe.y << " " << raxe.z << " " << raxe.w << endl;
        for i in range(
            int(len(jsonpos) / 3)
        ):  # (int i = 0; i < jsonpos.size()/3; i++){//1
            beadp = (
                np.array([jsonpos[i * 3], jsonpos[i * 3 + 1], jsonpos[i * 3 + 2]])
                * main_scale
            )
            beadp = QuaternionTransform(raxe, beadp + offset)  # //rotate
            LevelPoints.append(beadp)  # *main_scale
            # std::cout << jsonpos[i*3].asFloat() << endl;
        # std::cout << "ingr positions  nb " << ingr_spheres.LevelPoints.size() << endl;
        # points_to_use = ingr_spheres.LevelPoints;

        if len(LevelPoints) == 0:
            # std::cout << "ingr proxy  0 return " << points_to_use.size() << endl;
            # try to do it from the mesh ?
            return
        # std::cout << "points_to_use0  : " << points_to_use[0].x << " " << points_to_use[0].y << " " << points_to_use[0].z << endl;
        # before creating the asset, if surface, remove beads at intersection of the enveloppe.
        proteins_beads.append(LevelPoints)
        pnames.append(ingr_node["name"])
        proteins_nodes.append(ingr_node)
        proteins_beads_radii.append(radii)


def parseJsonIngredientsSerialized(ingr_nodes, comp):
    # iteration is using alphabetic order?
    # JsonCpp keeps its values in a std::map<CZString, Value>, which is always sorted by the CZString comparison,
    nIngredients = len(ingr_nodes)
    for i in range(nIngredients):  # (int i = 0; i < nIngredients; i++) {
        ingr_node_name = ingr_nodes[i]
        ingredientToAsset(ingr_node_name, comp)


def loadIngredientFromCompartment(comp, compid):
    # std::cout << "load IngredientFromCompartment " << comp["name"].asString() << endl;
    if len(comp["IngredientGroups"]) != 0:
        # std::cout << "comp[IngredientGroups].size() " << comp["IngredientGroups"].size() << endl;
        igroup = comp["IngredientGroups"][0]
        if len(igroup["Ingredients"]) != 0:
            ingredients = igroup["Ingredients"]
            # std::cout << "compartment should have n ingredients " << ingredients.size() << endl;
            parseJsonIngredientsSerialized(ingredients, compid)


def loadRecipe(book_json):
    root = book_json
    loadIngredientFromCompartment(root, 0)
    comp = book_json["Compartments"]
    i = 0
    if len(comp) != 0:
        # std::cout << "find compartments " << comp.size() << endl;
        for i in range(len(comp)):  # (int i=0;i< comp.size();i++)
            compid = i + 1
            comp_name = comp[i]
            # CompMask* cm = new CompMask();
            # std::cout << "compartment should have several childs " << comp_name.size() << " " << comp_name["name"].asString() << endl;
            if len(comp_name) == 0:
                continue

            comp_childs = comp_name["Compartments"]
            for j in range(
                len(comp_childs)
            ):  # (int j = 0; j < comp_childs.size(); j++) {
                if comp_childs[j]["name"] == "surface":
                    loadIngredientFromCompartment(comp_childs[j], compid)
                elif comp_childs[j]["name"] == "interior":
                    loadIngredientFromCompartment(comp_childs[j], -compid)


def oneModel():
    bounds = [
        [0.0, 0.0, 0.0],  # Box big enough to enclose all the particles
        [-1.0, -1.0, -1.0],
    ]

    wdir = "/Users/meganriel-mehan/Dropbox/cellPack/NM_Analysis_C_rapid"
    file_in = wdir + "results_seed_0.json"  # recipe.json
    model_in = wdir + "model.bin"  # bin or traj
    tree = json.load(open(file_in, "r"), object_pairs_hook=OrderedDict)
    model_data = GetModelData(model_in)
    ninstances = len(model_data["pos"])

    n_agents = []
    type_names = []
    types = []
    positions = []
    radii = []

    loadRecipe(tree)

    for i in range(ninstances):
        p = model_data["pos"][i]
        q = model_data["quat"][i]
        ptype = int(p[3])
        # print (ptype,ingredient["name"])
        # name = ingredient["name"]
        # int ingrIndex = (int) pos[i][3];
        # //std::cout << "instance " << i << " with pid " << ingrIndex << " " << pnames[ingrIndex] << endl;
        print(ptype, pnames[ptype], p, q)
        # add beads to positions and radii after transformation
        for j in range(len(proteins_beads[ptype])):
            bead_p = np.array([p[0], p[1], p[2]]) + QuaternionTransform(
                q, proteins_beads[ptype][j]
            )
            bead_r = proteins_beads_radii[ptype][j]
            positions.append([bead_p[0], bead_p[1], bead_p[2]])
            radii.append(bead_r)
            type_names.append(pnames[ptype])
            types.append(ptype)
            AdjustBounds(bounds, [bead_p[0], bead_p[1], bead_p[2]])

    ncpts = len(model_data["cpts"])
    cpts_info = model_data["cinfo"]
    if ncpts != 0:
        ncurves = np.unique(cpts_info[:, 0])
        for i in ncurves:
            indices = cpts_info[:, 0] == i
            infos = cpts_info[indices]  # curve_id, curve_type, angle, uLength
            pts = model_data["cpts"][indices] * np.array(
                [-1.0, 1.0, 1.0, 1.0]
            )  # xyz_radius
            ptype = infos[0][1]
            print("ingredient fiber ", i, ptype, pnames_fiber[int(ptype)])
            # add pts to positions and radii
            for cp in pts:
                positions.append([cp[0], cp[1], cp[2]])
                radii.append(cp[3])
                type_names.append(pnames_fiber[int(ptype)])
                types.append(int(ptype))

    print("convert")
    print(bounds)
    print(len(positions))
    # parameters
    total_steps = 1
    timestep = 0.5  # seconds
    box_size = 3500
    n_agents = len(positions)  # n instances

    example_default_data = CustomData(
        # spatial_unit_factor_meters=1e-10,  # angstrom
        box_size=np.array([box_size, box_size, box_size]),
        agent_data=AgentData(
            times=timestep * np.array(list(range(total_steps))),
            n_agents=np.array(total_steps * [n_agents]),
            viz_types=np.array(total_steps * [n_agents * [1000.0]]),
            unique_ids=np.array(total_steps * [list(range(n_agents))]),
            types=[type_names],
            positions=np.array([positions]),
            radii=np.array([radii]),
        ),
    )

    CustomConverter(example_default_data).write_JSON("test3")


# def multiModel():
bounds = [
    [0.0, 0.0, 0.0],  # Box big enough to enclose all the particles
    [-1.0, -1.0, -1.0],
]

main_scale = 1.0 / 100.0  # could be 1/200.0 like flex
pnames_fiber = []
pnames_fiber_nodes = []
pnames = []
proteins_nodes = []
proteins_beads = []
proteins_beads_radii = []
lodproxy_to_use = 0

wdir = "/Users/meganriel-mehan/Dropbox/cellPack/NM_Analysis_C_rapid/"
file_in = wdir + "results_seed_0.json"  # recipe.json
model_in = wdir + "model.bin"  # bin or traj
tree = json.load(open(file_in, "r"), object_pairs_hook=OrderedDict)
loadRecipe(tree)
path_to_traj = wdir + "traj\\"
listOfFile = os.listdir(path_to_traj)
n_agents = []
viz_types = []
unique_ids = []
type_names = []
types = []
all_positions = []
all_radii = []
all_type_names = []
n_subpoints = []
subpoints = []
total_steps = len(listOfFile)
STOP = 20
counter = 0
for entry in sorted(listOfFile, key=lambda x: int(x.split(".bin")[0].split("_")[2])):
    if counter > STOP:
        break
    # Create full path
    fullPath = os.path.join(path_to_traj, entry)
    print(fullPath)
    model_data = GetModelData(fullPath)
    ninstances = len(model_data["pos"])  # should be consistant
    n_agents = []
    viz_types = []
    unique_ids = []
    type_names = []
    types = []
    positions = []
    radii = []
    n_subpoints = []
    subpoints = []

    for i in range(ninstances):
        p = model_data["pos"][i]
        q = model_data["quat"][i]
        ptype = int(p[3])
        # ingredient, cname, path = FindIngredientInTreeFromId(ptype,tree)
        # print (ptype,ingredient["name"])
        # name = ingredient["name"]
        # int ingrIndex = (int) pos[i][3];
        # print (ptype,pnames[ptype], p, q );
        # add beads to positions and radii after transformation
        for j in range(len(proteins_beads[ptype])):
            bead_p = np.array([p[0], p[1], p[2]]) * main_scale + QuaternionTransform(
                q, proteins_beads[ptype][j]
            )
            bead_r = float(proteins_beads_radii[ptype][j]) * main_scale
            positions.append([bead_p[0], bead_p[1], bead_p[2]])
            radii.append(bead_r)
            type_names.append(pnames[ptype])
            # types.append(ptype)
            AdjustBounds(bounds, [bead_p[0], bead_p[1], bead_p[2]])

    ncpts = len(model_data["cpts"])
    cpts_info = model_data["cinfo"]
    if ncpts != 0:
        ncurves = np.unique(cpts_info[:, 0])
        curves = np.array([cpts_info[cpts_info[:, 0] == i, :] for i in ncurves])
        for i in ncurves:
            indices = cpts_info[:, 0] == i
            infos = cpts_info[indices]  # curve_id, curve_type, angle, uLength
            pts = model_data["cpts"][indices] * np.array(
                [-1.0, 1.0, 1.0, 1.0]
            )  # xyz_radius
            normal = model_data["cnorm"][indices]  # xyz_0
            ptype = infos[0][1]
            # print ("ingredient fiber ",i , ptype, pnames_fiber[int(ptype)])
            # add pts to positions and radii
            for cp in pts:
                positions.append(
                    [cp[0] * main_scale, cp[1] * main_scale, cp[2] * main_scale]
                )
                radii.append(cp[3] * main_scale)
                type_names.append(pnames_fiber[int(ptype)])
                # types.append(int(ptype))
    all_positions.append(positions)
    all_radii.append(radii)
    all_type_names.append(type_names)
    counter += 1

print("convert")
print(bounds)
print(len(positions))
# parameters
total_steps = len(all_positions)
timestep = 0.5  # seconds
box_size = 3500 * main_scale
n_agents = len(positions)  # n instances
min_radius = 5
max_radius = 10
points_per_fiber = 4
example_default_data = CustomData(
    # spatial_unit_factor_meters=1e-10,  # angstrom
    box_size=np.array([box_size, box_size, box_size]),
    agent_data=AgentData(
        times=timestep * np.array(list(range(total_steps))),
        n_agents=np.array(total_steps * [n_agents]),
        viz_types=np.array(total_steps * [n_agents * [1000.0]]),
        unique_ids=np.array(total_steps * [list(range(n_agents))]),
        types=all_type_names,
        positions=np.array(all_positions),
        radii=np.array(all_radii),
    ),
)
CustomConverter(example_default_data).write_JSON("traj1")


"""
type_names = []
for t in range(total_steps):
    type_names.append([choice(ascii_uppercase) for i in range(n_agents)])

example_fiber_data = CustomData(
    spatial_unit_factor_meters=1e-9,  # nanometers
    box_size=np.array([box_size, box_size, box_size]),
    agent_data=AgentData(
        times=timestep * np.array(list(range(total_steps))),
        n_agents=np.array(total_steps * [n_agents]),
        viz_types=np.array(total_steps * [n_agents * [1001.0]]), # fiber viz type = 1001
        unique_ids=np.array(total_steps * [list(range(n_agents))]),
        types=type_names,
        positions=np.zeros(shape=(total_steps, n_agents, 3)),
        radii=np.ones(shape=(total_steps, n_agents)),
        n_subpoints=points_per_fiber * np.ones(shape=(total_steps, n_agents)),
        subpoints=box_size * np.random.uniform(
            size=(total_steps, n_agents, points_per_fiber, 3)) - box_size * 0.5
    )
)

example_default_data = CustomData(
    spatial_unit_factor_meters=1e-9,  # nanometers
    box_size=np.array([box_size, box_size, box_size]),
    agent_data=AgentData(
        times=timestep * np.array(list(range(total_steps))),
        n_agents=np.array(total_steps * [n_agents]),
        viz_types=np.array(total_steps * [n_agents * [1000.0]]),  # default viz type = 1000
        unique_ids=np.array(total_steps * [list(range(n_agents))]),
        types=type_names,
        positions=np.random.uniform(size=(total_steps, n_agents, 3)) * box_size - box_size * 0.5,
        radii=(max_radius - min_radius) * np.random.uniform(size=(total_steps, n_agents)) + min_radius
    )
)


CustomConverter(example_fiber_data).write_JSON("example_fibers")
CustomConverter(example_default_data).write_JSON("example_default")
"""
