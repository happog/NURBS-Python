"""
.. module:: Multi
    :platform: Unix, Windows
    :synopsis: Provides container classes for spline geoemtries

.. moduleauthor:: Onur Rauf Bingol <orbingol@gmail.com>

"""

import abc
import warnings
from functools import partial
from . import abstract
from . import vis
from . import voxelize
from . import utilities
from . import tessellate
from . import _utilities as utl
from .exceptions import GeomdlException


@utl.add_metaclass(abc.ABCMeta)
class AbstractContainer(abstract.GeomdlBase):
    """ Abstract class for geometry containers.

    This class implements Python Iterator Protocol and therefore any instance of this class can be directly used in
    a for loop.

    This class provides the following properties:

    * :py:attr:`dimension`
    * :py:attr:`evalpts`
    * :py:attr:`bbox`
    * :py:attr:`vis`
    * :py:attr:`delta`
    * :py:attr:`sample_size`
    """

    def __init__(self, *args, **kwargs):
        self._pdim = 0 if not hasattr(self, '_pdim') else self._pdim  # number of parametric dimensions
        self._dinit = 0.01 if not hasattr(self, '_dinit') else self._dinit  # delta initialization value
        super(AbstractContainer, self).__init__(**kwargs)
        self._geometry_type = "container"
        self._name = self._geometry_type
        self._delta = [float(self._dinit) for _ in range(self._pdim)]  # evaluation delta
        self._elements = []  # list of elements contained
        self._vis_component = None  # visualization component
        self._cache['evalpts'] = []

    def __iter__(self):
        self._iter_index = 0
        return self

    def next(self):
        return self.__next__()

    def __next__(self):
        try:
            result = self._elements[self._iter_index]
        except IndexError:
            raise StopIteration
        self._iter_index += 1
        return result

    def __reversed__(self):
        return reversed(self._elements)

    def __getitem__(self, index):
        return self._elements[index]

    def __len__(self):
        return len(self._elements)

    def __add__(self, other):
        if not isinstance(other, self.__class__):
            raise GeomdlException("Cannot add non-matching container types")
        self.add(other)
        return self

    @property
    def pdimension(self):
        """ Parametric dimension.

        Please refer to the `wiki <https://github.com/orbingol/NURBS-Python/wiki/Using-Python-Properties>`_ for details
        on using this class member.

        :getter: Gets the parametric dimension
        :type: int
        """
        return self._pdim

    @property
    def evalpts(self):
        """ Evaluated points.

        Since there are multiple shapes contained in the multi objects, the evaluated points will be returned in the
        format of list of individual evaluated points which is also a list of Cartesian coordinates.

        The following code example illustrates these details:

        .. code-block:: python
            :linenos:

            multi_obj = multi.SurfaceContainer()  # it can also be multi.CurveContainer()
            # Add shapes to multi_obj via multi_obj.add() method
            # Then, the following loop will print all the evaluated points of the Multi object
            for idx, mpt in enumerate(multi_obj.evalpts):
                print("Shape", idx+1, "contains", len(mpt), "points. These points are:")
                for pt in mpt:
                    line = ", ".join([str(p) for p in pt])
                    print(line)

        Please refer to the `wiki <https://github.com/orbingol/NURBS-Python/wiki/Using-Python-Properties>`_ for details
        on using this class member.

        :getter: Gets the evaluated points of all contained shapes
        """
        if not self._cache['evalpts']:
            for elem in self._elements:
                elem.delta = self._delta[0] if self._pdim == 1 else self._delta
                evalpts = elem.evalpts
                self._cache['evalpts'] += evalpts
        return self._cache['evalpts']

    @property
    def bbox(self):
        """ Bounding box.

        Please refer to the `wiki <https://github.com/orbingol/NURBS-Python/wiki/Using-Python-Properties>`_ for details
        on using this class member.

        :getter: Gets the bounding box of all contained shapes
        """
        all_box = []
        for elem in self._elements:
            all_box += list(elem.bbox)
        return utilities.evaluate_bounding_box(all_box)

    @property
    def vis(self):
        """ Visualization component.

        Please refer to the `wiki <https://github.com/orbingol/NURBS-Python/wiki/Using-Python-Properties>`_ for details
        on using this class member.

        :getter: Gets the visualization component
        :setter: Sets the visualization component
        """
        return self._vis_component

    @vis.setter
    def vis(self, value):
        if not isinstance(value, vis.VisAbstract):
            warnings.warn("Visualization component is NOT an instance of the vis.VisAbstract class")
            return
        self._vis_component = value

    @property
    def delta(self):
        """ Evaluation delta (for all parametric directions).

        Evaluation delta corresponds to the *step size*. Decreasing the step size results in evaluation of more points.
        Therefore; smaller the delta value, smoother the shape.

        The following figure illustrates the working principles of the delta property:

        .. math::

            \\left[{{u_{start}},{u_{start}} + \\delta ,({u_{start}} + \\delta ) + \\delta , \\ldots ,{u_{end}}} \\right]

        Please refer to the `wiki <https://github.com/orbingol/NURBS-Python/wiki/Using-Python-Properties>`_ for details
        on using this class member.

        :getter: Gets the delta value
        :setter: Sets the delta value
        """
        return self._delta[0] if self._pdim == 1 else self._delta

    @delta.setter
    def delta(self, value):
        if self._pdim == 1 and isinstance(value, (int, float)):
            delta_vals = [value]
        else:
            if isinstance(value, (list, tuple)):
                if len(value) != self._pdim:
                    raise ValueError("The input must be a list of a tuple with a length of " + str(self._pdim))
                delta_vals = value
            elif isinstance(value, (int, float)):
                delta_vals = [value for _ in range(self._pdim)]
            else:
                raise TypeError("Unsupported input type for evaluation delta. Use float, list or tuple")

        # Set delta values
        for idx, dval in enumerate(delta_vals):
            self._delta_setter_common(idx, dval)

        # Reset the cache
        self.reset()

    def _delta_setter_common(self, idx, value):
        # Check and set the delta value corresponding to the idx-th parametric dimension
        if float(value) <= 0 or float(value) >= 1:
            raise ValueError("Evaluation delta should be between 0.0 and 1.0. You are trying to set it to " + str(value)
                             + " for the " + str(idx + 1) + "st parametric dimension.")
        self._delta[idx] = float(value)

    @property
    def sample_size(self):
        """ Sample size (for all parametric directions).

        Sample size defines the number of points to evaluate. It also sets the ``delta`` property.

        The following figure illustrates the working principles of sample size property:

        .. math::

            \\underbrace {\\left[ {{u_{start}}, \\ldots ,{u_{end}}} \\right]}_{{n_{sample}}}

        Please refer to the `wiki <https://github.com/orbingol/NURBS-Python/wiki/Using-Python-Properties>`_ for details
        on using this class member.

        :getter: Gets sample size
        :setter: Sets sample size
        """
        ssz = [self._sample_size_getter_common(idx) for idx in range(self._pdim)]
        return ssz[0] if self._pdim == 1 else ssz

    @sample_size.setter
    def sample_size(self, value):
        if self._pdim == 1 and isinstance(value, (int, float)):
            ssz = [value]
        else:
            if isinstance(value, (list, tuple)):
                if len(value) != self._pdim:
                    raise ValueError("The input must be a list of a tuple with a length of " + str(self._pdim))
                ssz = value
            elif isinstance(value, (int, float)):
                ssz = [value for _ in range(self._pdim)]
            else:
                raise TypeError("Unsupported input type for sample size. Use float, list or tuple")

        # Set sample size
        for idx, sval in enumerate(ssz):
            self._sample_size_setter_common(idx, sval)

        # Reset the cache
        self.reset()

    def _sample_size_getter_common(self, idx):
        return int(1 / self._delta[idx]) + 1

    def _sample_size_setter_common(self, idx, value):
        # Check and set the delta value corresponding to the idx-th parametric dimension
        if not isinstance(value, int):
            raise GeomdlException("Sample size must be an integer value bigger than 2")
        if value < 2:
            raise GeomdlException("Sample size must be an integer value bigger than 2")
        self._delta[idx] = 1.0 / float(value - 1)

    def add(self, element):
        """ Adds shapes to the container.

        The input can be a single shape, a list of shapes or a container object.

        :param element: shape to be added
        """
        if isinstance(element, (self.__class__, list, tuple)):
            for elem in element:
                self.add(elem)
        elif hasattr(self, '_pdim'):
            if element.pdimension == self.pdimension:
                if self.dimension == 0:
                    self._dimension = element.dimension
                else:
                    if self.dimension != element.dimension:
                        raise GeomdlException("The spatial dimensions of the container and the input must be the same")
                self._elements.append(element)
        else:
            raise GeomdlException("Cannot add the element to the container")

        # Reset the cache
        self.reset()

    # Make container look like a list
    append = add

    def reset(self):
        """ Resets the cache. """
        self._cache['evalpts'][:] = []

    # Runs visualization component to render the surface
    @abc.abstractmethod
    def render(self, **kwargs):
        """ Renders plots using the visualization component.

        .. note::

            This is an abstract method and it must be implemented in the subclass.
        """
        pass


