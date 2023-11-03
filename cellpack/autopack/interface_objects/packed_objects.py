import pickle
import numpy


class PackedObject:
    def __init__(
        self,
        position,
        rotation,
        radius,
        pt_index,
        ingredient=None,
        is_compartment=False,
    ) -> None:
        self.name = ingredient.name
        self.position = position
        self.rotation = rotation
        self.radius = radius
        self.encapsulating_radius = ingredient.encapsulating_radius
        self.pt_index = pt_index
        self.is_compartment = is_compartment
        self.color = ingredient.color
        self.ingredient = ingredient


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

    def get_ingredients(self):
        return [obj for obj in self._packed_objects if obj.is_compartment is False]

    def get_compartment(self):
        return [obj for obj in self._packed_objects if obj.is_compartment is True]

    def get_all(self):
        return self._packed_objects

    def save_to_file(self, path):
        pickle.dump(self.get_ingredients(), open(path, "wb"))
        return path

    def load_from_file(self, path):
        for obj in pickle.load(open(path, "rb")):
            obj.ingredient.reset()
            self.add(obj)
