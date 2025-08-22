# -*- coding: utf-8 -*-
"""
Created on Mon May  6 22:58:44 2013

@author: ludo
"""
import concurrent.futures
import json
import logging
import multiprocessing
from pathlib import Path
from time import time
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.patches import Circle
from scipy.spatial.distance import cdist, pdist

import cellpack.autopack as autopack
from cellpack.autopack.Environment import Environment
from cellpack.autopack.ingredient.Ingredient import Ingredient
from cellpack.autopack.ldSequence import halton
from cellpack.autopack.plotly_result import PlotlyAnalysis
from cellpack.autopack.transformation import signed_angle_between_vectors
from cellpack.autopack.utils import check_paired_key, get_paired_key, get_seed_list
from cellpack.autopack.writers import Writer
from cellpack.autopack.writers.MarkdownWriter import MarkdownWriter

log = logging.getLogger(__name__)


class Analysis:
    def __init__(
        self,
        env: Environment,
        packing_results_path: Optional[Union[Path, str]] = None,
        output_path: Optional[Union[Path, str]] = None,
    ) -> None:
        """
        Initialize the Analysis class.

        Parameters
        ----------
        env
            The environment object containing the packing results.
        packing_results_path
            Path to the folder containing packing results. If None, uses env.out_folder.
        output_path
            Path to the output folder for analysis results. If None, uses env.out_folder.
        """
        self.env = None
        if env:
            self.env = env
        self.center = [0, 0, 0]
        self.plotly = PlotlyAnalysis()

        if packing_results_path is not None:
            self.packing_results_path = Path(packing_results_path)
        elif self.env is not None:
            self.packing_results_path = Path(self.env.out_folder)
        else:
            raise ValueError("Either packing_results_path or env must be provided.")

        if output_path is not None:
            self.output_path = Path(output_path)
        elif self.env is not None:
            self.output_path = Path(self.env.out_folder)
        else:
            self.output_path = Path("out/")

        self.figures_path = self.output_path / "figures"
        self.figures_path.mkdir(parents=True, exist_ok=True)

        self.seed_to_results = {}
        self.helper = autopack.helper

    @staticmethod
    def cartesian_to_sph(
        xyz: np.ndarray, center: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Convert cartesian to spherical coordinates.

        Parameters
        ----------
        xyz
            Array of shape (n, 3) containing cartesian coordinates.
        center
            Optional center point for conversion. If None, uses the origin (0, 0, 0).

        Returns
        -------
        :
            Array of shape (n, 3) containing spherical coordinates (r, theta, phi).
            r: radial distance from the center
            theta: polar angle (angle from the z-axis)
            phi: azimuthal angle (angle in the x-y plane)
        """
        if center is None:
            center = np.zeros(3)
        xyz = xyz - center
        sph_pts = np.zeros(xyz.shape)
        xy = xyz[:, 0] ** 2 + xyz[:, 1] ** 2
        sph_pts[:, 0] = np.sqrt(xy + xyz[:, 2] ** 2)
        sph_pts[:, 1] = np.arctan2(np.sqrt(xy), xyz[:, 2])
        sph_pts[:, 2] = np.arctan2(xyz[:, 1], xyz[:, 0])

        return sph_pts

    @staticmethod
    def get_list_of_dims() -> list[str]:
        """
        Get a list of dimensions used in the analysis.

        Returns
        -------
        :
            List of dimension names.
        """
        return ["x", "y", "z", "r", "theta", "phi"]

    def get_all_distances(self, position: Optional[List[float]] = None) -> np.ndarray:
        """
        Get distances between all packed objects or from a specific position.

        Parameters
        ----------
        position
            Position to calculate distances from

        Returns
        -------
        :
            Array of distances
        """
        positions = self.env.packed_objects.get_positions()
        if len(positions) == 0:
            return np.array([])
        elif position is not None:
            return np.linalg.norm(positions - np.array(position), axis=1)
        else:
            return pdist(positions)

    def get_distances(
        self, ingredient_name: str, center: List[float]
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Get distances for a specific ingredient.

        Parameters
        ----------
        ingredient_name
            Name of the ingredient
        center
            Center position for distance calculations

        Returns
        -------
        :
            Ingredient positions, distances from center, distances between ingredients
        """
        ingredient_positions = self.env.packed_objects.get_positions_for_ingredient(
            ingredient_name
        )

        if len(ingredient_positions):
            distances_between_ingredients = pdist(ingredient_positions)
            distances_from_center = np.linalg.norm(
                ingredient_positions - np.array(center), axis=1
            )
        else:
            distances_from_center = np.array([])
            distances_between_ingredients = np.array([])

        return (
            ingredient_positions,
            distances_from_center,
            distances_between_ingredients,
        )

    def get_ingredient_angles(
        self,
        ingredient_name: str,
        center: List[float],
        ingredient_positions: np.ndarray,
    ) -> np.ndarray:
        """
        Calculate angles for ingredient orientations.

        Parameters
        ----------
        ingredient_name
            Name of the ingredient
        center
            Center position for angle calculations
        ingredient_positions
            Positions of ingredient instances

        Returns
        -------
        :
            Array of angles in degrees for X, Y, Z rotations
        """
        ingredient_rotation = self.env.packed_objects.get_rotations_for_ingredient(
            ingredient_name=ingredient_name,
        )
        ingredient_position_vector = np.array(ingredient_positions) - np.array(center)

        anglesX = np.array(
            signed_angle_between_vectors(
                [[0, 0, 1]] * len(ingredient_positions),
                ingredient_rotation[:, 0, :3],
                -ingredient_position_vector,
                directed=False,
                axis=1,
            )
        )
        anglesY = np.array(
            signed_angle_between_vectors(
                [[0, 1, 0]] * len(ingredient_positions),
                ingredient_rotation[:, 1, :3],
                -ingredient_position_vector,
                directed=False,
                axis=1,
            )
        )
        anglesZ = np.array(
            signed_angle_between_vectors(
                [[1, 0, 0]] * len(ingredient_positions),
                ingredient_rotation[:, 2, :3],
                -ingredient_position_vector,
                directed=False,
                axis=1,
            )
        )
        return np.degrees(np.array([anglesX, anglesY, anglesZ]))

    def get_distances_and_angles(
        self, ingredient_name: str, center: List[float], get_angles: bool = False
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Get distances and optionally angles for an ingredient.

        Parameters
        ----------
        ingredient_name
            Name of the ingredient
        center
            Center position for calculations
        get_angles
            Whether to calculate angles

        Returns
        -------
        :
            Positions, distances from center, distances between ingredients, angles
        """
        (
            ingredient_positions,
            distances_from_center,
            distances_between_ingredients,
        ) = self.get_distances(ingredient_name, center)
        if get_angles:
            angles = self.get_ingredient_angles(
                ingredient_name, center, ingredient_positions
            )
        else:
            angles = np.array([])

        return (
            ingredient_positions,
            distances_from_center,
            distances_between_ingredients,
            angles,
        )

    def calc_pairwise_distances(self, ingr1name: str, ingr2name: str) -> np.ndarray:
        """
        Returns pairwise distances between ingredients of different types.

        Parameters
        ----------
        ingr1name
            Name of first ingredient type
        ingr2name
            Name of second ingredient type

        Returns
        -------
        :
            Flattened array of pairwise distances
        """
        ingredient_positions_1 = self.env.packed_objects.get_positions_for_ingredient(
            ingredient_name=ingr1name
        )
        ingredient_positions_2 = self.env.packed_objects.get_positions_for_ingredient(
            ingredient_name=ingr2name
        )
        return np.ravel(cdist(ingredient_positions_1, ingredient_positions_2))

    def writeJSON(self, filename: Union[Path, str], data: Union[Dict, list]) -> None:
        """
        Write data to a JSON file.

        Parameters
        ----------
        filename
            The path to the file where data will be written.
        data
            The data to be written to the file, typically a dictionary or list.
        """
        with open(filename, "w") as fp:
            json.dump(data, fp, indent=4, separators=(",", ": "))

    def loadJSON(self, filename: Union[Path, str]) -> Dict:
        """
        Load data from a JSON file.

        Parameters
        ----------
        filename
            The path to the JSON file to be loaded.

        Returns
        -------
        :
            The data loaded from the JSON file as a dictionary.
        """
        with open(filename) as data_file:
            data = json.load(data_file)
        return data

    def plot_position_histogram_all_ingredients(
        self, all_positions: Union[list[list[float]], np.ndarray]
    ) -> None:
        """
        Plot the histogram of positions for all ingredients.

        Parameters
        ----------
        all_positions
            A list of lists containing the positions of all ingredients.
            Each inner list should contain [x, y, z] coordinates.
        """
        pos_xyz = np.array(all_positions)
        if pos_xyz.shape[0] <= 1:
            return
        pos_sph = self.cartesian_to_sph(pos_xyz)
        all_pos = np.hstack([pos_xyz, pos_sph])
        for ind, dim in enumerate(self.get_list_of_dims()):
            self.histogram(
                all_pos[:, ind],
                self.figures_path
                / f"all_ingredient_histogram_{dim}_{self.basename}.png",
                title_str="all_ingredients",
                x_label=dim,
                y_label="count",
            )

    def plot_position_histogram_for_ingredient(self, ingredient: Ingredient) -> None:
        """
        Plot the histogram of positions for a specific ingredient.

        Parameters
        ----------
        ingredient
            An instance of the Ingredient class containing the positions and name.
        """
        pos_xyz = np.array(self.ingredient_positions[ingredient.name])
        if pos_xyz.shape[0] <= 1:
            log.debug(f"Not enough positions for {ingredient.name} to plot histogram.")
            return
        pos_sph = self.cartesian_to_sph(pos_xyz)
        all_pos = np.hstack([pos_xyz, pos_sph])
        for ind, dim in enumerate(self.get_list_of_dims()):
            self.histogram(
                all_pos[:, ind],
                self.figures_path
                / f"{ingredient.name}_histogram_{dim}_{self.basename}.png",
                title_str=ingredient.name,
                x_label=dim,
                y_label="count",
            )

    def plot_occurence_distribution(self, ingredient: Ingredient) -> None:
        """
        Plot the occurrence distribution of a specific ingredient.

        Parameters
        ----------
        ingredient
            An instance of the Ingredient class containing the name and occurrences.
        """
        occ = self.occurences[ingredient.name]
        if len(occ) <= 1:
            return
        self.simpleplot(
            np.arange(len(occ)),
            occ,
            self.figures_path
            / f"{ingredient.name}_occurrence_{self.basename}_lineplot.png",
            title_str=ingredient.name,
            x_label="seed",
            y_label="occurrences",
        )
        self.histogram(
            distances=np.array(occ),
            filename=self.figures_path
            / f"{ingredient.name}_occurrence_{self.basename}_histogram.png",
            title_str=ingredient.name,
            x_label="occurrences",
            y_label="count",
        )

    def plot_distance_distribution(
        self, all_ingredient_distances: Dict[str, list[float]]
    ) -> None:
        """
        Plot the distribution of distances for ingredient and pairs of ingredients.

        Parameters
        ----------
        all_ingredient_distances
            A dictionary where keys are ingredient names and values are lists of distances.
            Each list contains pairwise distances for that ingredient.
        """
        for ingr_key, distances in all_ingredient_distances.items():
            if len(distances) <= 1:
                continue
            self.histogram(
                distances=np.array(distances),
                filename=self.figures_path
                / f"{ingr_key}_pairwise_distances_{self.basename}.png",
                title_str=ingr_key,
                x_label="pairwise distance",
                y_label="count",
                save_png=True,
            )

    def get_packed_object_data(
        self, packing_results_path: Union[Path, str]
    ) -> Tuple[Dict[str, Any], list[Dict[str, Any]]]:
        """
        Get packed object data from JSON files in the specified directory.

        Parameters
        ----------
        packing_results_path
            Path to the directory containing JSON files with packed object positions.

        Returns
        -------
        :
            A tuple containing:
            - all_objs: A dictionary with object positions and spherical coordinates.
            - all_pos_list: A list of dictionaries with positions for each packing.
        """
        file_list = Path(packing_results_path).glob("positions_*.json")
        all_pos_list = []
        packing_id_dict = {}
        for packing_index, file_path in enumerate(file_list):
            packing_id_dict[packing_index] = str(file_path).split("_")[-1].split(".")[0]
            with open(file_path, "r") as j:
                all_pos_list.append(json.loads(j.read()))

        all_objs = {}
        for packing_id, all_pos in zip(packing_id_dict.values(), all_pos_list):
            for seed, object_dict in all_pos.items():
                for obj, positions in object_dict.items():
                    positions = np.array(positions)
                    if obj not in all_objs:
                        all_objs[obj] = {}
                    seed_key = f"{seed}_{packing_id}"
                    if seed_key not in all_objs[obj]:
                        all_objs[obj][seed_key] = {}
                    for ct, dim in enumerate(["x", "y", "z"]):
                        all_objs[obj][seed_key][dim] = positions[:, ct]
                    sph_pts = self.cartesian_to_sph(positions)
                    for ct, dim in enumerate(["r", "theta", "phi"]):
                        all_objs[obj][seed_key][dim] = sph_pts[:, ct]
        self.all_objs = all_objs
        self.all_pos_list = all_pos_list
        self.packing_id_dict = packing_id_dict
        return all_objs, all_pos_list

    def get_minimum_expected_distance_from_recipe(
        self, recipe_data: Dict[str, Any]
    ) -> float:
        """
        Get 2x the smallest radius of objects in the recipe.

        Parameters
        ----------
        recipe_data
            Dictionary containing recipe data with object definitions.

        Returns
        -------
        :
            The minimum expected distance between packed objects, calculated as
            2 times the smallest radius of the ingredients in the recipe.
        """
        return 2 * min(
            [val for val in self.get_ingredient_radii(recipe_data=recipe_data).values()]
        )

    def get_packed_minimum_distance(
        self, pairwise_distance_dict: Dict[str, Any]
    ) -> float:
        """
        Get the minimum distance between packed objects.

        Parameters
        ----------
        pairwise_distance_dict
            Dictionary containing pairwise distances between packed objects.

        Returns
        -------
        :
            The minimum distance between packed objects.
        """
        return min(
            self.combine_results_from_ingredients(
                self.combine_results_from_seeds(pairwise_distance_dict)
            )
        )

    def get_number_of_ingredients_packed(
        self,
        ingredient_keys: Optional[list[str]] = None,
    ) -> Dict[str, float]:
        """
        Returns the number of ingredients packed.

        Parameters
        ----------
        ingredient_keys
            List of ingredient keys to analyze. If None, analyzes all ingredients.

        Returns
        -------
        :
            Dictionary mapping ingredient keys to average number packed.
        """
        avg_num_packed = {}
        for ingr_key in ingredient_keys:
            ingredient_packing_dict = self.all_objs.get(ingr_key)
            if not ingredient_packing_dict:
                val = 0
            else:
                ingredients_packed = 0
                for packing_dict in ingredient_packing_dict.values():
                    ingredients_packed += len(packing_dict["r"])
                val = ingredients_packed / self.num_packings
            avg_num_packed[ingr_key] = val

        return avg_num_packed

    def get_ingredient_radii(
        self,
        recipe_data: Dict[str, Any],
    ) -> Dict[str, float]:
        """
        Returns the radii of ingredients packed.

        Parameters
        ----------
        recipe_data
            Dictionary containing recipe data with object definitions.

        Returns
        -------
        :
            Dictionary mapping ingredient keys to their radii.
        """
        ingredient_radii = {}
        for object_key, object_values in recipe_data.get("objects").items():
            if "radius" in object_values:
                ingredient_radii[object_key] = object_values["radius"]
        return ingredient_radii

    def read_dict_from_glob_file(
        self,
        glob_str: str,
    ) -> Dict:
        """
        Read dictionary from a file matching the glob pattern.

        Parameters
        ----------
        glob_str
            Glob pattern to match files.

        Returns
        -------
        :
            Dictionary loaded from the matching JSON file, or None if no file found.
        """
        glob_to_distance_file = self.packing_results_path.glob(glob_str)
        for path_to_distance_file in glob_to_distance_file:
            if path_to_distance_file.is_file() and (
                path_to_distance_file.suffix == ".json"
            ):
                return self.loadJSON(path_to_distance_file)
        log.warning(
            f"No file found matching glob pattern {glob_str} in {self.packing_results_path}"
        )
        return {}

    def run_distance_analysis(
        self,
        md_object: MarkdownWriter,
        recipe_data: Dict[str, Any],
        pairwise_distance_dict: Optional[Dict[str, Any]],
        figure_path: Path,
        output_image_location: Union[Path, str],
    ) -> None:
        """
        Runs distance analysis on the given packing and adds it to the analysis report.

        Parameters
        ----------
        md_object
            Markdown writer object to add content to.
        recipe_data
            Dictionary containing recipe data.
        pairwise_distance_dict
            Dictionary containing pairwise distance data.
        figure_path
            Path to figures directory.
        output_image_location
            Location for output images in the markdown file.
        """
        expected_minimum_distance = self.get_minimum_expected_distance_from_recipe(
            recipe_data
        )
        if pairwise_distance_dict is not None:
            all_pairwise_distances = self.combine_results_from_seeds(
                pairwise_distance_dict
            )

            packed_minimum_distance = self.get_packed_minimum_distance(
                pairwise_distance_dict
            )

            md_object.add_header(level=1, header="Distance analysis")
            md_object.add_line(
                f"Expected minimum distance: {expected_minimum_distance:.2f}"
            )
            md_object.add_line(
                f"Actual minimum distance: {packed_minimum_distance:.2f}\n"
            )

            if expected_minimum_distance > packed_minimum_distance:
                md_object.add_header(level=2, header="Possible errors")
                md_object.add_list(
                    [
                        f"Packed minimum distance {packed_minimum_distance:.2f}"
                        " is less than the "
                        f"expected minimum distance {expected_minimum_distance:.2f}\n"
                    ]
                )

            img_list = []
            for ingr_key in all_pairwise_distances:
                ingr_distance_histo_path = figure_path.glob(
                    f"{ingr_key}_pairwise_distances_*.png"
                )
                for img_path in ingr_distance_histo_path:
                    img_list.append(
                        md_object.add_inline_image(
                            text=f"Distance distribution {ingr_key}",
                            filepath=f"{output_image_location}/{img_path.name}",
                        )
                    )

            df = pd.DataFrame(
                {
                    "Ingredient key": list(all_pairwise_distances.keys()),
                    "Pairwise distance distribution": img_list,
                }
            )

            md_object.add_table(header="", table=df)

    def get_ingredient_key_from_object_or_comp_name(
        self, search_name: str, ingredient_key_dict: Dict[str, Dict[str, str]]
    ) -> Optional[str]:
        """
        Returns the ingredient key if object or composition name is given.

        Parameters
        ----------
        search_name
            Name to search for in the ingredient key dictionary.
        ingredient_key_dict
            Dictionary mapping ingredient keys to name mappings.

        Returns
        -------
        :
            The ingredient key if found, otherwise None.
        """
        for ingredient_key, name_mappings in ingredient_key_dict.items():
            if search_name in name_mappings.values():
                return ingredient_key

    def get_partner_pair_dict(
        self,
        recipe_data: Dict[str, Any],
        combined_pairwise_distance_dict: Dict[str, list[float]],
        avg_num_packed: Dict[str, float],
    ) -> Dict[str, Dict[str, Union[float, int]]]:
        """
        Creates a partner pair dictionary.

        Parameters
        ----------
        recipe_data
            Dictionary containing recipe data.
        combined_pairwise_distance_dict
            Dictionary of combined pairwise distances.
        avg_num_packed
            Dictionary of average number packed per ingredient.

        Returns
        -------
        :
            Dictionary with partner pair information including binding probability,
            touching radius, and number packed.
        """
        partner_pair_dict = {}
        for ingredient_key, name_mappings in self.ingredient_key_dict.items():
            object_name = name_mappings["object_name"]
            if "partners" in recipe_data["objects"][object_name]:
                partner_list = recipe_data["objects"][object_name]["partners"]
                ingredient_radius = recipe_data["objects"][object_name]["radius"]
                for partner in partner_list.all_partners:
                    partner_object_name = partner.name
                    binding_probability = partner.binding_probability
                    partner_radius = recipe_data["objects"][partner_object_name][
                        "radius"
                    ]
                    partner_ingr_key = self.get_ingredient_key_from_object_or_comp_name(
                        partner_object_name, self.ingredient_key_dict
                    )
                    paired_key = get_paired_key(
                        combined_pairwise_distance_dict,
                        ingredient_key,
                        partner_ingr_key,
                    )
                    if paired_key not in partner_pair_dict:
                        partner_pair_dict[paired_key] = {
                            "binding_probability": binding_probability,
                            "touching_radius": ingredient_radius + partner_radius,
                            "num_packed": avg_num_packed[ingredient_key],
                        }

        return partner_pair_dict

    def run_partner_analysis(
        self,
        md_object: MarkdownWriter,
        recipe_data: Dict[str, Any],
        combined_pairwise_distance_dict: Dict[str, list[float]],
        ingredient_radii: Dict[str, float],
        avg_num_packed: Dict[str, float],
    ) -> None:
        """
        Runs an analysis of partner packings.

        Parameters
        ----------
        md_object
            Markdown writer object to add content to.
        recipe_data
            Dictionary containing recipe data.
        combined_pairwise_distance_dict
            Dictionary of combined pairwise distances.
        ingredient_radii
            Dictionary of ingredient radii.
        avg_num_packed
            Dictionary of average number packed per ingredient.
        """
        partner_pair_dict = self.get_partner_pair_dict(
            recipe_data,
            combined_pairwise_distance_dict,
            avg_num_packed,
        )
        if len(partner_pair_dict):
            md_object.add_header(header="Partner Analysis")
            partner_data = []
            for paired_key, partner_values in partner_pair_dict.items():
                pairwise_distances = np.array(
                    combined_pairwise_distance_dict[paired_key]
                )
                padded_radius = 1.2 * partner_values["touching_radius"]
                close_fraction = (
                    np.count_nonzero(pairwise_distances < padded_radius)
                    / partner_values["num_packed"]
                )
                partner_data.append(
                    {
                        "Ingredient pair": paired_key,
                        "Touching radius": partner_values["touching_radius"],
                        "Binding probability": partner_values["binding_probability"],
                        "Close packed fraction": close_fraction,
                    }
                )

            df = pd.DataFrame(partner_data)

            md_object.add_table(header="", table=df)

    def create_report(
        self,
        recipe_data: Dict[str, Any],
        ingredient_keys: Optional[list[str]] = None,
        report_output_path: Optional[Union[Path, str]] = None,
        output_image_location: Optional[Union[Path, str]] = None,
        run_distance_analysis: bool = True,
        run_partner_analysis: bool = True,
    ) -> None:
        """
        Creates a markdown file with various analyses included.

        Parameters
        ----------
        recipe_data
            Dictionary containing recipe data for the packing being analyzed.
        ingredient_keys
            List of ingredient keys to analyze. If None, uses all available keys.
        report_output_path
            Path to save the report. If None, uses self.output_path.
        output_image_location
            Path to look for output images for the markdown file.
        run_distance_analysis
            Whether to run distance analysis.
        run_partner_analysis
            Whether to run partner analysis.
        """
        if report_output_path is None:
            report_output_path = self.output_path
        report_output_path = Path(report_output_path)

        if not hasattr(self, "ingredient_key_dict"):
            self.ingredient_key_dict = self.read_dict_from_glob_file(
                "ingredient_keys_*"
            )

        if ingredient_keys is None:
            ingredient_keys = list(self.ingredient_key_dict.keys())

        avg_num_packed = self.get_number_of_ingredients_packed(
            ingredient_keys=ingredient_keys
        )
        ingredient_radii = self.get_ingredient_radii(recipe_data=recipe_data)

        if not hasattr(self, "pairwise_distance_dict"):
            self.pairwise_distance_dict = self.read_dict_from_glob_file(
                "pairwise_distances_*.json"
            )
        combined_pairwise_distance_dict = self.combine_results_from_seeds(
            self.pairwise_distance_dict
        )

        df = pd.DataFrame(
            {
                "Ingredient name": list(ingredient_keys),
                "Encapsulating radius": list(ingredient_radii.values()),
                "Average number packed": list(avg_num_packed.values()),
            }
        )

        # path to save report and other outputs
        if output_image_location is None:
            output_image_location = self.output_path
        output_image_location = Path(output_image_location)

        md_object = MarkdownWriter(
            title="Packing analysis report",
            output_path=report_output_path,
            output_image_location=output_image_location,
            report_name="analysis_report",
        )

        md_object.add_header(
            header=f"Analysis for packing results located at {self.packing_results_path}"
        )

        md_object.add_table(header="", table=df)

        # path where packing results are stored
        packing_results_path = self.packing_results_path
        figure_path = packing_results_path / "figures"

        md_object.add_images(
            header="Packing image",
            image_text=["Packing image"],
            filepaths=list(figure_path.glob("packing_image_*.png")),
        )

        if run_distance_analysis:
            # TODO: take packing distance dict as direct input for live mode
            self.run_distance_analysis(
                md_object,
                recipe_data,
                self.pairwise_distance_dict,
                figure_path,
                output_image_location,
            )

        if run_partner_analysis:
            self.run_partner_analysis(
                md_object,
                recipe_data,
                combined_pairwise_distance_dict,
                ingredient_radii,
                avg_num_packed,
            )

        md_object.write_file()

    def run_analysis_workflow(
        self,
        analysis_config: Dict[str, Any],
        recipe_data: Dict[str, Any],
    ) -> None:
        """
        Run the complete analysis workflow.

        Parameters
        ----------
        analysis_config
            Dictionary containing analysis configuration options.
        recipe_data
            Dictionary containing recipe data.
        """
        all_objs, all_pos_list = self.get_packed_object_data(self.packing_results_path)

        self.num_packings = len(all_pos_list)
        self.num_seeds_per_packing = np.array(
            [len(packing_dict) for packing_dict in all_pos_list]
        )

        log.debug("Starting analysis workflow...")

        if analysis_config.get("create_report"):
            self.create_report(
                recipe_data=recipe_data,
                **analysis_config["create_report"],
            )

    def histogram(
        self,
        distances: Union[np.ndarray, list[float]],
        filename: Union[Path, str],
        title_str: str = "",
        x_label: str = "",
        y_label: str = "",
        add_to_result: bool = True,
        save_png: bool = False,
    ) -> None:
        """
        Create and save a histogram of distances.

        Parameters
        ----------
        distances
            Array or list of distance values.
        filename
            Path to save the histogram image.
        title_str
            Title for the histogram.
        x_label
            Label for the x-axis.
        y_label
            Label for the y-axis.
        add_to_result
            Whether to add histogram to result file and display on web page.
        save_png
            Whether to save as PNG using matplotlib.
        """
        if (
            add_to_result
            and hasattr(self, "helper")
            and self.helper is not None
            and hasattr(self.helper, "plot_data")
        ):
            # add histogrm to result file and display on the web page
            self.helper.plot_data.add_histogram(
                title=f"{title_str}: {x_label}",
                xaxis_title=x_label,
                traces={y_label: np.array(distances)},
            )
        if save_png:
            # use matplotlib to create histogram and save as png
            plt.clf()
            # calculate histogram
            nbins = int(np.sqrt(len(distances)))
            if nbins < 2:
                return
            y, bin_edges = np.histogram(distances, bins=nbins)
            bincenters = 0.5 * (bin_edges[1] + bin_edges[:-1])

            # calculate standard error for values in each bin
            bin_inds = np.digitize(distances, bin_edges)
            x_err_vals = np.zeros(y.shape)
            for bc in range(nbins):
                dist_vals = distances[bin_inds == (bc + 1)]
                if len(dist_vals) > 1:
                    x_err_vals[bc] = np.std(dist_vals)
                else:
                    x_err_vals[bc] = 0
            y_err_vals = np.sqrt(y * (1 - y / np.sum(y)))
            # set bin width
            dbin = 0.9 * (bincenters[1] - bincenters[0])
            plt.bar(
                bincenters, y, width=dbin, color="r", xerr=x_err_vals, yerr=y_err_vals
            )
            plt.title(title_str)
            plt.xlabel(x_label)
            plt.ylabel(y_label)
            plt.savefig(filename)
            plt.close()

    def plot(
        self, rdf: np.ndarray, radii: np.ndarray, file_name: Union[Path, str]
    ) -> None:
        """
        Plot radial distribution function.

        Parameters
        ----------
        rdf
            Radial distribution function values.
        radii
            Radial distance values.
        file_name
            Path to save the plot.
        """
        plt.clf()
        matplotlib.rc("font", size=14)
        matplotlib.rc("figure", figsize=(5, 4))
        plt.plot(radii, rdf, linewidth=3)
        plt.xlabel(r"distance $r$ in $\AA$")
        plt.ylabel(r"radial distribution function $g(r)$")
        plt.savefig(file_name)

    def simpleplot(
        self,
        X: Union[np.ndarray, list[float]],
        Y: Union[np.ndarray, list[float]],
        filename: Union[Path, str],
        w: int = 3,
        title_str: str = "",
        x_label: str = "",
        y_label: str = "",
    ) -> None:
        """
        Create a simple line plot.

        Parameters
        ----------
        X
            X-axis values.
        Y
            Y-axis values.
        filename
            Path to save the plot.
        w
            Line width.
        title_str
            Title for the plot.
        x_label
            Label for the x-axis.
        y_label
            Label for the y-axis.
        """
        plt.clf()
        plt.plot(X, Y, linewidth=w)
        plt.title(title_str)
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.savefig(filename)

    def build_grid(
        self,
    ) -> None:
        """
        Build the grid for the environment and log the time taken.
        """
        t1 = time()
        self.env.buildGrid()
        t2 = time()
        gridTime = t2 - t1
        log.debug(f"Time to build grid: {gridTime:0.2f}")

    def pack(
        self,
        seed: int = 20,
        show_plotly_plot: bool = True,
        **kwargs: Any,
    ) -> None:
        """
        Pack the grid with ingredients and optionally display visualization.

        Parameters
        ----------
        seed
            Random seed for packing.
        show_plotly_plot
            Whether to show the plotly visualization.
        **kwargs
            Additional keyword arguments passed to pack_grid.
        """
        if show_plotly_plot:
            self.plotly.update_title(self.env.place_method)

        t1 = time()
        results = self.env.pack_grid(seedNum=seed, **kwargs)
        self.seed_to_results[seed] = results
        t2 = time()
        run_time = t2 - t1
        log.debug(f"Time to run pack_grid for {self.env.place_method}: {run_time:0.2f}")
        log.debug(f"Number placed: {len(self.env.packed_objects.get_ingredients())}")
        if show_plotly_plot:
            min_bound, max_bound = self.env.get_bounding_box_limits()
            extents = max_bound - min_bound
            self.plotly.plot["data"] = []
            self.plotly.plot.layout.shapes = ()
            self.plotly.plot.update_xaxes(
                range=[min_bound[0] - 0.2 * extents[0], max_bound[0] + 0.2 * extents[0]]
            )
            self.plotly.plot.update_yaxes(
                range=[min_bound[1] - 0.2 * extents[1], max_bound[1] + 0.2 * extents[1]]
            )
            self.plotly.update_title(
                f"{self.env.place_method} took {str(round(t2 - t1, 2))}s, "
                f"packed {len(self.env.packed_objects.get_ingredients())}"
            )
            self.plotly.make_grid_heatmap(self.env)
            self.plotly.add_ingredient_positions(self.env)
            self.plotly.show()

    def set_ingredient_color(self, ingr: Ingredient) -> Optional[np.ndarray]:
        """
        Sets the color of an ingredient.

        Parameters
        ----------
        ingr
            The ingredient object.

        Returns
        -------
        :
            RGB color array normalized to [0,1] range, or None if no color set.
        """
        color = None

        if ingr.color is not None:
            color = (
                ingr.color
                if all([x <= 1 for x in ingr.color])
                else np.array(ingr.color) / 255
            )

        return color

    def add_ingredient_positions_to_plot(
        self,
        ax: Axes,
        ingr: Ingredient,
        color: Optional[np.ndarray],
        seed_index: int,
        ingredient_position_dict: Dict[str, Dict[str, list[list[float]]]],
        extents: np.ndarray,
    ) -> Axes:
        """
        Adds 2D images of ingredient positions to axis.

        Parameters
        ----------
        ax
            Matplotlib axes object to add patches to.
        ingr
            The ingredient object.
        color
            RGB color for the ingredient.
        seed_index
            Index of the current seed.
        ingredient_position_dict
            Dictionary containing ingredient positions by seed.
        extents
            Extents of the bounding box for periodic boundary conditions.

        Returns
        -------
        :
            Updated matplotlib axes object.
        """
        string_seed_index = str(seed_index)
        seed_ingredient_positions = ingredient_position_dict[string_seed_index][
            ingr.name
        ]
        for i, pos in enumerate(seed_ingredient_positions):
            ax.add_patch(
                Circle(
                    (pos[0], pos[1]),
                    ingr.encapsulating_radius,
                    edgecolor="black",
                    facecolor=color,
                )
            )

            #  Plot "image" particles to verify that periodic boundary conditions are working
            radius = ingr.encapsulating_radius
            if autopack.testPeriodicity:
                if pos[0] < radius:
                    ax.add_patch(
                        Circle(
                            (pos[0] + extents[0], pos[1]),
                            radius,
                            facecolor=color,
                        )
                    )
                elif pos[0] > (extents[0] - radius):
                    ax.add_patch(
                        Circle(
                            (pos[0] - extents[0], pos[1]),
                            radius,
                            facecolor=color,
                        )
                    )
                if pos[1] < radius:
                    ax.add_patch(
                        Circle(
                            (pos[0], pos[1] + extents[1]),
                            radius,
                            facecolor=color,
                        )
                    )
                elif pos[1] > (extents[1] - radius):
                    ax.add_patch(
                        Circle(
                            (pos[0], pos[1] - extents[1]),
                            radius,
                            facecolor=color,
                        )
                    )

            if i == 0:  # len(ingrpos)-1:
                continue

            if ingr.type == "Grow":
                plt.plot(
                    [
                        seed_ingredient_positions[-i][0],
                        seed_ingredient_positions[-i - 1][0],
                    ],
                    [
                        seed_ingredient_positions[-i][1],
                        seed_ingredient_positions[-i - 1][1],
                    ],
                    "k-",
                    lw=2,
                )
                # plot the sphere
                # if ingr.use_rbsphere:
                #     (
                #         ext_recipe,
                #         pts,
                #     ) = ingr.getInterpolatedSphere(
                #         seed_ingredient_positions[-i - 1],
                #         seed_ingredient_positions[-i],
                #     )
                #     for pt in pts:
                #         ax.add_patch(
                #             Circle(
                #                 (pt[0], pt[1]),
                #                 ingr.min_radius,
                #                 edgecolor="black",
                #                 facecolor=color,
                #             )
                #         )
        return ax

    def getHaltonUnique(self, n: int) -> np.ndarray:
        """
        Generate unique Halton sequence numbers.

        Parameters
        ----------
        n
            Number of unique seeds to generate.

        Returns
        -------
        :
            Array of unique integer seeds.
        """
        seeds_f = np.array(halton(int(n * 1.5))) * int(n * 1.5)
        seeds_int = np.array(np.round(seeds_f), "int")
        _, indices_u = np.unique(seeds_int, return_index=True)
        seeds_i = np.array(seeds_int[np.sort(indices_u)])[:n]
        return seeds_i

    def update_distance_distribution_dictionaries(
        self,
        ingr: Ingredient,
        center_distance_dict: Dict[str, Dict[str, list[float]]],
        pairwise_distance_dict: Dict[str, Dict[str, list[float]]],
        ingredient_position_dict: Dict[str, Dict[str, list[list[float]]]],
        ingredient_angle_dict: Dict[str, Dict[str, list[float]]],
        ingredient_occurence_dict: Dict[str, Dict[str, list[int]]],
        seed_index: int,
        center: list[float],
    ) -> Tuple[
        Dict[str, Dict[str, list[float]]],
        Dict[str, Dict[str, list[float]]],
        Dict[str, Dict[str, list[list[float]]]],
        Dict[str, Dict[str, list[float]]],
        Dict[str, Dict[str, list[int]]],
    ]:
        """
        Update dictionaries that store distance and angle information.

        Parameters
        ----------
        ingr
            The ingredient object.
        center_distance_dict
            Dictionary storing distances from center by seed and ingredient.
        pairwise_distance_dict
            Dictionary storing pairwise distances by seed and ingredient.
        ingredient_position_dict
            Dictionary storing positions by seed and ingredient.
        ingredient_angle_dict
            Dictionary storing angles by seed and ingredient.
        ingredient_occurence_dict
            Dictionary storing occurrence counts by seed and ingredient.
        seed_index
            Index of the current seed.
        center
            Center coordinates for distance calculations.

        Returns
        -------
        :
            Updated versions of all input dictionaries.
        """
        string_seed_index = str(seed_index)
        if ingr.name not in center_distance_dict[string_seed_index]:
            center_distance_dict[string_seed_index][ingr.name] = []
            pairwise_distance_dict[string_seed_index][ingr.name] = []
            ingredient_position_dict[string_seed_index][ingr.name] = []
            ingredient_angle_dict[string_seed_index][ingr.name] = []
            ingredient_occurence_dict[string_seed_index][ingr.name] = []

        get_angles = False
        if ingr.packing_mode == "gradient" and self.env.use_gradient:
            if isinstance(ingr.gradient, list):
                if len(ingr.gradient) > 1 or len(ingr.gradient) == 0:
                    self.center = center
                else:
                    self.center = center = self.env.gradients[
                        ingr.gradient[0]
                    ].mode_settings.get("center", center)
            else:
                self.center = center = self.env.gradients[
                    ingr.gradient
                ].mode_settings.get("center", center)
            get_angles = True

        # get angles wrt gradient
        (
            seed_ingredient_positions,
            seed_distances_from_center,
            seed_distances_between_ingredients,
            seed_angles,
        ) = self.get_distances_and_angles(ingr.name, center, get_angles=get_angles)

        center_distance_dict[string_seed_index][
            ingr.name
        ] = seed_distances_from_center.tolist()
        pairwise_distance_dict[string_seed_index][
            ingr.name
        ] = seed_distances_between_ingredients.tolist()
        ingredient_position_dict[string_seed_index][
            ingr.name
        ] = seed_ingredient_positions.tolist()
        ingredient_angle_dict[string_seed_index][ingr.name] = seed_angles.tolist()
        ingredient_occurence_dict[string_seed_index][ingr.name].append(
            len(seed_ingredient_positions)
        )

        return (
            center_distance_dict,
            pairwise_distance_dict,
            ingredient_position_dict,
            ingredient_angle_dict,
            ingredient_occurence_dict,
        )

    def update_pairwise_distances(
        self,
        ingr: Ingredient,
        recipe: Any,
        pairwise_distance_dict: Dict[str, Dict[str, list[float]]],
        seed_index: int,
    ) -> Dict[str, Dict[str, list[float]]]:
        """
        Adds cross-ingredient distances for pairwise distance dictionary.

        Parameters
        ----------
        ingr
            The current ingredient.
        recipe
            Recipe object containing all ingredients.
        pairwise_distance_dict
            Dictionary storing pairwise distances.
        seed_index
            Index of the current seed.

        Returns
        -------
        :
            Updated pairwise distance dictionary.
        """
        string_seed_index = str(seed_index)
        for ingr2 in recipe.ingredients:
            if ingr2.name == ingr.name:
                continue
            if not check_paired_key(
                pairwise_distance_dict[string_seed_index],
                ingr.name,
                ingr2.name,
            ):
                pairwise_distance_dict[string_seed_index][
                    f"{ingr.name}_{ingr2.name}"
                ] = self.calc_pairwise_distances(ingr.name, ingr2.name).tolist()

        return pairwise_distance_dict

    def process_ingredients_in_recipe(
        self,
        recipe: Any,
        center_distance_dict: Dict[str, Dict[str, list[float]]],
        pairwise_distance_dict: Dict[str, Dict[str, list[float]]],
        ingredient_position_dict: Dict[str, Dict[str, list[list[float]]]],
        ingredient_angle_dict: Dict[str, Dict[str, list[float]]],
        ingredient_occurence_dict: Dict[str, Dict[str, list[int]]],
        ingredient_key_dict: Dict[str, Dict[str, str]],
        seed_index: int,
        center: list[float],
        plot_figures: bool,
        two_d: bool,
        ax: Optional[Axes],
        extents: np.ndarray,
    ) -> Tuple[
        Dict[str, Dict[str, list[float]]],
        Dict[str, Dict[str, list[float]]],
        Dict[str, Dict[str, list[list[float]]]],
        Dict[str, Dict[str, list[float]]],
        Dict[str, Dict[str, list[int]]],
        Dict[str, Dict[str, str]],
        Optional[Axes],
    ]:
        """
        Updates distance/angle dictionaries and creates plots for ingredients in recipe.

        Parameters
        ----------
        recipe
            Recipe object containing ingredients.
        center_distance_dict
            Dictionary storing center distances.
        pairwise_distance_dict
            Dictionary storing pairwise distances.
        ingredient_position_dict
            Dictionary storing ingredient positions.
        ingredient_angle_dict
            Dictionary storing ingredient angles.
        ingredient_occurence_dict
            Dictionary storing ingredient occurrences.
        ingredient_key_dict
            Dictionary mapping ingredient keys to names.
        seed_index
            Index of the current seed.
        center
            Center coordinates.
        plot_figures
            Whether to create plots.
        two_d
            Whether this is a 2D analysis.
        ax
            Matplotlib axes for plotting.
        extents
            Extents of the bounding box.

        Returns
        -------
        :
            Updated versions of all input dictionaries and axes.
        """
        for ingr in recipe.ingredients:
            # set ingredient color
            color = self.set_ingredient_color(ingr)

            if ingr.name not in ingredient_key_dict:
                ingredient_key_dict[ingr.name] = {}
                ingredient_key_dict[ingr.name][
                    "composition_name"
                ] = ingr.composition_name
                ingredient_key_dict[ingr.name]["object_name"] = ingr.object_name

            # calculate distances and angles for ingredient
            (
                center_distance_dict,
                pairwise_distance_dict,
                ingredient_position_dict,
                ingredient_angle_dict,
                ingredient_occurence_dict,
            ) = self.update_distance_distribution_dictionaries(
                ingr,
                center_distance_dict,
                pairwise_distance_dict,
                ingredient_position_dict,
                ingredient_angle_dict,
                ingredient_occurence_dict,
                seed_index,
                center,
            )

            # calculate cross ingredient_distances
            pairwise_distance_dict = self.update_pairwise_distances(
                ingr, recipe, pairwise_distance_dict, seed_index
            )

            if plot_figures and two_d and ax is not None:
                ax = self.add_ingredient_positions_to_plot(
                    ax=ax,
                    ingr=ingr,
                    color=color,
                    seed_index=seed_index,
                    ingredient_position_dict=ingredient_position_dict,
                    extents=extents,
                )

        return (
            center_distance_dict,
            pairwise_distance_dict,
            ingredient_position_dict,
            ingredient_angle_dict,
            ingredient_occurence_dict,
            ingredient_key_dict,
            ax,
        )

    def combine_results_from_seeds(
        self, input_dict: Dict[str, Dict[str, list[Any]]]
    ) -> Dict[str, list[Any]]:
        """
        Combines results from multiple seeds into one dictionary.

        Parameters
        ----------
        input_dict
            Dictionary with seed indices as keys and ingredient dictionaries as values.

        Returns
        -------
        :
            Dictionary with ingredient names as keys and combined value lists.
        """
        output_dict = {}
        for _, ingr_dict in input_dict.items():
            for ingr_name, value_list in ingr_dict.items():
                if ingr_name not in output_dict:
                    output_dict[ingr_name] = []
                output_dict[ingr_name].extend(value_list)

        return output_dict

    def combine_results_from_ingredients(
        self, input_dict: Dict[str, list[Any]]
    ) -> list[Any]:
        """
        Combines results from multiple ingredients into one list.

        Parameters
        ----------
        input_dict
            Dictionary with ingredient names as keys and value lists.

        Returns
        -------
        :
            Combined list of all values from all ingredients.
        """
        output_list = []
        for ingr_name, value_list in input_dict.items():
            output_list.extend(value_list)
        return output_list

    def pack_one_seed(
        self,
        seed_index: int,
        seed_list: Union[list[int], np.ndarray],
        bounding_box: list[list[float]],
        center_distance_dict: Dict[str, Dict[str, list[float]]],
        pairwise_distance_dict: Dict[str, Dict[str, list[float]]],
        ingredient_position_dict: Dict[str, Dict[str, list[list[float]]]],
        ingredient_angle_dict: Dict[str, Dict[str, list[float]]],
        ingredient_occurence_dict: Dict[str, Dict[str, list[int]]],
        ingredient_key_dict: Dict[str, Dict[str, str]],
        get_distance_distribution: bool = False,
        image_export_options: Optional[Dict[str, Any]] = None,
        show_grid: bool = False,
        plot_figures: bool = False,
        save_gradient_data_as_image: bool = False,
        clean_grid_cache: bool = False,
    ) -> Tuple[
        Dict[str, Dict[str, list[float]]],
        Dict[str, Dict[str, list[float]]],
        Dict[str, Dict[str, list[list[float]]]],
        Dict[str, Dict[str, list[float]]],
        Dict[str, Dict[str, list[int]]],
        Dict[str, Dict[str, str]],
    ]:
        """
        Packs one seed of a recipe and returns the recipe object.

        Parameters
        ----------
        seed_index
            Index of the seed in the seed list.
        seed_list
            List of all seeds to be used.
        bounding_box
            Bounding box coordinates [[min_x, min_y, min_z], [max_x, max_y, max_z]].
        center_distance_dict
            Dictionary to store center distances.
        pairwise_distance_dict
            Dictionary to store pairwise distances.
        ingredient_position_dict
            Dictionary to store ingredient positions.
        ingredient_angle_dict
            Dictionary to store ingredient angles.
        ingredient_occurence_dict
            Dictionary to store ingredient occurrences.
        ingredient_key_dict
            Dictionary mapping ingredient keys to names.
        get_distance_distribution
            Whether to calculate distance distributions.
        image_export_options
            Options for image export.
        show_grid
            Whether to show grid visualization.
        plot_figures
            Whether to create and save plots.
        save_gradient_data_as_image
            Whether to save gradient data as images.
        clean_grid_cache
            Whether to clean grid cache after packing.

        Returns
        -------
        :
            Updated versions of all distance and position dictionaries.
        """
        seed = int(seed_list[seed_index])
        string_seed_index = str(seed_index)
        seed_basename = self.env.add_seed_number_to_base_name(seed)
        self.env.reset()
        np.random.seed(seed)
        self.build_grid()
        two_d = self.env.is_two_d()
        use_simularium = False
        self.pack(
            seed=seed,
            # TODO: fix this to disable plotly if using simularium
            show_plotly_plot=(show_grid and two_d) and not use_simularium,
            clean_grid_cache=clean_grid_cache,
        )

        self.center = self.env.grid.getCenter()

        ax = None
        extents = np.zeros(2)
        if plot_figures and two_d:
            extents = self.env.get_bounding_box_size()
            fig = plt.figure()
            ax = fig.add_subplot(111)

        if get_distance_distribution:
            center_distance_dict[string_seed_index] = {}
            pairwise_distance_dict[string_seed_index] = {}
            ingredient_position_dict[string_seed_index] = {}
            ingredient_angle_dict[string_seed_index] = {}
            ingredient_occurence_dict[string_seed_index] = {}

            if hasattr(self, "center"):
                center = self.center
            else:
                center = self.env.grid.getCenter()

            # Process all recipes in order
            recipes_to_process = []

            # Add exterior recipe if it exists
            if self.env.exteriorRecipe:
                recipes_to_process.append(self.env.exteriorRecipe)

            # Add compartment recipes if they exist
            for compartment in self.env.compartments:
                if compartment.surfaceRecipe:
                    recipes_to_process.append(compartment.surfaceRecipe)
                if compartment.innerRecipe:
                    recipes_to_process.append(compartment.innerRecipe)

            # Process each recipe
            for recipe in recipes_to_process:
                (
                    center_distance_dict,
                    pairwise_distance_dict,
                    ingredient_position_dict,
                    ingredient_angle_dict,
                    ingredient_occurence_dict,
                    ingredient_key_dict,
                    ax,
                ) = self.process_ingredients_in_recipe(
                    recipe=recipe,
                    center_distance_dict=center_distance_dict,
                    pairwise_distance_dict=pairwise_distance_dict,
                    ingredient_position_dict=ingredient_position_dict,
                    ingredient_angle_dict=ingredient_angle_dict,
                    ingredient_occurence_dict=ingredient_occurence_dict,
                    ingredient_key_dict=ingredient_key_dict,
                    seed_index=seed_index,
                    center=center,
                    plot_figures=plot_figures,
                    two_d=two_d,
                    ax=ax,
                    extents=extents,
                )

            if plot_figures and two_d:
                ax.set_aspect(1.0)
                ax.axhline(y=bounding_box[0][1], color="k")
                ax.axhline(y=bounding_box[1][1], color="k")
                ax.axvline(x=bounding_box[0][0], color="k")
                ax.axvline(x=bounding_box[1][0], color="k")
                ax.set_xlim((bounding_box[0][0], bounding_box[1][0]))
                ax.set_ylim((bounding_box[0][1], bounding_box[1][1]))

                plt.savefig(self.figures_path / f"packing_image_{seed_basename}.png")
                plt.close()

        if image_export_options is not None:
            env_image_writer = ImageWriter(
                env=self.env,
                name=seed_basename,
                output_path=self.figures_path,
                **image_export_options,
            )
            env_image_writer = self.env.create_voxelization(env_image_writer)
            env_image_writer.export_image()

        if save_gradient_data_as_image:
            gradient_data_figure_path = self.figures_path / "gradient_data_figures"
            gradient_data_figure_path.mkdir(exist_ok=True)
            for _, gradient in self.env.gradients.items():
                grid_image_writer = ImageWriter(
                    env=self.env,
                    name=f"{seed_basename}_grid_data",
                    output_path=gradient_data_figure_path,
                )
                grid_image_writer = gradient.create_voxelization(grid_image_writer)
                grid_image_writer.export_image()
        return (
            center_distance_dict,
            pairwise_distance_dict,
            ingredient_position_dict,
            ingredient_angle_dict,
            ingredient_occurence_dict,
            ingredient_key_dict,
        )

    def doloop(
        self,
        recipe_data: Dict[str, Any],
        packing_config_data: Dict[str, Any],
        bounding_box: list[list[float]],
        get_distance_distribution: bool = True,
    ) -> None:
        """
        Runs multiple packings of the same recipe in a loop.

        This workflow also runs various analyses and saves the output figures
        and data at the location set by the environment. The output data is
        also stored as an attribute on the environment object and on the
        Analysis class instance.

        Parameters
        ----------
        recipe_data
            Dictionary containing recipe data.
        packing_config_data
            Dictionary containing packing configuration data.
        bounding_box
            List of two lists containing the minimum and maximum coordinates
            of the bounding box.
        get_distance_distribution
            Whether to calculate and store distance and angle distributions.

        Notes
        -----
        Outputs include:
        - {}_distance_dict: Dictionaries with various ingredient distances stored
        - images: packing image, histograms of distance, angle, and occurrence
          distributions as applicable for each seed, and a combined image
          across seeds
        """
        number_of_packings = packing_config_data["number_of_packings"]
        plot_figures = packing_config_data.get("save_plot_figures", True)
        show_grid = packing_config_data["show_grid_plot"]
        image_export_options = packing_config_data.get("image_export_options")

        if image_export_options is not None:
            global ImageWriter
            if "ImageWriter" not in globals():
                from cellpack.autopack.writers.ImageWriter import ImageWriter

        parallel = packing_config_data.get("parallel", False)
        save_gradient_data_as_image = packing_config_data.get(
            "save_gradient_data_as_image", False
        )
        clean_grid_cache = packing_config_data.get("clean_grid_cache", False)

        seed_list = get_seed_list(packing_config_data, recipe_data)
        if seed_list is None:
            seed_list = self.getHaltonUnique(number_of_packings)
        packing_basename = self.env.base_name
        np.savetxt(
            self.env.out_folder / f"seeds_{packing_basename}.txt",
            seed_list,
            delimiter=",",
        )

        center_distance_file = (
            self.env.out_folder / f"center_distances_{packing_basename}.json"
        )
        pairwise_distance_file = (
            self.env.out_folder / f"pairwise_distances_{packing_basename}.json"
        )
        ingredient_position_file = (
            self.env.out_folder / f"positions_{packing_basename}.json"
        )
        ingredient_angle_file = self.env.out_folder / f"angles_{packing_basename}.json"
        ingredient_occurences_file = (
            self.env.out_folder / f"occurences_{packing_basename}.json"
        )
        ingredient_key_file = (
            self.env.out_folder / f"ingredient_keys_{packing_basename}.json"
        )

        center_distance_dict = {}
        pairwise_distance_dict = {}
        ingredient_position_dict = {}
        ingredient_angle_dict = {}
        ingredient_occurence_dict = {}
        ingredient_key_dict = {}

        if parallel:
            num_processes = np.min(
                [
                    int(np.floor(0.8 * multiprocessing.cpu_count())),
                    number_of_packings,
                ]
            )
            with concurrent.futures.ProcessPoolExecutor(
                max_workers=num_processes
            ) as executor:
                futures = []
                for seed_index in range(number_of_packings):
                    futures.append(
                        executor.submit(
                            self.pack_one_seed,
                            seed_index=seed_index,
                            seed_list=seed_list,
                            bounding_box=bounding_box,
                            center_distance_dict=center_distance_dict,
                            pairwise_distance_dict=pairwise_distance_dict,
                            ingredient_position_dict=ingredient_position_dict,
                            ingredient_angle_dict=ingredient_angle_dict,
                            ingredient_occurence_dict=ingredient_occurence_dict,
                            ingredient_key_dict=ingredient_key_dict,
                            get_distance_distribution=get_distance_distribution,
                            image_export_options=image_export_options,
                            save_gradient_data_as_image=save_gradient_data_as_image,
                            clean_grid_cache=clean_grid_cache,
                        )
                    )
                for future in concurrent.futures.as_completed(futures):
                    (
                        seed_center_distance_dict,
                        seed_pairwise_distance_dict,
                        seed_ingredient_position_dict,
                        seed_ingredient_angle_dict,
                        seed_ingredient_occurence_dict,
                        seed_ingredient_key_dict,
                    ) = future.result()
                    center_distance_dict.update(seed_center_distance_dict)
                    pairwise_distance_dict.update(seed_pairwise_distance_dict)
                    ingredient_position_dict.update(seed_ingredient_position_dict)
                    ingredient_angle_dict.update(seed_ingredient_angle_dict)
                    ingredient_occurence_dict.update(seed_ingredient_occurence_dict)
                    ingredient_key_dict.update(seed_ingredient_key_dict)

        else:
            for seed_index in range(number_of_packings):
                (
                    center_distance_dict,
                    pairwise_distance_dict,
                    ingredient_position_dict,
                    ingredient_angle_dict,
                    ingredient_occurence_dict,
                    ingredient_key_dict,
                ) = self.pack_one_seed(
                    seed_index=seed_index,
                    seed_list=seed_list,
                    bounding_box=bounding_box,
                    center_distance_dict=center_distance_dict,
                    pairwise_distance_dict=pairwise_distance_dict,
                    ingredient_position_dict=ingredient_position_dict,
                    ingredient_angle_dict=ingredient_angle_dict,
                    ingredient_occurence_dict=ingredient_occurence_dict,
                    ingredient_key_dict=ingredient_key_dict,
                    get_distance_distribution=get_distance_distribution,
                    image_export_options=image_export_options,
                    show_grid=show_grid,
                    plot_figures=plot_figures,
                    save_gradient_data_as_image=save_gradient_data_as_image,
                    clean_grid_cache=clean_grid_cache,
                )

        self.writeJSON(center_distance_file, center_distance_dict)
        self.writeJSON(pairwise_distance_file, pairwise_distance_dict)
        self.writeJSON(ingredient_position_file, ingredient_position_dict)
        self.writeJSON(ingredient_angle_file, ingredient_angle_dict)
        self.writeJSON(ingredient_occurences_file, ingredient_occurence_dict)
        self.writeJSON(ingredient_key_file, ingredient_key_dict)

        all_ingredient_positions = self.combine_results_from_seeds(
            ingredient_position_dict
        )
        all_center_distances = self.combine_results_from_seeds(center_distance_dict)
        all_ingredient_distances = self.combine_results_from_seeds(
            pairwise_distance_dict
        )
        all_ingredient_occurences = self.combine_results_from_seeds(
            ingredient_occurence_dict
        )
        all_ingredient_angles = self.combine_results_from_seeds(ingredient_angle_dict)

        all_center_distance_array = np.array(
            self.combine_results_from_ingredients(all_center_distances)
        )
        all_pairwise_distance_array = np.array(
            self.combine_results_from_ingredients(all_ingredient_distances)
        )
        all_ingredient_position_array = np.array(
            self.combine_results_from_ingredients(all_ingredient_positions)
        )
        all_ingredient_angle_array = np.array(
            self.combine_results_from_ingredients(all_ingredient_angles)
        )

        self.ingredient_positions = all_ingredient_positions
        self.distances = all_ingredient_distances
        self.basename = packing_basename
        self.occurences = all_ingredient_occurences
        self.angles = all_ingredient_angles

        self.center_distance_dict = center_distance_dict
        self.pairwise_distance_dict = pairwise_distance_dict
        self.ingredient_position_dict = ingredient_position_dict
        self.ingredient_angle_dict = ingredient_angle_dict
        self.ingredient_occurence_dict = ingredient_occurence_dict
        self.ingredient_key_dict = ingredient_key_dict

        if plot_figures:
            self.env.loopThroughIngr(self.plot_position_histogram_for_ingredient)
            self.env.loopThroughIngr(self.plot_occurence_distribution)

            # plot pairwise distance histograms
            self.plot_distance_distribution(all_ingredient_distances)

            # plot distribution of positions for all combined seeds and ingredients
            self.plot_position_histogram_all_ingredients(all_ingredient_position_array)

            # plot histograms for all combined distances
            if len(all_center_distance_array) > 1:
                self.histogram(
                    all_center_distance_array,
                    self.figures_path
                    / f"all_ingredient_center_distances_{self.basename}.png",
                    title_str="all_ingredients",
                    x_label="center distance",
                    y_label="count",
                )

            if len(all_center_distance_array) > 1:
                self.histogram(
                    all_pairwise_distance_array,
                    self.figures_path
                    / f"all_ingredient_pairwise_distances_{self.basename}.png",
                    title_str="all_ingredients",
                    x_label="pairwise distances",
                    y_label="count",
                )

            # plot the angle
            if len(all_ingredient_angle_array) > 1:
                self.histogram(
                    all_ingredient_angle_array[0],
                    self.figures_path / f"all_angles_X_{self.basename}.png",
                    title_str="all_ingredients",
                    x_label="angles X",
                    y_label="count",
                )
                self.histogram(
                    all_ingredient_angle_array[1],
                    self.figures_path / f"all_angles_Y_{self.basename}.png",
                    title_str="all_ingredients",
                    x_label="angles Y",
                    y_label="count",
                )
                self.histogram(
                    all_ingredient_angle_array[2],
                    self.figures_path / f"all_angles_Z_{self.basename}.png",
                    title_str="all_ingredients",
                    x_label="angles Z",
                    y_label="count",
                )
        if number_of_packings > 1:
            for seed, result in self.seed_to_results.items():
                Writer().save_as_simularium(self.env, {seed: result})
        Writer().save_as_simularium(self.env, self.seed_to_results)
