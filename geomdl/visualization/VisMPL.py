"""
.. module:: VisMPL
    :platform: Unix, Windows
    :synopsis: Matplotlib visualization component for NURBS-Python (experimental)

.. moduleauthor:: Onur Rauf Bingol <orbingol@gmail.com>

"""

from geomdl import Abstract
from geomdl import utilities as utils

import numpy as np
import matplotlib as mpl
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt


class VisConfig(Abstract.VisConfigAbstract):

    def __init__(self, **kwargs):
        super(VisConfig, self).__init__(**kwargs)
        self.display_ctrlpts = kwargs.get('ctrlpts', True)
        self.display_legend = kwargs.get('legend', True)
        self.display_axes = kwargs.get('axes', True)
        self.figure_size = kwargs.get('figure_size', [10.67, 8])
        self.figure_dpi = kwargs.get('figure_dpi', 96)


class VisCurve2D(Abstract.VisAbstract):
    """ Visualization module for 2D Curves """
    def __init__(self, config=VisConfig()):
        super(VisCurve2D, self).__init__(config=config)

    def render(self):
        """ Plots the 2D curve and the control points polygon """
        if not self._plots:
            return

        legend_proxy = []
        legend_names = []

        # Draw control points polygon and the curve
        plt.figure(figsize=self._config.figure_size, dpi=self._config.figure_dpi)

        # Start plotting
        for plot in self._plots:
            pts = np.array(plot['ptsarr'])
            if plot['type'] == 1:
                if self._config.display_ctrlpts:
                    cpplot, = plt.plot(pts[:, 0], pts[:, 1], color=plot['color'], linestyle='-.', marker='o')
                    legend_proxy.append(cpplot)
                    legend_names.append(plot['name'])
            else:
                curveplt, = plt.plot(pts[:, 0], pts[:, 1], color=plot['color'], linestyle='-')
                legend_proxy.append(curveplt)
                legend_names.append(plot['name'])

        # Add legend
        if self._config.display_legend:
            plt.legend(legend_proxy, legend_names)

        # Display 2D plot
        plt.show()


class VisCurve3D(Abstract.VisAbstract):
    """ Visualization module for 3D Curves """
    def __init__(self, config=VisConfig()):
        super(VisCurve3D, self).__init__(config=config)

    def render(self):
        """ Plots the 3D curve and the control points polygon """
        if not self._plots:
            return

        # Draw control points polygon and the 3D curve
        fig = plt.figure(figsize=self._config.figure_size, dpi=self._config.figure_dpi)
        ax = Axes3D(fig)

        legend_proxy = []
        legend_names = []

        # Start plotting
        for plot in self._plots:
            pts = np.array(plot['ptsarr'])

            # Try not to fail if the input is 2D
            if pts.shape[1] == 2:
                pts = np.c_[pts, np.zeros(pts.shape[0])]

            # Control points or not
            if plot['type'] == 1:
                if self._config.display_ctrlpts:
                    ax.plot(pts[:, 0], pts[:, 1], pts[:, 2], color=plot['color'], linestyle='-.', marker='o')
                    plot1_proxy = mpl.lines.Line2D([0], [0], linestyle='-.', color=plot['color'], marker='o')
                    legend_proxy.append(plot1_proxy)
                    legend_names.append(plot['name'])
            else:
                ax.plot(pts[:, 0], pts[:, 1], pts[:, 2], color=plot['color'], linestyle='-')
                plot2_proxy = mpl.lines.Line2D([0], [0], linestyle='-', color=plot['color'])
                legend_proxy.append(plot2_proxy)
                legend_names.append(plot['name'])

        # Add legend to 3D plot, @ref: https://stackoverflow.com/a/20505720
        if self._config.display_legend:
            ax.legend(legend_proxy, legend_names, numpoints=1)

        # Display the 3D plot
        plt.show()


class VisSurface(Abstract.VisAbstractSurf):
    """ Visualization module for Surfaces

    Triangular mesh plot for the surface and wireframe plot for the control points grid
    """
    def __init__(self, config=VisConfig()):
        super(VisSurface, self).__init__(config=config)

    def render(self):
        """ Plots the surface and the control points grid """
        if not self._plots:
            return

        # Start plotting of the surface and the control points grid
        fig = plt.figure(figsize=self._config.figure_size, dpi=self._config.figure_dpi)
        ax = Axes3D(fig)

        legend_proxy = []
        legend_names = []

        # Start plotting
        for plot in self._plots:
            if plot['type'] == 1:
                if self._config.display_ctrlpts:
                    pts = np.array(utils.make_quad(plot['ptsarr'], plot['size'][1], plot['size'][0]))
                    cp_z = pts[:, 2] + self._ctrlpts_offset
                    ax.plot(pts[:, 0], pts[:, 1], cp_z, color=plot['color'], linestyle='-.', marker='o')
                    plot1_proxy = mpl.lines.Line2D([0], [0], linestyle='-.', color=plot['color'], marker='o')
                    legend_proxy.append(plot1_proxy)
                    legend_names.append(plot['name'])
            else:
                pts = np.array(utils.make_triangle(plot['ptsarr'], plot['size'][1], plot['size'][0]))
                ax.plot(pts[:, 0], pts[:, 1], pts[:, 2], color=plot['color'])
                plot2_proxy = mpl.lines.Line2D([0], [0], linestyle='-', color=plot['color'])
                legend_proxy.append(plot2_proxy)
                legend_names.append(plot['name'])

        # Add legend to 3D plot, @ref: https://stackoverflow.com/a/20505720
        if self._config.display_legend:
            ax.legend(legend_proxy, legend_names, numpoints=1)

        # Display the 3D plot
        plt.show()


