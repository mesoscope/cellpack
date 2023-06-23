from aicsimageio.writers.ome_tiff_writer import OmeTiffWriter
from pathlib import Path
import numpy
from scipy.ndimage import convolve

"""
ImageWriter provides a class to export cellpack packings as tiff images
"""


class ImageWriter:
    def __init__(
        self,
        env,
        name=None,
        output_path=None,
        voxel_size=None,
        num_voxels=None,
        hollow=False,
        convolution_options=None,
        projection_axis="z",
    ):
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
        elif num_voxels is not None:
            self.voxel_size = (
                self.env.boundingBox[1] - self.env.boundingBox[0]
            ) / numpy.array(num_voxels)

        self.hollow = hollow

        bounding_box = self.env.boundingBox
        self.image_size = tuple(
            numpy.maximum(
                ((bounding_box[1] - bounding_box[0]) / self.voxel_size), 1
            ).astype(int)
        )
        self.image_data = {}

        self.convolution_options = convolution_options

        self.projection_axis = projection_axis

        
    @staticmethod
    def create_gaussian_psf(sigma=1.5, size=None):
        """
        Creates a gaussian psf

        Parameters
        ----------
        sigma: float
            sigma of the gaussian
        size: np.ndarray
            size of the psf

        Returns
        ----------
        numpy.ndarray
            psf
        """
        if size is None:
            size = [3, 3, 3]

        x, y, z = numpy.meshgrid(
            numpy.linspace(-size[0] / 2, size[0] / 2, size[0]),
            numpy.linspace(-size[1] / 2, size[1] / 2, size[1]),
            numpy.linspace(-size[2] / 2, size[2] / 2, size[2]),
        )
        psf = numpy.exp(-(x**2 + y**2 + z**2) / (2 * sigma**2))
        psf /= psf.sum()

        return psf


    @staticmethod
    def create_box_psf(size=None):
        """
        Creates a box psf

        Parameters
        ----------
        size: np.ndarray
            size of the psf

        Returns
        ----------
        numpy.ndarray
            psf
        """
        if size is None:
            size = [3, 3, 3]

        psf = numpy.ones(size)
        psf /= psf.sum()

        return psf

      
    @staticmethod
    def convolve_channel(channel, psf):
        """
        Convolves a channel with a psf

        Parameters
        ----------
        channel: numpy.ndarray
            channel to be convolved
        psf: numpy.ndarray
            psf

        Returns
        ----------
        numpy.ndarray
            convolved channel
        """
        scaled_channel = channel.astype(numpy.float32) / 255.0
        conv_channel = convolve(scaled_channel, psf, mode="constant", cval=0.0)
        conv_channel = (conv_channel * 255).astype(numpy.uint8)
        return conv_channel


    @staticmethod
    def transpose_image_for_projection(image, projection_axis):
        if projection_axis == "x":
            image = numpy.transpose(image, axes=(1, 0, 3, 2))
        elif projection_axis == "y":
            image = numpy.transpose(image, axes=(2, 0, 3, 1))
        elif projection_axis == "z":
            image = numpy.transpose(image, axes=(3, 0, 2, 1))
        return image


    def convolve_image(self, image, psf="gaussian", psf_parameters=None):
        """
        Convolves the image with a psf

        Parameters
        ----------
        image: numpy.ndarray
            image to be convolved
        psf: str or numpy.ndarray
            psf type
        psf_parameters: dict
            psf parameters

        Returns
        ----------
        numpy.ndarray
            convolved image
        """
        # TODO: add checking for psf_parameters
        if psf_parameters is None:
            psf_parameters = {}
            psf_parameters["sigma"] = 1.5
            psf_parameters["size"] = [3, 3, 3]

        if isinstance(psf, str):
            if psf == "gaussian":
                psf = self.create_gaussian_psf(**psf_parameters)
            elif psf == "box":
                psf = self.create_box_psf(psf_parameters.get("size", None))
            else:
                raise NotImplementedError(f"PSF type {psf} not implemented")

        conv_img = numpy.zeros(image.shape, dtype=image.dtype)
        for channel in range(image.shape[0]):
            conv_img[channel] = self.convolve_channel(image[channel], psf)
        return conv_img


    def create_voxelization(self):
        """
        Creates a voxelized representation of the current scene
        """

        self.image_data, channel_colors = self.env.create_voxelization(
            self.image_data, self.image_size, self.voxel_size, self.hollow
        )


        concatenated_image = numpy.zeros(
            (len(self.image_data), *self.image_size), dtype=numpy.uint8
        )
        channel_names = []
        for ct, (channel_name, channel_image) in enumerate(self.image_data.items()):
            concatenated_image[ct] = channel_image
            channel_names.append(channel_name)

        if self.convolution_options is not None:
            concatenated_image = self.convolve_image(
                concatenated_image, **self.convolution_options
            )

        concatenated_image = self.transpose_image_for_projection(
            concatenated_image, self.projection_axis
        )

        return concatenated_image, channel_names, channel_colors

    def export_image(self):
        """
        Saves the results as a tiff file
        """
        print(f"Exporting image to {self.output_path}")
        concatenated_image, channel_names, channel_colors = self.create_voxelization()
        if len(channel_names) != 0:
            filepath = self.output_path / f"voxelized_image_{self.name}.ome.tiff"
            OmeTiffWriter.save(
                concatenated_image,
                filepath,
                dim_order="ZCYX",
                channel_names=channel_names,
                channel_colors=channel_colors,
            )
