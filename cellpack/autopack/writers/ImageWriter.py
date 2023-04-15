from aicsimageio.writers.ome_tiff_writer import OmeTiffWriter
from pathlib import Path
import numpy
from cellpack.autopack.interface_objects.ingredient_types import INGREDIENT_TYPE

"""
ImageWriter provides a class to export cellpack packings as tiff images
"""


class ImageWriter:
    def __init__(self, env, name=None, output_path=None, voxel_size=None):
        self.env = env

        self.name = "default"
        if name is not None:
            self.name = name

        self.output_path = Path(self.env.out_folder)
        if output_path is not None:
            self.output_path = Path(output_path)

        self.voxel_size = numpy.array([1, 1, 1])  # units of grid points per voxel
        if voxel_size is not None:
            self.voxel_size = numpy.array(voxel_size)

        bounding_box = self.env.boundingBox
        self.num_voxels = tuple(
            ((bounding_box[1] - bounding_box[0]) / self.voxel_size).astype(int)
        )
        self.img = numpy.zeros(self.num_voxels)

    def create_voxelization(self):
        """
        Creates a voxelized representation of the current scene
        """
        for pos, rot, ingr, ptInd in self.env.molecules:
            self.img = ingr.create_voxelization_mask(
                img=self.img,
                bounding_box=self.env.boundingBox,
                voxel_size=self.voxel_size,
                num_voxels=self.num_voxels,
                position=pos,
                rotation=rot,
            )

        return self.img.T

    def export_image(self):
        """
        Saves the results as a tiff file
        """
        print(f"Exporting image to {self.output_path}")
        img = self.create_voxelization()
        filepath = self.output_path / f"voxelized_image_{self.name}.ome.tiff"
        OmeTiffWriter.save(img, filepath, dim_order="ZYX")