class CurveContainer(AbstractContainer):
    """ Container class for storing multiple curves.

    This class implements Python Iterator Protocol and therefore any instance of this class can be directly used in
    a for loop.

    This class provides the following properties:

    * :py:attr:`dimension`
    * :py:attr:`evalpts`
    * :py:attr:`bbox`
    * :py:attr:`vis`
    * :py:attr:`delta`
    * :py:attr:`sample_size`

    The following code example illustrates the usage of the Python properties:

    .. code-block:: python

        # Create a multi-curve container instance
        mcrv = Multi.CurveContainer()

        # Add single or multi curves to the multi container using mcrv.add() command
        # Addition operator, e.g. mcrv1 + mcrv2, also works

        # Set the evaluation delta of the multi-curve
        mcrv.delta = 0.05

        # Get the evaluated points
        curve_points = mcrv.evalpts
    """

    def __init__(self, *args, **kwargs):
        self._pdim = 1 if not hasattr(self, '_pdim') else self._pdim  # number of parametric dimensions
        self._dinit = 0.01 if not hasattr(self, '_dinit') else self._dinit  # evaluation delta
        super(CurveContainer, self).__init__(*args, **kwargs)
        for arg in args:
            self.add(arg)

    def render(self, **kwargs):
        """ Renders the curves.

        The visualization component must be set using :py:attr:`~vis` property before calling this method.

        Keyword Arguments:

        * ``cpcolor``: sets the color of the control points grid
        * ``evalcolor``: sets the color of the surface
        * ``filename``: saves the plot with the input name
        * ``plot``: controls plot window visibility. *Default: True*
        * ``animate``: activates animation (if supported). *Default: False*
        * ``delta``: if True, the evaluation delta of the Multi object will be used. *Default: True*

        The ``cpcolor`` and ``evalcolor`` arguments can be a string or a list of strings corresponding to the color
        values. Both arguments are processed separately, e.g. ``cpcolor`` can be a string whereas ``evalcolor`` can be
        a list or  a tuple, or vice versa. A single string value sets the color to the same value. List input allows
        customization over the color values. If none provided, a random color will be selected.

        The ``plot`` argument is useful when you would like to work on the command line without any window context.
        If ``plot`` flag is False, this method saves the plot as an image file (.png file where possible) and disables
        plot window popping out. If you don't provide a file name, the name of the image file will be pulled from the
        configuration class.
        """
        if not self._vis_component:
            warnings.warn("No visualization component has set")
            return

        # Get the color values from keyword arguments
        cpcolor = kwargs.get('cpcolor')
        evalcolor = kwargs.get('evalcolor')
        filename = kwargs.get('filename', None)
        plot_visible = kwargs.get('plot', True)
        animate_plot = kwargs.get('animate', False)
        # Flag to control evaluation delta updates
        update_delta = kwargs.get('delta', True)

        # Check if the input list sizes are equal
        if isinstance(cpcolor, (list, tuple)):
            if len(cpcolor) < len(self._elements):
                raise ValueError("The number of color values in 'cpcolor' (" + str(len(cpcolor)) +
                                 ") cannot be less than the number of shaped contained ("
                                 + str(len(self._elements)) + ")")

        if isinstance(evalcolor, (list, tuple)):
            if len(evalcolor) < len(self._elements):
                raise ValueError("The number of color values in 'evalcolor' (" + str(len(evalcolor)) +
                                 ") cannot be less than the number of shapes contained ("
                                 + str(len(self._elements)) + ")")

        # Run the visualization component
        self._vis_component.clear()
        for idx, elem in enumerate(self._elements):
            if update_delta:
                elem.delta = self.delta
            elem.evaluate()

            # Fix element name
            if elem.name == "curve":
                elem.name = elem.name + " " + str(idx)

            # Color selection
            color = select_color(cpcolor, evalcolor, idx=idx)

            self._vis_component.add(ptsarr=elem.ctrlpts, name=(elem.name, "(CP)"),
                                    color=color[0], plot_type='ctrlpts', idx=idx)
            self._vis_component.add(ptsarr=elem.evalpts, name=elem.name,
                                    color=color[1], plot_type='evalpts', idx=idx)

        # Display the figures
        if animate_plot:
            self._vis_component.animate(fig_save_as=filename, display_plot=plot_visible)
        else:
            self._vis_component.render(fig_save_as=filename, display_plot=plot_visible)


