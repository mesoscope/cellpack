from cellpack.autopack.upy.colors import create_divergent_color_map_with_scaled_values
import plotly.graph_objects as go
import plotly.colors as pcolors


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

    def add_square(self, radius, pos, color, opacity=1):
        self.plot.add_shape(
            type="rect",
            xref="x",
            yref="y",
            x0=pos[0] - radius,
            y0=pos[1] - radius,
            x1=pos[0] + radius,
            y1=pos[1] + radius,
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
                    self.add_square(ingr.encapsulatingRadius, pos, ingr.color)

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
