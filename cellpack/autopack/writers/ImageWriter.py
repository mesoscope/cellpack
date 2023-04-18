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

        bounding_box = self.env.boundingBox
        self.image_size = tuple(
            ((bounding_box[1] - bounding_box[0]) / self.voxel_size).astype(int)
        )
        self.image_data = {}

    def create_voxelization(self):
        """
        Creates a voxelized representation of the current scene
        """
        channel_colors = []
        for pos, rot, ingr, _ in self.env.molecules:
            if ingr.name not in self.image_data:
                self.image_data[ingr.name] = numpy.zeros(self.image_size)
                if ingr.color is not None:
                    color = ingr.color
                    if all([x <= 1 for x in ingr.color]):
                        color = [int(col * 255) for col in ingr.color]
                    channel_colors.append(color)

            self.image_data[ingr.name] = ingr.create_voxelization_mask(
                image_data=self.image_data[ingr.name],
                bounding_box=self.env.boundingBox,
                voxel_size=self.voxel_size,
                image_size=self.image_size,
                position=pos,
                rotation=rot,
            )

        concatenated_image = numpy.zeros((len(self.image_data), *self.image_size))
        channel_names = []
        for ct, (channel_name, channel_image) in enumerate(self.image_data.items()):
            concatenated_image[ct] = channel_image
            channel_names.append(channel_name)

        concatenated_image = numpy.transpose(concatenated_image, axes=(3, 0, 1, 2))

        return concatenated_image, channel_names, channel_colors

    def export_image(self):
        """
        Saves the results as a tiff file
        """
        print(f"Exporting image to {self.output_path}")
        concatenated_image, channel_names, channel_colors = self.create_voxelization()
        filepath = self.output_path / f"voxelized_image_{self.name}.ome.tiff"
        OmeTiffWriter.save(
            concatenated_image,
            filepath,
            dim_order="ZCYX",
            channel_names=channel_names,
            channel_colors=channel_colors,
        )