class SurfaceContainer(AbstractContainer):
    """ Container class for storing multiple surfaces.

    This class implements Python Iterator Protocol and therefore any instance of this class can be directly used in
    a for loop.

    This class provides the following properties:

    * :py:attr:`dimension`
    * :py:attr:`evalpts`
    * :py:attr:`bbox`
    * :py:attr:`vis`
    * :py:attr:`delta`
    * :py:attr:`delta_u`
    * :py:attr:`delta_v`
    * :py:attr:`sample_size`
    * :py:attr:`sample_size_u`
    * :py:attr:`sample_size_v`

    The following code example illustrates the usage of these Python properties:

    .. code-block:: python

        # Create a multi-surface container instance
        msurf = Multi.SurfaceContainer()

        # Add single or multi surfaces to the multi container using msurf.add() command
        # Addition operator, e.g. msurf1 + msurf2, also works

        # Set the evaluation delta of the multi-surface
        msurf.delta = 0.05

        # Get the evaluated points
        surface_points = msurf.evalpts
    """

    def __init__(self, *args, **kwargs):
        self._pdim = 2 if not hasattr(self, '_pdim') else self._pdim  # number of parametric dimensions
        self._dinit = 0.05 if not hasattr(self, '_dinit') else self._dinit  # evaluation delta
        super(SurfaceContainer, self).__init__(*args, **kwargs)
        for arg in args:
            self.add(arg)

    @property
    def delta_u(self):
        """ Evaluation delta for the u-direction.

        Evaluation delta corresponds to the *step size*. Decreasing the step size results in evaluation of more points.
        Therefore; smaller the delta, smoother the shape.

        Please note that ``delta_u`` and ``sample_size_u`` properties correspond to the same variable with different
        descriptions. Therefore, setting ``delta_u`` will also set ``sample_size_u``.

        Please refer to the `wiki <https://github.com/orbingol/NURBS-Python/wiki/Using-Python-Properties>`_ for details
        on using this class member.

        :getter: Gets the delta value for the u-direction
        :setter: Sets the delta value for the u-direction
        :type: float
        """
        return self._delta[0]

    @delta_u.setter
    def delta_u(self, value):
        self._delta_setter_common(0, value)

    @property
    def delta_v(self):
        """ Evaluation delta for the v-direction.

        Evaluation delta corresponds to the *step size*. Decreasing the step size results in evaluation of more points.
        Therefore; smaller the delta, smoother the shape.

        Please note that ``delta_v`` and ``sample_size_v`` properties correspond to the same variable with different
        descriptions. Therefore, setting ``delta_v`` will also set ``sample_size_v``.

        Please refer to the `wiki <https://github.com/orbingol/NURBS-Python/wiki/Using-Python-Properties>`_ for details
        on using this class member.

        :getter: Gets the delta value for the v-direction
        :setter: Sets the delta value for the v-direction
        :type: float
        """
        return self._delta[1]

    @delta_v.setter
    def delta_v(self, value):
        self._delta_setter_common(1, value)

    @property
    def sample_size_u(self):
        """ Sample size for the u-direction.

        Sample size defines the number of points to evaluate. It also sets the ``delta_u`` property.

        Please refer to the `wiki <https://github.com/orbingol/NURBS-Python/wiki/Using-Python-Properties>`_ for details
        on using this class member.

        :getter: Gets sample size for the u-direction
        :setter: Sets sample size for the u-direction
        :type: int
        """
        return self._sample_size_getter_common(0)

    @sample_size_u.setter
    def sample_size_u(self, value):
        self._sample_size_setter_common(0, value)

    @property
    def sample_size_v(self):
        """ Sample size for the v-direction.

        Sample size defines the number of points to evaluate. It also sets the ``delta_v`` property.

        Please refer to the `wiki <https://github.com/orbingol/NURBS-Python/wiki/Using-Python-Properties>`_ for details
        on using this class member.

        :getter: Gets sample size for the v-direction
        :setter: Sets sample size for the v-direction
        :type: int
        """
        return self._sample_size_getter_common(1)

    @sample_size_v.setter
    def sample_size_v(self, value):
        self._sample_size_setter_common(1, value)

    def set_tessellator(self, tsl):
        """ Sets the tessellation component of the surfaces inside the container.

        Please refer to :doc:`Tessellation <module_tessellate>` documentation for details.

        .. code-block:: python
            :linenos:

            from geomdl import multi
            from geomdl import tessellate

            # Create the surface container
            surf_container = multi.SurfaceContainer(surf_list)

            # Set tessellator component (use a tessellator type object)
            surf_container.set_tessellator(tessellate.TrimTessellate)

            # You can also use like the following
            tsl = tessellator.TrimTessellate()
            surf_container.set_tessellator(tsl.__class__)

        :param tsl: tessellation component type
        """
        # Set tessellation component
        for idx in range(len(self._elements)):
            self._elements[idx].tessellator = tsl()

    def render(self, **kwargs):
        """ Renders the surfaces.

        The visualization component must be set using :py:attr:`~vis` property before calling this method.

        Keyword Arguments:
            * ``cpcolor``: sets the color of the control points grids
            * ``evalcolor``: sets the color of the surface
            * ``filename``: saves the plot with the input name
            * ``plot``: controls plot window visibility. *Default: True*
            * ``animate``: activates animation (if supported). *Default: False*
            * ``colormap``: sets the colormap of the surfaces
            * ``delta``: if True, the evaluation delta of the Multi object will be used. *Default: True*
            * ``num_procs``: number of concurrent processes for rendering the surfaces. *Default: 1*

        The ``cpcolor`` and ``evalcolor`` arguments can be a string or a list of strings corresponding to the color
        values. Both arguments are processed separately, e.g. ``cpcolor`` can be a string whereas ``evalcolor`` can be
        a list or  a tuple, or vice versa. A single string value sets the color to the same value. List input allows
        customization over the color values. If none provided, a random color will be selected.

        The ``plot`` argument is useful when you would like to work on the command line without any window context.
        If ``plot`` flag is False, this method saves the plot as an image file (.png file where possible) and disables
        plot window popping out. If you don't provide a file name, the name of the image file will be pulled from the
        configuration class.

        Please note that ``colormap`` argument can only work with visualization classes that support colormaps. As an
        example, please see :py:class:`.VisMPL.VisSurfTriangle()` class documentation. This method expects multiple
        colormap inputs as a list or tuple, preferable the input list size is the same as the number of surfaces
        contained in the class. In the case of number of surfaces is bigger than number of input colormaps, this method
        will automatically assign a random color for the remaining surfaces.
        """
        # Validation
        if not self._vis_component:
            warnings.warn("No visualization component has been set")
            return

        # Get the color values from keyword arguments
        cpcolor = kwargs.get('cpcolor')
        evalcolor = kwargs.get('evalcolor')
        trimcolor = kwargs.get('trimcolor', 'black')
        filename = kwargs.get('filename', None)
        plot_visible = kwargs.get('plot', True)
        animate_plot = kwargs.get('animate', False)
        # Flag to control evaluation delta updates
        update_delta = kwargs.get('delta', True)
        # Number of parallel processes
        num_procs = kwargs.get('num_procs', 1)

        # Check if the input list sizes are equal
        if isinstance(cpcolor, (list, tuple)):
            if len(cpcolor) != len(self._elements):
                raise ValueError("The number of colors in 'cpcolor' (" + str(len(cpcolor)) +
                                 ") cannot be less than the number of shapes contained(" +
                                 str(len(self._elements)) + ")")

        if isinstance(evalcolor, (list, tuple)):
            if len(evalcolor) != len(self._elements):
                raise ValueError("The number of colors in 'evalcolor' (" + str(len(evalcolor)) +
                                 ") cannot be less than the number of shapes contained ("
                                 + str(len(self._elements)) + ")")

        # Get colormaps as a list
        surf_cmaps = kwargs.get('colormap', [])
        if not isinstance(surf_cmaps, (list, tuple)):
            warnings.warn("Expecting a list of colormap values, not " + str(type(surf_cmaps)))
            surf_cmaps = []

        # Run the visualization component
        self._vis_component.clear()
        vis_list = []
        if num_procs > 1:
            with utl.pool_context(processes=num_procs) as pool:
                tmp = pool.map(partial(process_elements_surface, mconf=self._vis_component.mconf,
                                       colorval=(cpcolor, evalcolor, trimcolor), idx=-1,
                                       update_delta=update_delta, delta=self.delta), self._elements)
                vis_list += tmp
        else:
            for idx, elem in enumerate(self._elements):
                tmp = process_elements_surface(elem, self._vis_component.mconf, (cpcolor, evalcolor, trimcolor), idx, update_delta, self.delta)
                vis_list += tmp

        for vl in vis_list:
            if isinstance(vl, dict):
                self._vis_component.add(**vl)
            else:
                for v in vl:
                    self._vis_component.add(**v)

        # Display the figures
        if animate_plot:
            self._vis_component.animate(fig_save_as=filename, display_plot=plot_visible, colormap=surf_cmaps)
        else:
            self._vis_component.render(fig_save_as=filename, display_plot=plot_visible, colormap=surf_cmaps)


