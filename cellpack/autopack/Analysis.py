# -*- coding: utf-8 -*-
"""
Created on Mon May  6 22:58:44 2013

@author: ludo
"""
import concurrent.futures
import json
import multiprocessing
from pathlib import Path
from time import time

import matplotlib
import numpy
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.patches import Circle

import cellpack.autopack as autopack
from cellpack.autopack.ldSequence import halton
from cellpack.autopack.plotly_result import PlotlyAnalysis
from cellpack.autopack.utils import check_paired_key, get_paired_key, get_seed_list
from cellpack.autopack.writers import Writer
from cellpack.autopack.writers.MarkdownWriter import MarkdownWriter


class Analysis:
    def __init__(
        self,
        env=None,
        packing_results_path=None,
        output_path=None,
    ):
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
            self.packing_results_path = Path()

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
    def cartesian_to_sph(xyz, center=None):
        """
        Converts cartesian to spherical coordinates
        """
        if center is None:
            center = numpy.zeros(3)
        xyz = xyz - center
        sph_pts = numpy.zeros(xyz.shape)
        xy = xyz[:, 0] ** 2 + xyz[:, 1] ** 2
        sph_pts[:, 0] = numpy.sqrt(xy + xyz[:, 2] ** 2)
        sph_pts[:, 1] = numpy.arctan2(numpy.sqrt(xy), xyz[:, 2])
        sph_pts[:, 2] = numpy.arctan2(xyz[:, 1], xyz[:, 0])

        return sph_pts

    @staticmethod
    def get_list_of_dims():
        return ["x", "y", "z", "r", "theta", "phi"]

    def writeJSON(self, filename, data):
        with open(filename, "w") as fp:  # doesnt work with symbol link ?
            json.dump(
                data, fp, indent=4, separators=(",", ": ")
            )  # ,indent=4, separators=(',', ': ')

    def loadJSON(self, filename):
        with open(filename) as data_file:
            data = json.load(data_file)
        return data

    def plot_position_distribution_total(self, all_positions):
        pos_xyz = numpy.array(all_positions)
        if pos_xyz.shape[0] <= 1:
            return
        pos_sph = self.cartesian_to_sph(pos_xyz)
        all_pos = numpy.hstack([pos_xyz, pos_sph])
        for ind, dim in enumerate(self.get_list_of_dims()):
            self.histogram(
                all_pos[:, ind],
                self.figures_path
                / f"all_ingredient_histo_{dim}_{self.env.basename}.png",
                title_str="all_ingredients",
                x_label=dim,
                y_label="count",
            )

    def plot_position_distribution(self, ingr):
        pos_xyz = numpy.array(self.env.ingredient_positions[ingr.name])
        if pos_xyz.shape[0] <= 1:
            return
        pos_sph = self.cartesian_to_sph(pos_xyz)
        all_pos = numpy.hstack([pos_xyz, pos_sph])
        for ind, dim in enumerate(self.get_list_of_dims()):
            self.histogram(
                all_pos[:, ind],
                self.figures_path / f"{ingr.name}_histo_{dim}_{self.env.basename}.png",
                title_str=ingr.name,
                x_label=dim,
                y_label="count",
            )

    def plot_occurence_distribution(self, ingr):
        occ = self.env.occurences[ingr.name]
        if len(occ) <= 1:
            return
        self.simpleplot(
            range(len(occ)),
            occ,
            self.figures_path
            / f"{ingr.name}_occurrence_{self.env.basename}_lineplot.png",
            title_str=ingr.name,
            x_label="seed",
            y_label="occurrences",
        )
        self.histogram(
            distances=numpy.array(occ),
            filename=self.figures_path
            / f"{ingr.name}_occurrence_{self.env.basename}_histo.png",
            title_str=ingr.name,
            x_label="occurrences",
            y_label="count",
        )

    def plot_distance_distribution(self, all_ingredient_distances):
        """
        Plots the distribution of distances for ingredient and pairs of ingredients
        """
        for ingr_key, distances in all_ingredient_distances.items():
            if len(distances) <= 1:
                continue
            self.histogram(
                distances=numpy.array(distances),
                filename=self.figures_path
                / f"{ingr_key}_pairwise_distances_{self.env.basename}.png",
                title_str=ingr_key,
                x_label="pairwise distance",
                y_label="count",
                save_png=True,
            )

    def get_obj_dict(self, packing_results_path):
        """
        Returns the object dictionary from the input path folder.

        Args:
            packing_results_path (str): The path to the folder containing the packing results.

        Returns:
            tuple: A tuple containing the object dictionary and the list of all positions.

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
                    positions = numpy.array(positions)
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

    def get_minimum_expected_distance_from_recipe(self, recipe_data):
        """
        Returns 2x the smallest radius of objects in the recipe
        """
        return 2 * min(
            [val for val in self.get_ingredient_radii(recipe_data=recipe_data).values()]
        )

    def get_packed_minimum_distance(self, pairwise_distance_dict):
        """
        Returns the minimum distance between packed objects
        """
        return min(
            self.combine_results_from_ingredients(
                self.combine_results_from_seeds(pairwise_distance_dict)
            )
        )

    def get_number_of_ingredients_packed(
        self,
        ingredient_keys=None,
    ):
        """
        Returns the number of ingredients packed

        Parameters
        ----------
        ingredient_key: str
            ingredient key in self.all_pos_list
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
        recipe_data,
    ):
        """
        Returns the radii of ingredients packed

        Parameters
        ----------
        ingredient_key: str
            ingredient key in self.all_pos_list
        """
        ingredient_radii = {}
        for object_key, object_values in recipe_data.get("objects").items():
            if "radius" in object_values:
                ingredient_radii[object_key] = object_values["radius"]
        return ingredient_radii

    def read_dict_from_glob_file(
        self,
        glob_str,
    ):
        glob_to_distance_file = self.packing_results_path.glob(glob_str)
        for path_to_distance_file in glob_to_distance_file:
            if path_to_distance_file.is_file() and (
                path_to_distance_file.suffix == ".json"
            ):
                return self.loadJSON(path_to_distance_file)

    def run_distance_analysis(
        self,
        md_object: MarkdownWriter,
        recipe_data,
        pairwise_distance_dict,
        figure_path,
        output_image_location,
    ):
        """
        Runs distance analysis on the given packing and adds it to
        the analysis report
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
                md_object.add_header(
                    level=2, header="Possible errors", add_table_of_contents="n"
                )
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
        self, search_name, ingredient_key_dict
    ):
        """
        Returns the ingredient key if object or composition name is given
        """
        for ingredient_key, name_mappings in ingredient_key_dict.items():
            if search_name in name_mappings.values():
                return ingredient_key

    def get_partner_pair_dict(
        self,
        recipe_data,
        combined_pairwise_distance_dict,
        ingredient_radii,
        avg_num_packed,
    ):
        """
        Creates a partner pair dictionary as follows:
        {
            key_from_pairwise_distance_dict: {
                "binding_probability": value,
                "touching_radius": value,
            },
            ...
        }
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
        recipe_data,
        combined_pairwise_distance_dict,
        ingredient_radii,
        avg_num_packed,
    ):
        """
        runs an analysis of partner packings
        """
        partner_pair_dict = self.get_partner_pair_dict(
            recipe_data,
            combined_pairwise_distance_dict,
            ingredient_radii,
            avg_num_packed,
        )
        if len(partner_pair_dict):
            md_object.add_header(header="Partner Analysis")
            partner_data = []
            for paired_key, partner_values in partner_pair_dict.items():
                pairwise_distances = numpy.array(
                    combined_pairwise_distance_dict[paired_key]
                )
                padded_radius = 1.2 * partner_values["touching_radius"]
                close_fraction = (
                    numpy.count_nonzero(pairwise_distances < padded_radius)
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
        recipe_data,
        ingredient_keys=None,
        report_output_path=None,
        output_image_location=None,
        run_distance_analysis=True,
        run_partner_analysis=True,
    ):
        """
        Creates a markdown file with various analyses included

        Parameters
        ----------
        self: AnalyseAP
            instance of AnalyseAP class
        recipe_data: dict
            dictionary containing recipe data for the packing being analyzed
        ingredient_keys: List[str]
            list of ingredient keys to analyze
        output_image_location: Path
            this is the path to look for output images for the markdown file
        run_*_analysis: bool
            whether to run specific analysis
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
        analysis_config: dict,
        recipe_data: dict,
    ):
        all_objs, all_pos_list = self.get_obj_dict(self.packing_results_path)

        self.num_packings = len(all_pos_list)
        self.num_seeds_per_packing = numpy.array(
            [len(packing_dict) for packing_dict in all_pos_list]
        )

        print("Starting analysis workflow...")

        if analysis_config.get("create_report"):
            self.create_report(
                recipe_data=recipe_data,
                **analysis_config["create_report"],
            )

    def histogram(
        self,
        distances,
        filename,
        title_str="",
        x_label="",
        y_label="",
        add_to_result=True,
        save_png=False,
    ):
        if add_to_result:
            # add histogrm to result file and display on the web page
            self.helper.plot_data.add_histogram(
                title=f"{title_str}: {x_label}",
                xaxis_title=x_label,
                traces={y_label: numpy.array(distances)},
            )
        if save_png:
            # use matplotlib to create histogram and save as png
            plt.clf()
            # calculate histogram
            nbins = int(numpy.sqrt(len(distances)))
            if nbins < 2:
                return
            y, bin_edges = numpy.histogram(distances, bins=nbins)
            bincenters = 0.5 * (bin_edges[1:] + bin_edges[:-1])

            # calculate standard error for values in each bin
            bin_inds = numpy.digitize(distances, bin_edges)
            x_err_vals = numpy.zeros(y.shape)
            for bc in range(nbins):
                dist_vals = distances[bin_inds == (bc + 1)]
                if len(dist_vals) > 1:
                    x_err_vals[bc] = numpy.std(dist_vals)
                else:
                    x_err_vals[bc] = 0
            y_err_vals = numpy.sqrt(y * (1 - y / numpy.sum(y)))
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

    def plot(self, rdf, radii, file_name):
        plt.clf()
        matplotlib.rc("font", size=14)
        matplotlib.rc("figure", figsize=(5, 4))
        #        plt.clf()
        plt.plot(radii, rdf, linewidth=3)
        plt.xlabel(r"distance $r$ in $\AA$")
        plt.ylabel(r"radial distribution function $g(r)$")
        plt.savefig(file_name)

    def simpleplot(self, X, Y, filename, w=3, title_str="", x_label="", y_label=""):
        plt.clf()
        plt.plot(X, Y, linewidth=w)
        plt.title(title_str)
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.savefig(filename)

    def build_grid(
        self,
    ):
        t1 = time()
        self.env.buildGrid()
        t2 = time()
        gridTime = t2 - t1
        print(f"time to build grid: {gridTime:0.2f}")

    def pack(
        self,
        seed=20,
        show_plotly_plot=True,
        **kwargs,
    ):
        if show_plotly_plot:
            self.plotly.update_title(self.env.place_method)

        t1 = time()
        results = self.env.pack_grid(seedNum=seed, **kwargs)
        self.seed_to_results[seed] = results
        t2 = time()
        run_time = t2 - t1
        print(f"time to run pack_grid for {self.env.place_method}: {run_time:0.2f}")
        print(f"num placed: {len(self.env.packed_objects.get_ingredients())}")
        if show_plotly_plot:
            min_bound, max_bound = self.env.get_bounding_box_limits()
            width = max_bound - min_bound
            self.plotly.plot["data"] = []
            self.plotly.plot.layout.shapes = ()
            self.plotly.plot.update_xaxes(
                range=[min_bound[0] - 0.2 * width[0], max_bound[0] + 0.2 * width[0]]
            )
            self.plotly.plot.update_yaxes(
                range=[min_bound[1] - 0.2 * width[1], max_bound[1] + 0.2 * width[1]]
            )
            self.plotly.update_title(
                f"{self.env.place_method} took {str(round(t2 - t1, 2))}s, packed {len(self.env.packed_objects.get_ingredients())}"
            )
            self.plotly.make_grid_heatmap(self.env)
            self.plotly.add_ingredient_positions(self.env)
            self.plotly.show()

    def set_ingredient_color(self, ingr):
        """
        Sets the color of an ingredient
        """
        color = None

        if ingr.color is not None:
            color = (
                ingr.color
                if all([x <= 1 for x in ingr.color])
                else numpy.array(ingr.color) / 255
            )

        return color

    def add_ingredient_positions_to_plot(
        self, ax, ingr, color, seed_index, ingredient_position_dict, width
    ):
        """
        Adds 2D images of ingredient positions to axis
        """
        seed_ingredient_positions = ingredient_position_dict[seed_index][ingr.name]
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
                            (pos[0] + width[0], pos[1]),
                            radius,
                            facecolor=color,
                        )
                    )
                elif pos[0] > (width[0] - radius):
                    ax.add_patch(
                        Circle(
                            (pos[0] - width[0], pos[1]),
                            radius,
                            facecolor=color,
                        )
                    )
                if pos[1] < radius:
                    ax.add_patch(
                        Circle(
                            (pos[0], pos[1] + width[1]),
                            radius,
                            facecolor=color,
                        )
                    )
                elif pos[1] > (width[1] - radius):
                    ax.add_patch(
                        Circle(
                            (pos[0], pos[1] - width[1]),
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
                if ingr.use_rbsphere:
                    (
                        ext_recipe,
                        pts,
                    ) = ingr.getInterpolatedSphere(
                        seed_ingredient_positions[-i - 1],
                        seed_ingredient_positions[-i],
                    )
                    for pt in pts:
                        ax.add_patch(
                            Circle(
                                (pt[0], pt[1]),
                                ingr.min_radius,
                                edgecolor="black",
                                facecolor=color,
                            )
                        )
        return ax

    def getHaltonUnique(self, n):
        seeds_f = numpy.array(halton(int(n * 1.5))) * int(n * 1.5)
        seeds_int = numpy.array(numpy.round(seeds_f), "int")
        _, indices_u = numpy.unique(seeds_int, return_index=True)
        seeds_i = numpy.array(seeds_int[numpy.sort(indices_u)])[:n]
        return seeds_i

    def update_distance_distribution_dictionaries(
        self,
        ingr,
        center_distance_dict,
        pairwise_distance_dict,
        ingredient_position_dict,
        ingredient_angle_dict,
        ingredient_occurence_dict,
        seed_index,
        center,
    ):
        """
        Update dictionaries that store distance and angle information
        """
        if ingr.name not in center_distance_dict[seed_index]:
            center_distance_dict[seed_index][ingr.name] = []
            pairwise_distance_dict[seed_index][ingr.name] = []
            ingredient_position_dict[seed_index][ingr.name] = []
            ingredient_angle_dict[seed_index][ingr.name] = []
            ingredient_occurence_dict[seed_index][ingr.name] = []

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
        ) = self.env.get_distances_and_angles(ingr.name, center, get_angles=get_angles)

        center_distance_dict[seed_index][
            ingr.name
        ] = seed_distances_from_center.tolist()
        pairwise_distance_dict[seed_index][
            ingr.name
        ] = seed_distances_between_ingredients.tolist()
        ingredient_position_dict[seed_index][
            ingr.name
        ] = seed_ingredient_positions.tolist()
        ingredient_angle_dict[seed_index][ingr.name] = seed_angles.tolist()
        ingredient_occurence_dict[seed_index][ingr.name].append(
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
        self, ingr, recipe, pairwise_distance_dict, seed_index
    ):
        """
        Adds cross-ingredient distances for pairwise distance dictionary
        """
        for ingr2 in recipe.ingredients:
            if ingr2.name == ingr.name:
                continue
            if not check_paired_key(
                pairwise_distance_dict[seed_index],
                ingr.name,
                ingr2.name,
            ):
                pairwise_distance_dict[seed_index][f"{ingr.name}_{ingr2.name}"] = (
                    self.env.calc_pairwise_distances(ingr.name, ingr2.name).tolist()
                )

        return pairwise_distance_dict

    def process_ingredients_in_recipe(
        self,
        recipe,
        center_distance_dict,
        pairwise_distance_dict,
        ingredient_position_dict,
        ingredient_angle_dict,
        ingredient_occurence_dict,
        ingredient_key_dict,
        seed_index,
        center,
        ax,
        plot_figures,
        two_d,
        width,
    ):
        """
        Updates distance/angle dictionaries and creates plots for ingredients in recipe
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

            if plot_figures and two_d:
                ax = self.add_ingredient_positions_to_plot(
                    ax,
                    ingr,
                    color,
                    seed_index,
                    ingredient_position_dict,
                    width,
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

    def combine_results_from_seeds(self, input_dict):
        """
        Combines results from multiple seeds into one dictionary
        Dictionary keys are ingredient names
        """
        output_dict = {}
        for seed_index, ingr_dict in input_dict.items():
            for ingr_name, value_list in ingr_dict.items():
                if ingr_name not in output_dict:
                    output_dict[ingr_name] = []
                output_dict[ingr_name].extend(value_list)

        return output_dict

    def combine_results_from_ingredients(self, input_dict):
        """
        Combines results from multiple ingredients into one list
        """
        output_list = []
        for ingr_name, value_list in input_dict.items():
            output_list.extend(value_list)
        return output_list

    def pack_one_seed(
        self,
        seed_index,
        seed_list,
        bounding_box,
        center_distance_dict=None,
        pairwise_distance_dict=None,
        ingredient_position_dict=None,
        ingredient_angle_dict=None,
        ingredient_occurence_dict=None,
        ingredient_key_dict=None,
        get_distance_distribution=False,
        image_export_options=None,
        show_grid=False,
        plot_figures=False,
        save_gradient_data_as_image=False,
        clean_grid_cache=False,
    ):
        """
        Packs one seed of a recipe and returns the recipe object
        """
        seed = int(seed_list[seed_index])
        seed_basename = self.env.add_seed_number_to_base_name(seed)
        self.env.reset()
        numpy.random.seed(seed)
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
        width = 0
        if plot_figures and two_d:
            width = self.env.get_size_of_bounding_box()
            fig = plt.figure()
            ax = fig.add_subplot(111)

        if get_distance_distribution:
            center_distance_dict[seed_index] = {}
            pairwise_distance_dict[seed_index] = {}
            ingredient_position_dict[seed_index] = {}
            ingredient_angle_dict[seed_index] = {}
            ingredient_occurence_dict[seed_index] = {}

            if hasattr(self, "center"):
                center = self.center
            else:
                center = self.env.grid.getCenter()  # center of the grid

            ext_recipe = self.env.exteriorRecipe
            if ext_recipe:
                (
                    center_distance_dict,
                    pairwise_distance_dict,
                    ingredient_position_dict,
                    ingredient_angle_dict,
                    ingredient_occurence_dict,
                    ingredient_key_dict,
                    ax,
                ) = self.process_ingredients_in_recipe(
                    recipe=ext_recipe,
                    center_distance_dict=center_distance_dict,
                    pairwise_distance_dict=pairwise_distance_dict,
                    ingredient_position_dict=ingredient_position_dict,
                    ingredient_angle_dict=ingredient_angle_dict,
                    ingredient_occurence_dict=ingredient_occurence_dict,
                    ingredient_key_dict=ingredient_key_dict,
                    seed_index=seed_index,
                    center=center,
                    ax=ax,
                    plot_figures=plot_figures,
                    two_d=two_d,
                    width=width,
                )

            for comparment in self.env.compartments:
                surface_recipe = comparment.surfaceRecipe
                if surface_recipe:
                    (
                        center_distance_dict,
                        pairwise_distance_dict,
                        ingredient_position_dict,
                        ingredient_angle_dict,
                        ingredient_occurence_dict,
                        ingredient_key_dict,
                        ax,
                    ) = self.process_ingredients_in_recipe(
                        recipe=surface_recipe,
                        center_distance_dict=center_distance_dict,
                        pairwise_distance_dict=pairwise_distance_dict,
                        ingredient_position_dict=ingredient_position_dict,
                        ingredient_angle_dict=ingredient_angle_dict,
                        ingredient_occurence_dict=ingredient_occurence_dict,
                        ingredient_key_dict=ingredient_key_dict,
                        seed_index=seed_index,
                        center=center,
                        ax=ax,
                        plot_figures=plot_figures,
                        two_d=two_d,
                        width=width,
                    )

                inner_recipe = comparment.innerRecipe
                if inner_recipe:
                    (
                        center_distance_dict,
                        pairwise_distance_dict,
                        ingredient_position_dict,
                        ingredient_angle_dict,
                        ingredient_occurence_dict,
                        ingredient_key_dict,
                        ax,
                    ) = self.process_ingredients_in_recipe(
                        recipe=inner_recipe,
                        center_distance_dict=center_distance_dict,
                        pairwise_distance_dict=pairwise_distance_dict,
                        ingredient_position_dict=ingredient_position_dict,
                        ingredient_angle_dict=ingredient_angle_dict,
                        ingredient_occurence_dict=ingredient_occurence_dict,
                        ingredient_key_dict=ingredient_key_dict,
                        seed_index=seed_index,
                        center=center,
                        ax=ax,
                        plot_figures=plot_figures,
                        two_d=two_d,
                        width=width,
                    )

            if plot_figures and two_d:
                ax.set_aspect(1.0)
                ax.axhline(y=bounding_box[0][1], color="k")
                ax.axhline(y=bounding_box[1][1], color="k")
                ax.axvline(x=bounding_box[0][0], color="k")
                ax.axvline(x=bounding_box[1][0], color="k")
                ax.set_xlim([bounding_box[0][0], bounding_box[1][0]])
                ax.set_ylim([bounding_box[0][1], bounding_box[1][1]])

                plt.savefig(self.figures_path / f"packing_image_{seed_basename}.png")
                plt.close()  # closes the current figure

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
        recipe_data,
        packing_config_data,
        bounding_box,
        get_distance_distribution=True,
    ):
        """
        Runs multiple packings of the same recipe in a loop. This workflow
        also runs various analyses and saves the output figures and data at
        the location set by the environment. The output data is also stored
        as an attribute on the environment object and on the Analysis class
        instance.

        Parameters
        ----------
        recipe_data: dict
            Dictionary containing recipe data
        packing_config_data: dict
            Dictionary containing packing configuration data
        bounding_box: list
            List of two lists containing the minimum and maximum coordinates
            of the bounding box
        get_distance_distribution: bool
            Whether to calculate and store distance and angle distributions
        seed_list: list
            List of seeds to use for packings

        Outputs
        -------
        {}_distance_dict: dict
            Dictionaries with various ingredient distances stored
        images: png
            packing image, histograms of distance, angle, and occurence
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
        numpy.savetxt(
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
            num_processes = numpy.min(
                [
                    int(numpy.floor(0.8 * multiprocessing.cpu_count())),
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

        all_center_distance_array = numpy.array(
            self.combine_results_from_ingredients(all_center_distances)
        )
        all_pairwise_distance_array = numpy.array(
            self.combine_results_from_ingredients(all_ingredient_distances)
        )
        all_ingredient_position_array = numpy.array(
            self.combine_results_from_ingredients(all_ingredient_positions)
        )
        all_ingredient_angle_array = numpy.array(
            self.combine_results_from_ingredients(all_ingredient_angles)
        )

        self.env.ingredient_positions = all_ingredient_positions
        self.env.distances = all_ingredient_distances
        self.env.basename = packing_basename
        self.env.occurences = all_ingredient_occurences
        self.env.angles = all_ingredient_angles

        self.center_distance_dict = center_distance_dict
        self.pairwise_distance_dict = pairwise_distance_dict
        self.ingredient_position_dict = ingredient_position_dict
        self.ingredient_angle_dict = ingredient_angle_dict
        self.ingredient_occurence_dict = ingredient_occurence_dict
        self.ingredient_key_dict = ingredient_key_dict

        if plot_figures:
            self.env.loopThroughIngr(self.plot_position_distribution)
            self.env.loopThroughIngr(self.plot_occurence_distribution)

            # plot pairwise distance histograms
            self.plot_distance_distribution(all_ingredient_distances)

            # plot distribution of positions for all combined seeds and ingredients
            self.plot_position_distribution_total(all_ingredient_position_array)

            # plot histograms for all combined distances
            if len(all_center_distance_array) > 1:
                self.histogram(
                    all_center_distance_array,
                    self.figures_path
                    / f"all_ingredient_center_distances_{self.env.basename}.png",
                    title_str="all_ingredients",
                    x_label="center distance",
                    y_label="count",
                )

            if len(all_center_distance_array) > 1:
                self.histogram(
                    all_pairwise_distance_array,
                    self.figures_path
                    / f"all_ingredient_pairwise_distances_{self.env.basename}.png",
                    title_str="all_ingredients",
                    x_label="pairwise distances",
                    y_label="count",
                )

            # plot the angle
            if len(all_ingredient_angle_array) > 1:
                self.histogram(
                    all_ingredient_angle_array[0],
                    self.figures_path / f"all_angles_X_{self.env.basename}.png",
                    title_str="all_ingredients",
                    x_label="angles X",
                    y_label="count",
                )
                self.histogram(
                    all_ingredient_angle_array[1],
                    self.figures_path / f"all_angles_Y_{self.env.basename}.png",
                    title_str="all_ingredients",
                    x_label="angles Y",
                    y_label="count",
                )
                self.histogram(
                    all_ingredient_angle_array[2],
                    self.figures_path / f"all_angles_Z_{self.env.basename}.png",
                    title_str="all_ingredients",
                    x_label="angles Z",
                    y_label="count",
                )
        if number_of_packings > 1:
            for seed, result in self.seed_to_results.items():
                Writer().save_as_simularium(self.env, {seed: result})
        Writer().save_as_simularium(self.env, self.seed_to_results)
