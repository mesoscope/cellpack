from cellpack.autopack.upy.colors import create_divergent_color_map_with_scaled_values
import plotly.graph_objects as go
import plotly.colors as pcolors


class PlotlyAnalysis:
    def __init__(self, title):
        fig = go.Figure()
        fig.update_layout(
            width=700,
            height=700,
            title=title
        )
        fig.update_xaxes(range=[-200, 1200])
        fig.update_yaxes(range=[-200, 1200])
        self.plot = fig

    def update_title(self, title):
        self.plot.update_layout(title=title)

    def add_ingredient_positions(self, env):
        for pos, rot, ingr, ptInd in env.molecules:
            self.plot.add_shape(type="circle",
                xref="x", yref="y",
                x0=pos[0] - ingr.encapsulatingRadius , y0=pos[1] - ingr.encapsulatingRadius, 
                x1=pos[0] + ingr.encapsulatingRadius, y1=pos[1] + ingr.encapsulatingRadius,
                line_color="LightSeaGreen",
            )

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
        color_map = create_divergent_color_map_with_scaled_values(min_value, max_value, color_scale)
        fig.add_trace(go.Scatter(
            ids=ids,
            x=x,
            y=y,
            text=list(zip(colors, ids)),
            mode="markers",
            marker=go.scatter.Marker(
                size=10,
                color=colors,
                opacity=1,
                symbol="square",
                showscale=True,
                colorscale=color_map

            )
        ))

    def make_and_show_heatmap(self, env):

        self.make_grid_heatmap(env)

        self.plot.show()

    def show(self):
        self.plot.show()