class VolumeContainer(SurfaceContainer):
    """ Container class for storing multiple volumes.

    This class implements Python Iterator Protocol and therefore any instance of this class can be directly used in
    a for loop.

    This class provides the following properties:

    * :py:attr:`dimension`
    * :py:attr:`evalpts`
    * :py:attr:`bbox`
    * :py:attr:`vis`
    * :py:attr:`delta`
    * :py:attr:`delta_u`
    * :py:attr:`delta_v`
    * :py:attr:`delta_w`
    * :py:attr:`sample_size`
    * :py:attr:`sample_size_u`
    * :py:attr:`sample_size_v`
    * :py:attr:`sample_size_w`

    The following code example illustrates the usage of these Python properties:

    .. code-block:: python

        # Create a multi-volume container instance
        mvol = Multi.VolumeContainer()

        # Add single or multi volumes to the multi container using mvol.add() command
        # Addition operator, e.g. mvol1 + mvol2, also works

        # Set the evaluation delta of the multi-volume
        mvol.delta = 0.05

        # Get the evaluated points
        volume_points = mvol.evalpts
    """

    def __init__(self, *args, **kwargs):
        self._pdim = 3 if not hasattr(self, '_pdim') else self._pdim  # number of parametric dimensions
        self._dinit = 0.1 if not hasattr(self, '_dinit') else self._dinit  # evaluation delta
        super(VolumeContainer, self).__init__()
        self._delta = [0.1, 0.1, 0.1]  # evaluation delta
        for arg in args:
            self.add(arg)

    @property
    def delta_w(self):
        """ Evaluation delta for the w-direction.

        Evaluation delta corresponds to the *step size*. Decreasing the step size results in evaluation of more points.
        Therefore; smaller the delta, smoother the shape.

        Please note that ``delta_w`` and ``sample_size_w`` properties correspond to the same variable with different
        descriptions. Therefore, setting ``delta_w`` will also set ``sample_size_w``.

        Please refer to the `wiki <https://github.com/orbingol/NURBS-Python/wiki/Using-Python-Properties>`_ for details
        on using this class member.

        :getter: Gets the delta value for the w-direction
        :setter: Sets the delta value for the w-direction
        :type: float
        """
        return self._delta[2]

    @delta_w.setter
    def delta_w(self, value):
        self._delta_setter_common(2, value)

    @property
    def sample_size_w(self):
        """ Sample size for the w-direction.

        Sample size defines the number of points to evaluate. It also sets the ``delta_w`` property.

        Please refer to the `wiki <https://github.com/orbingol/NURBS-Python/wiki/Using-Python-Properties>`_ for details
        on using this class member.

        :getter: Gets sample size for the w-direction
        :setter: Sets sample size for the w-direction
        :type: int
        """
        return self._sample_size_getter_common(2)

    @sample_size_w.setter
    def sample_size_w(self, value):
        self._sample_size_setter_common(2, value)

    def render(self, **kwargs):
        """ Renders the volumes.

        The visualization component must be set using :py:attr:`~vis` property before calling this method.

        Keyword Arguments:
            * ``cpcolor``: sets the color of the control points plot
            * ``evalcolor``: sets the color of the volume
            * ``filename``: saves the plot with the input name
            * ``plot``: controls plot window visibility. *Default: True*
            * ``animate``: activates animation (if supported). *Default: False*
            * ``delta``: if True, the evaluation delta of the Multi object will be used. *Default: True*
            * ``grid_size``: grid size for voxelization. *Default: (16, 16, 16)*
            * ``num_procs``: number of concurrent processes for voxelization. *Default: 1*

        The ``cpcolor`` and ``evalcolor`` arguments can be a string or a list of strings corresponding to the color
        values. Both arguments are processed separately, e.g. ``cpcolor`` can be a string whereas ``evalcolor`` can be
        a list or  a tuple, or vice versa. A single string value sets the color to the same value. List input allows
        customization over the color values. If none provided, a random color will be selected.

        The ``plot`` argument is useful when you would like to work on the command line without any window context.
        If ``plot`` flag is False, this method saves the plot as an image file (.png file where possible) and disables
        plot window popping out. If you don't provide a file name, the name of the image file will be pulled from the
        configuration class.
        """
        if not self._vis_component:
            warnings.warn("No visualization component has been set")
            return

        cpcolor = kwargs.pop('cpcolor', None)
        evalcolor = kwargs.pop('evalcolor', None)
        filename = kwargs.pop('filename', None)
        plot_visible = kwargs.pop('plot', True)
        animate_plot = kwargs.pop('animate', False)
        # Flag to control evaluation delta updates
        update_delta = kwargs.pop('delta', True)

        # Check if the input list sizes are equal
        if isinstance(cpcolor, (list, tuple)):
            if len(cpcolor) != len(self._elements):
                raise ValueError("The number of colors in 'cpcolor' (" + str(len(cpcolor)) +
                                 ") cannot be less than the number of shapes contained(" +
                                 str(len(self._elements)) + ")")

        if isinstance(evalcolor, (list, tuple)):
            if len(evalcolor) != len(self._elements):
                raise ValueError("The number of colors in 'evalcolor' (" + str(len(evalcolor)) +
                                 ") cannot be less than the number of shapes contained ("
                                 + str(len(self._elements)) + ")")

        # Run the visualization component
        self._vis_component.clear()
        for idx, elem in enumerate(self._elements):
            if update_delta:
                elem.delta = self.delta
            elem.evaluate()

            # Fix element name
            if elem.name == "volume":
                elem.name = elem.name + " " + str(idx)

            # Color selection
            color = select_color(cpcolor, evalcolor, idx=idx)

            # Add control points
            if self._vis_component.mconf['ctrlpts'] == 'points':
                self._vis_component.add(ptsarr=elem.ctrlpts, name=(elem.name, "(CP)"),
                                        color=color[0], plot_type='ctrlpts', idx=idx)

            # Add evaluated points
            if self._vis_component.mconf['evalpts'] == 'points':
                self._vis_component.add(ptsarr=elem.evalpts, name=elem.name,
                                        color=color[1], plot_type='evalpts', idx=idx)

            # Add evaluated points as voxels
            if self._vis_component.mconf['evalpts'] == 'voxels':
                grid, filled = voxelize.voxelize(elem, **kwargs)
                polygrid = voxelize.convert_bb_to_faces(grid)
                self._vis_component.add(ptsarr=[polygrid, filled], name=elem.name,
                                        color=color[1], plot_type='evalpts', idx=idx)

        # Display the figures
        if animate_plot:
            self._vis_component.animate(fig_save_as=filename, display_plot=plot_visible)
        else:
            self._vis_component.render(fig_save_as=filename, display_plot=plot_visible)


