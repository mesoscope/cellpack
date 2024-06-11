import numpy as np
from simulariumio import ScatterPlotData, HistogramPlotData


class PlotData:
    def __init__(self):
        self.plot_list = []  # list of tuples

    def _add_plot(self, plot):
        self.plot_list.append(plot)

    def add_scatter(self, title, xaxis_title, yaxis_title, xtrace, ytraces):
        self._add_plot(
            (
                "scatter",
                ScatterPlotData(
                    title=title,
                    xaxis_title=xaxis_title,
                    yaxis_title=yaxis_title,
                    xtrace=np.array(xtrace),
                    ytraces={key: np.array(value) for key, value in ytraces.items()},
                ),
            )
        )

    def add_histogram(self, title, xaxis_title, traces):
        self._add_plot(
            (
                "histogram",
                HistogramPlotData(
                    title=title,
                    xaxis_title=xaxis_title,
                    traces={key: np.array(value) for key, value in traces.items()},
                ),
            )
        )
