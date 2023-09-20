import numpy

from cellpack.autopack.interface_objects.ingredient_types import INGREDIENT_TYPE


class PackedObject:
    def __init__(
        self,
        name,
        position,
        rotation,
        radius,
        encapsulating_radius,
        pt_index,
        compartment_id,
        ingredient_type: INGREDIENT_TYPE,
        color,
        is_compartment=False,
    ) -> None:
        self.name = name
        self.position = position
        self.rotation = rotation
        self.radius = radius
        self.encapsulating_radius = encapsulating_radius
        self.pt_index = pt_index
        self.compartment_id = compartment_id
        self.is_compartment = is_compartment
        self.ingredient_type = ingredient_type
        self.color = color

class PackedObjects:
    def __init__(self):
        self._packed_objects = []

    def add(self, new_object: PackedObject):
        self._packed_objects.append(new_object)

    def get_radii(self):
        radii = []
        for obj in self._packed_objects:
            if not obj.is_compartment:
                radii.append(obj.radius)
        return radii

    def get_encapsulating_radii(self):
        radii = []
        for obj in self._packed_objects:
            if not obj.is_compartment:
                radii.append(obj.encapsulating_radius)
        return radii
    
    def get_positions(self):
        positions = []
        for obj in self._packed_objects:
            if not obj.is_compartment:
                positions.append(obj.position)
        return positions

    def get_positions_for_ingredient(self, ingredient_name):
        return numpy.array(
            [
                self._packed_objects[i].position
                for i in range(len(self._packed_objects))
                if self._packed_objects[i].name == ingredient_name
            ]
        )

    def get_rotations_for_ingredient(self, ingredient_name):
        return numpy.array(
            [
                self._packed_objects[i].rotation
                for i in range(len(self._packed_objects))
                if self._packed_objects[i].name == ingredient_name
            ]
        )

    def get(self):
        return self._packed_objects
