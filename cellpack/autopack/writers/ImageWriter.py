from aicsimageio.writers.ome_tiff_writer import OmeTiffWriter
from pathlib import Path
import numpy

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

    @staticmethod
    def create_circular_mask(x_width, y_width, z_width, center=None, radius=None):
        """
        Creates a circular mask of the given shape with the specified center
        and radius
        """
        if center is None:  # use the middle of the image
            center = (int(x_width / 2), int(y_width / 2), int(z_width / 2))
        if (
            radius is None
        ):  # use the smallest distance between the center and image walls
            radius = min(
                center[0],
                center[1],
                center[2],
                x_width - center[0],
                y_width - center[1],
                z_width - center[2],
            )

        X, Y, Z = numpy.ogrid[:x_width, :y_width, :z_width]
        dist_from_center = numpy.sqrt(
            (X - center[0]) ** 2 + (Y - center[1]) ** 2 + (Z - center[2]) ** 2
        )

        mask = dist_from_center <= radius
        return mask

    def create_voxelization(self):
        """
        Creates a voxelized representation of the current grid
        """
        bounding_box = self.env.boundingBox
        num_voxels = tuple(
            ((bounding_box[1] - bounding_box[0]) / self.voxel_size).astype(int)
        )

        img = numpy.zeros(num_voxels)

        return img

    def export_image(self):
        """
        Saves the results as a tiff file
        """
        print(f"Exporting image to {self.output_path}")
        img = self.create_voxelization()
        filepath = self.output_path / f"voxelized_image_{self.name}.ome.tiff"
        OmeTiffWriter.save(img.T, filepath, dim_order="ZYX")