class VisSurfWireframe(Abstract.VisAbstractSurf):
    """ Visualization module for Surfaces

    Scatter plot for the control points and wireframe for the surface points
    """
    def __init__(self, config=VisConfig()):
        super(VisSurfWireframe, self).__init__(config=config)

    def render(self):
        """ Plots the surface and the control points grid """
        if not self._plots:
            return

        # Start plotting of the surface and the control points grid
        fig = plt.figure(figsize=self._config.figure_size, dpi=self._config.figure_dpi)
        ax = Axes3D(fig)

        legend_proxy = []
        legend_names = []

        # Start plotting
        for plot in self._plots:
            if plot['type'] == 1:
                if self._config.display_ctrlpts:
                    pts = np.array(plot['ptsarr'])
                    cp_z = pts[:, 2] + self._ctrlpts_offset
                    ax.scatter(pts[:, 0], pts[:, 1], cp_z, color=plot['color'], s=25, depthshade=True)
                    plot1_proxy = mpl.lines.Line2D([0], [0], linestyle='-.', color=plot['color'], marker='o')
                    legend_proxy.append(plot1_proxy)
                    legend_names.append(plot['name'])
            else:
                pts = np.array(utils.make_quad(plot['ptsarr'], plot['size'][1], plot['size'][0]))
                ax.plot(pts[:, 0], pts[:, 1], pts[:, 2], color=plot['color'])
                plot2_proxy = mpl.lines.Line2D([0], [0], linestyle='-', color=plot['color'])
                legend_proxy.append(plot2_proxy)
                legend_names.append(plot['name'])

        # Add legend to 3D plot, @ref: https://stackoverflow.com/a/20505720
        if self._config.display_legend:
            ax.legend(legend_proxy, legend_names, numpoints=1)

        # Display the 3D plot
        plt.show()


class VisSurfTriangle(Abstract.VisAbstractSurf):
    """ Visualization module for Surfaces

    Wireframe plot for the control points and triangulated plot for the surface points
    """
    def __init__(self, config=VisConfig()):
        super(VisSurfTriangle, self).__init__(config=config)

    def render(self):
        """ Plots the surface and the control points grid """
        if not self._plots:
            return

        # Start plotting of the surface and the control points grid
        fig = plt.figure(figsize=self._config.figure_size, dpi=self._config.figure_dpi)
        ax = Axes3D(fig)

        legend_proxy = []
        legend_names = []

        # Start plotting
        for plot in self._plots:
            if plot['type'] == 1:
                if self._config.display_ctrlpts:
                    pts = np.array(utils.make_quad(plot['ptsarr'], plot['size'][1], plot['size'][0]))
                    cp_z = pts[:, 2] + self._ctrlpts_offset
                    ax.plot(pts[:, 0], pts[:, 1], cp_z, color=plot['color'], linestyle='-.', marker='o')
                    plot1_proxy = mpl.lines.Line2D([0], [0], linestyle='-.', color=plot['color'], marker='o')
                    legend_proxy.append(plot1_proxy)
                    legend_names.append(plot['name'])
            else:
                pts = np.array(plot['ptsarr'])
                ax.plot_trisurf(pts[:, 0], pts[:, 1], pts[:, 2], color=plot['color'])
                plot2_proxy = mpl.lines.Line2D([0], [0], linestyle='none', color=plot['color'], marker='^')
                legend_proxy.append(plot2_proxy)
                legend_names.append(plot['name'])

        # Add legend to 3D plot, @ref: https://stackoverflow.com/a/20505720
        if self._config.display_legend:
            ax.legend(legend_proxy, legend_names, numpoints=1)

        # Display the 3D plot
        plt.show()


class VisSurfScatter(Abstract.VisAbstractSurf):
    """ Visualization module for Surfaces

    Wireframe plot for the control points and scatter plot for the surface points
    """
    def __init__(self, config=VisConfig()):
        super(VisSurfScatter, self).__init__(config=config)

    def render(self):
        """ Plots the surface and the control points grid """
        if not self._plots:
            return

        # Start plotting of the surface and the control points grid
        fig = plt.figure(figsize=self._config.figure_size, dpi=self._config.figure_dpi)
        ax = Axes3D(fig)

        legend_proxy = []
        legend_names = []

        # Start plotting
        for plot in self._plots:
            if plot['type'] == 1:
                if self._config.display_ctrlpts:
                    pts = np.array(utils.make_quad(plot['ptsarr'], plot['size'][1], plot['size'][0]))
                    cp_z = pts[:, 2] + self._ctrlpts_offset
                    ax.plot(pts[:, 0], pts[:, 1], cp_z, color=plot['color'], linestyle='-.', marker='o')
                    plot1_proxy = mpl.lines.Line2D([0], [0], linestyle='-.', color=plot['color'], marker='o')
                    legend_proxy.append(plot1_proxy)
                    legend_names.append(plot['name'])
            else:
                pts = np.array(plot['ptsarr'])
                ax.scatter(pts[:, 0], pts[:, 1], pts[:, 2], color=plot['color'], s=50, depthshade=True)
                plot2_proxy = mpl.lines.Line2D([0], [0], linestyle='none', color=plot['color'], marker='o')
                legend_proxy.append(plot2_proxy)
                legend_names.append(plot['name'])

        # Add legend to 3D plot, @ref: https://stackoverflow.com/a/20505720
        if self._config.display_legend:
            ax.legend(legend_proxy, legend_names, numpoints=1)

        # Display the 3D plot
        plt.show()