def select_color(cpcolor, evalcolor, idx=0):
    """ Selects item color for plotting.

    :param cpcolor: color for control points grid item
    :type cpcolor: str, list, tuple
    :param evalcolor: color for evaluated points grid item
    :type evalcolor: str, list, tuple
    :param idx: index of the current shape
    :type idx: int
    :return: a list of color values
    :rtype: list
    """
    # Random colors by default
    color = utilities.color_generator()

    # Constant color for control points grid
    if isinstance(cpcolor, str):
        color[0] = cpcolor

    # User-defined color for control points grid
    if isinstance(cpcolor, (list, tuple)):
        color[0] = cpcolor[idx]

    # Constant color for evaluated points grid
    if isinstance(evalcolor, str):
        color[1] = evalcolor

    # User-defined color for evaluated points grid
    if isinstance(evalcolor, (list, tuple)):
        color[1] = evalcolor[idx]

    return color


def process_elements_surface(elem, mconf, colorval, idx, update_delta, delta):
    """ Processes visualization elements for surfaces.

    :param elem: surface
    :type elem: abstract.Surface
    :param mconf: visualization module configuration
    :type mconf: dict
    :param colorval: color values
    :type colorval: tuple
    :param idx: index of the surface
    :type idx: int
    :param update_delta: flag to update surface delta
    :type update_delta: bool
    :param delta: new surface evaluation delta
    :type delta: list, tuple
    :return: visualization element (as a dict)
    :rtype: list
    """
    if update_delta:
        elem.delta = delta
    elem.evaluate()

    # Fix element name
    if elem.name == "surface" and idx >= 0:
        elem.name = elem.name + " " + str(idx)

    # Color selection
    color = select_color(colorval[0], colorval[1], idx=idx)

    # Initialize the return list
    rl = []

    # Add control points
    if mconf['ctrlpts'] == 'points':
        ret = dict(ptsarr=elem.ctrlpts, name=(elem.name, "(CP)"),
                   color=color[0], plot_type='ctrlpts', idx=idx)
        rl.append(ret)

    # Add control points as quads
    if mconf['ctrlpts'] == 'quads':
        qtsl = tessellate.QuadTessellate()
        qtsl.tessellate(elem.ctrlpts, size_u=elem.ctrlpts_size_u, size_v=elem.ctrlpts_size_v)
        ret = dict(ptsarr=[qtsl.vertices, qtsl.faces], name=(elem.name, "(CP)"),
                   color=color[0], plot_type='ctrlpts', idx=idx)
        rl.append(ret)

    # Add surface points
    if mconf['evalpts'] == 'points':
        ret = dict(ptsarr=elem.evalpts, name=(elem.name, idx), color=color[1], plot_type='evalpts', idx=idx)
        rl.append(ret)

    # Add surface points as quads
    if mconf['evalpts'] == 'quads':
        qtsl = tessellate.QuadTessellate()
        qtsl.tessellate(elem.evalpts, size_u=elem.sample_size_u, size_v=elem.sample_size_v)
        ret = dict(ptsarr=[qtsl.vertices, qtsl.faces],
                   name=elem.name, color=color[1], plot_type='evalpts', idx=idx)
        rl.append(ret)

    # Add surface points as vertices and triangles
    if mconf['evalpts'] == 'triangles':
        elem.tessellate()
        ret = dict(ptsarr=[elem.tessellator.vertices, elem.tessellator.faces],
                   name=elem.name, color=color[1], plot_type='evalpts', idx=idx)
        rl.append(ret)

    # Add the trim curves
    for itc, trim in enumerate(elem.trims):
        ret = dict(ptsarr=elem.evaluate_list(trim.evalpts), name=("trim", itc),
                   color=colorval[2], plot_type='trimcurve', idx=idx)
        rl.append(ret)

    # Return the list
    return rl
