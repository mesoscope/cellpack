import numpy

class PackedObjects(object):
    def __init__(self):
        # packed_object has 
            # name
            # position (x, y, z)
            # rotation matrix, or quat
            # radius 
            # encapsulating_radius
            # pt_index
            # compartment_id: id
            # is_compartment (boolean)
            # color
            # ingredient_type
        self.packed_objects = []

    def add_object(self, new_object):
        self.packed_objects.append(new_object)

    def get_radii(self):
        radii = []
        for obj in self.packed_objects:
            if not obj.is_compartment:
                radii.append(obj.radius)
        return radii
    
    def get_positions(self):
        positions = []
        for obj in self.packed_objects:
            if not obj.is_compartment:
                positions.append(obj.position)
        return positions
    
    def get_positions_for_ingredient(self, ingredient_name):
        return numpy.array(
            [
                self.packed_objects[i].position
                for i in range(len(self.packed_objects))
                if self.packed_objects[i].name == ingredient_name
            ]
        )
    
    def get_rotations_for_ingredient(self, ingredient_name):
        return numpy.array(
            [
                self.packed_objects[i].rotation
                for i in range(len(self.packed_objects))
                if self.packed_objects[i].name == ingredient_name
            ]
        )