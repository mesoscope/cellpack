from cellpack.autopack.upy.colors import create_divergent_color_map_with_scaled_values
import plotly.graph_objects as go
import plotly.colors as pcolors
import numpy


class PlotlyAnalysis:
    def __init__(self, title=""):
        fig = go.Figure()
        fig.update_layout(width=800, height=800, title=title)
        fig.update_xaxes(range=[-200, 1200])
        fig.update_yaxes(range=[-200, 1200])
        self.plot = fig

    def update_title(self, title):
        self.plot.update_layout(title=title)

    @staticmethod
    def format_color(color):
        if color is None:
            color = [1.0, 0.0, 0.0]  # RED default
        return "rgb{}".format((255 * color[0], 255 * color[1], 255 * color[2]))

    def add_circle(self, radius, pos, color, opacity=1):
        self.plot.add_shape(
            type="circle",
            xref="x",
            yref="y",
            x0=pos[0] - radius,
            y0=pos[1] - radius,
            x1=pos[0] + radius,
            y1=pos[1] + radius,
            line_color=PlotlyAnalysis.format_color(color),
            opacity=opacity,
        )

    def add_square(self, side_length, pos, rotMat, color, opacity=1):
        # side_length is the length of each side
        x0 = -side_length[0][0] / 2.0
        y0 = -side_length[0][1] / 2.0
        x1 = side_length[0][0] / 2.0
        y1 = side_length[0][1] / 2.0
        # corner points of the cube top surface
        point_array = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
        rotated_pts = self.transformPoints2D(pos, rotMat, point_array)
        path_str = ""
        for index, point_to_print in enumerate(rotated_pts):
            if index == 0:
                path_str += "M {0[0]} {0[1]} ".format(point_to_print)
            else:
                path_str += "L {0[0]} {0[1]} ".format(point_to_print)
        path_str += "Z"

        self.plot.add_shape(
            type="path",
            path=path_str,
            line_color=PlotlyAnalysis.format_color(color),
            opacity=opacity,
        )

    def add_ingredient_positions(self, env):
        for pos, rot, ingr, ptInd in env.molecules:
            if len(ingr.positions) > 1:
                for level in range(len(ingr.positions)):
                    for i in range(len(ingr.positions[level])):
                        position = ingr.apply_rotation(
                            rot, ingr.positions[level][i], pos
                        )
                        self.add_circle(
                            ingr.radii[level][i],
                            [position[0], position[1]],
                            ingr.color,
                            level / len(ingr.positions),
                        )
            else:
                if ingr.modelType == "Spheres":
                    self.add_circle(ingr.encapsulatingRadius, pos, ingr.color)
                elif ingr.modelType == "Cube":
                    self.add_square(ingr.radii, pos, rot, ingr.color)
                elif ingr.modelType == "Cylinders":
                    length = ingr.length
                    width = 2 * ingr.radii[0][0]
                    side_lengths = [[width, length, 1.0]]
                    self.add_square(side_lengths, pos, rot, ingr.color)

    def make_grid_heatmap(self, env):
        ids = []
        x = []
        y = []
        colors = []
        color_scale = pcolors.diverging.PiYG
        fig = self.plot
        for i in range(len(env.grid.masterGridPositions)):
            ids.append(i)
            x.append(env.grid.masterGridPositions[i][0])
            y.append(env.grid.masterGridPositions[i][1])
            dist = env.grid.distToClosestSurf[i]
            colors.append(dist)

        min_value = min(colors)
        max_value = max(colors)
        color_map = create_divergent_color_map_with_scaled_values(
            min_value, max_value, color_scale
        )
        fig.add_trace(
            go.Scatter(
                ids=ids,
                x=x,
                y=y,
                text=list(zip(colors, ids)),
                mode="markers",
                marker=go.scatter.Marker(
                    size=8,
                    color=colors,
                    opacity=1,
                    symbol="square",
                    showscale=True,
                    colorscale=color_map,
                ),
            )
        )

    def make_and_show_heatmap(self, env):

        self.make_grid_heatmap(env)

        self.plot.show()

    def show(self):
        self.plot.show()

    def transformPoints2D(self, trans, rot, points):
        output = []
        rot = numpy.array(rot)
        for point in points:
            output.append(numpy.matmul(rot[0:2, 0:2], point) + trans[0:2])
        return output
