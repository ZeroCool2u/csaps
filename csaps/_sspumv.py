# -*- coding: utf-8 -*-

"""
Univariate/multivariate cubic smoothing spline implementation

"""

import functools
from typing import Optional, Union, Tuple, List

import numpy as np

import scipy.sparse as sp
import scipy.sparse.linalg as la
from scipy.interpolate import PPoly

from ._base import ISplinePPForm, ISmoothingSpline
from ._types import UnivariateDataType, MultivariateDataType
from ._reshape import to_2d, prod


class SplinePPForm(ISplinePPForm[np.ndarray, int], PPoly):
    """The base class for univariate/multivariate spline in piecewise polynomial form

    Piecewise polynomial in terms of coefficients and breakpoints.

    Notes
    -----

    Inherited from :py:class:`scipy.interpolate.PPoly`

    """

    __module__ = 'csaps'

    @property
    def breaks(self) -> np.ndarray:
        return self.x

    @property
    def coeffs(self) -> np.ndarray:
        return self.c

    @property
    def order(self) -> int:
        return self.c.shape[0]

    @property
    def pieces(self) -> int:
        return self.c.shape[1]

    @property
    def gcv(self) -> float:
        return self.gcv

    @property
    def degrees_of_freedom(self) -> float:
        return self.degrees_of_freedom

    @property
    def ndim(self) -> int:
        """Returns the number of spline dimensions

        The number of dimensions is product of shape without ``shape[self.axis]``.
        """
        shape = list(self.shape)
        shape.pop(self.axis)

        return prod(shape)

    @property
    def shape(self) -> Tuple[int]:
        """Returns the source data shape
        """
        shape: List[int] = list(self.c.shape[2:])
        shape.insert(self.axis, self.c.shape[1] + 1)

        return tuple(shape)

    def __repr__(self):  # pragma: no cover
        return (
            f'{type(self).__name__}\n'
            f'  breaks: {self.breaks}\n'
            f'  coeffs shape: {self.coeffs.shape}\n'
            f'  data shape: {self.shape}\n'
            f'  axis: {self.axis}\n'
            f'  pieces: {self.pieces}\n'
            f'  order: {self.order}\n'
            f'  ndim: {self.ndim}\n'
            f'  degrees of freedom: {self.degrees_of_freedom}\n'
            f'  gcv: {self.gcv}\n'

        )


class CubicSmoothingSpline(ISmoothingSpline[
                               SplinePPForm,
                               float,
                               UnivariateDataType,
                               int,
                               Union[bool, str]
                           ]):
    """Cubic smoothing spline

    The cubic spline implementation for univariate/multivariate data.

    Parameters
    ----------

    xdata : np.ndarray, sequence, vector-like
        X input 1-D data vector (data sites: ``x1 < x2 < ... < xN``)

    ydata : np.ndarray, vector-like, sequence[vector-like]
        Y input 1-D data vector or ND-array with shape[axis] equal of `xdata` size)

    weights : [*Optional*] np.ndarray, list
        Weights 1-D vector with size equal of ``xdata`` size

    smooth : [*Optional*] float
        Smoothing parameter in range [0, 1] where:
            - 0: The smoothing spline is the least-squares straight line fit
            - 1: The cubic spline interpolant with natural condition

    axis : [*Optional*] int
        Axis along which ``ydata`` is assumed to be varying.
        Meaning that for x[i] the corresponding values are np.take(ydata, i, axis=axis).
        By default is -1 (the last axis).

    normalizedsmooth : [*Optional*] bool
        If True, the smooth parameter is normalized such that results are invariant to xdata range
        and less sensitive to nonuniformity of weights and xdata clumping

        .. versionadded:: 1.1.0

    calculate_degrees_of_freedom : [*Optional*] bool
        If True, the degrees of freedom for the spline will be calculated and set as a property on the returned
        spline object. Typically the degrees of freedom may be used to calculate the Generalized Cross Validation
        criterion. The GCV can be minimized to attempt to identify an optimal smoothing parameter, while penalizing
        over fitting.
        Strictly speaking this involves generating splines for all smoothing parameter values across the valid domain
        of the smoothing parameter [0,1] then selecting the smoothing parameter that produces the lowest GCV. See
        [GCV in TEOSL (page 244 section 7.52)](https://hastie.su.domains/ElemStatLearn/printings/ESLII_print12_toc.pdf)
        for more information on methodology.
        The simplest way to use the GCV is to setup a loop that generates a spline with your data at every step, a step
        size of 0.001 is generally sufficient, and keep track of the spline that produces the lowest GCV. Setting this
        parameter to True, does _not_ generate the lowest GCV, it simply sets the neccesary dependencies to use the
        calculate_gcv function. You must still compute the GCV for each smoothing parameter.

    """

    __module__ = 'csaps'

    def __init__(self,
                 xdata: UnivariateDataType,
                 ydata: MultivariateDataType,
                 weights: Optional[UnivariateDataType] = None,
                 smooth: Optional[float] = None,
                 axis: int = -1,
                 normalizedsmooth: bool = False,
                 calculate_degrees_of_freedom: bool = False):

        x, y, w, shape, axis = self._prepare_data(xdata, ydata, weights, axis)
        coeffs, smooth, degrees_of_freedom = self._make_spline(x, y, w, smooth, shape, normalizedsmooth, calculate_degrees_of_freedom)
        spline = SplinePPForm.construct_fast(coeffs, x, axis=axis)
        self.degrees_of_freedom = degrees_of_freedom
        self.gcv = None
        self._smooth = smooth
        self._spline = spline

    def __call__(self,
                 x: UnivariateDataType,
                 nu: Optional[int] = None,
                 extrapolate: Optional[Union[bool, str]] = None) -> np.ndarray:
        """Evaluate the spline for given data

        Parameters
        ----------

        x : 1-d array-like
            Points to evaluate the spline at.

        nu : [*Optional*] int
            Order of derivative to evaluate. Must be non-negative.

        extrapolate : [*Optional*] bool or 'periodic'
            If bool, determines whether to extrapolate to out-of-bounds points
            based on first and last intervals, or to return NaNs. If 'periodic',
            periodic extrapolation is used. Default is True.

        Notes
        -----

        Derivatives are evaluated piecewise for each polynomial
        segment, even if the polynomial is not differentiable at the
        breakpoints. The polynomial intervals are considered half-open,
        ``[a, b)``, except for the last interval which is closed
        ``[a, b]``.

        """
        if nu is None:
            nu = 0
        return self._spline(x, nu=nu, extrapolate=extrapolate)

    @property
    def smooth(self) -> float:
        """Returns the smoothing factor

        Returns
        -------
        smooth : float
            Smoothing factor in the range [0, 1]
        """
        return self._smooth

    @property
    def spline(self) -> SplinePPForm:
        """Returns the spline description in `SplinePPForm` instance

        Returns
        -------
        spline : SplinePPForm
            The spline representation in :class:`SplinePPForm` instance
        """
        return self._spline

    def compute_gcv(self, y, y_pred) -> float:
        """Computes the GCV using the degrees of freedom, which must be computed upon spline creation

        Parameters
        ----------

        y : 1-d array-like
            Points the spline was evaluated at

        y_pred : 1-d array-like
            Predicted values returned from the generated spline object

        Returns
        -------
        gcv : float
            The generalized cross validation criterion


        """
        if not self.degrees_of_freedom:
            raise ValueError("You must recreate the spline with the calculate_degrees_of_freedom parameter set to True")

        y = np.asarray(y, dtype=np.float64)
        y_pred = np.asarray(y_pred, dtype=np.float64)
        self.gcv: float = np.linalg.norm(y-y_pred)**2 / (y.size - self.degrees_of_freedom)**2
        return self.gcv

    @staticmethod
    def _prepare_data(xdata, ydata, weights, axis):
        xdata = np.asarray(xdata, dtype=np.float64)
        ydata = np.asarray(ydata, dtype=np.float64)

        if xdata.ndim > 1:
            raise ValueError("'xdata' must be a vector")
        if xdata.size < 2:
            raise ValueError("'xdata' must contain at least 2 data points.")

        axis = ydata.ndim + axis if axis < 0 else axis

        if ydata.shape[axis] != xdata.size:
            raise ValueError(
                f"'ydata' data must be a 1-D or N-D array with shape[{axis}] "
                f"that is equal to 'xdata' size ({xdata.size})")

        # Rolling axis for using its shape while constructing coeffs array
        shape = np.rollaxis(ydata, axis).shape

        # Reshape ydata N-D array to 2-D NxM array where N is the data
        # dimension and M is the number of data points.
        ydata = to_2d(ydata, axis)

        if weights is None:
            weights = np.ones_like(xdata)
        else:
            weights = np.asarray(weights, dtype=np.float64)
            if weights.size != xdata.size:
                raise ValueError('Weights vector size must be equal of xdata size')

        return xdata, ydata, weights, shape, axis

    @staticmethod
    def _compute_smooth(a, b):
        """
        The calculation of the smoothing spline requires the solution of a
        linear system whose coefficient matrix has the form p*A + (1-p)*B, with
        the matrices A and B depending on the data sites x. The default value
        of p makes p*trace(A) equal (1 - p)*trace(B).
        """

        def trace(m: sp.dia_matrix):
            return m.diagonal().sum()

        return 1. / (1. + trace(a) / (6. * trace(b)))

    @staticmethod
    def _normalize_smooth(x: np.ndarray, w: np.ndarray, smooth: Optional[float]):
        """
        See the explanation here: https://github.com/espdev/csaps/pull/47
        """

        span = np.ptp(x)

        eff_x = 1 + (span ** 2) / np.sum(np.diff(x) ** 2)
        eff_w = np.sum(w) ** 2 / np.sum(w ** 2)
        k = 80 * (span ** 3) * (x.size ** -2) * (eff_x ** -0.5) * (eff_w ** -0.5)

        s = 0.5 if smooth is None else smooth
        p = s / (s + (1 - s) * k)

        return p

    @staticmethod
    def _make_spline(x, y, w, smooth, shape, normalizedsmooth, calculate_degrees_of_freedom):
        pcount = x.size
        dx = np.diff(x)

        if not all(dx > 0):  # pragma: no cover
            raise ValueError(
                "Items of 'xdata' vector must satisfy the condition: x1 < x2 < ... < xN")

        dy = np.diff(y, axis=1)
        dy_dx = dy / dx

        if pcount == 2:
            # The corner case for the data with 2 points (1 breaks interval)
            # In this case we have 2-ordered spline and linear interpolation in fact
            yi = y[:, 0][:, np.newaxis]

            c_shape = (2, pcount - 1) + shape[1:]
            c = np.vstack((dy_dx, yi)).reshape(c_shape)
            p = 1.0

            return c, p

        # Create diagonal sparse matrices
        diags_r = np.vstack((dx[1:], 2 * (dx[1:] + dx[:-1]), dx[:-1]))
        r = sp.spdiags(diags_r, [-1, 0, 1], pcount - 2, pcount - 2)

        dx_recip = 1. / dx
        diags_qtw = np.vstack((dx_recip[:-1], -(dx_recip[1:] + dx_recip[:-1]), dx_recip[1:]))
        diags_sqrw_recip = 1. / np.sqrt(w)

        # Calculate and store qt separately, so we can use it later to calculate the degrees of freedom for the gcv
        qt = sp.diags(diags_qtw, [0, 1, 2], (pcount - 2, pcount))
        qtw = (qt @ sp.diags(diags_sqrw_recip, 0, (pcount, pcount)))
        qtw = qtw @ qtw.T

        p = smooth

        if normalizedsmooth:
            p = CubicSmoothingSpline._normalize_smooth(x, w, smooth)
        elif smooth is None:
            p = CubicSmoothingSpline._compute_smooth(r, qtw)

        pp = (6. * (1. - p))

        # Solve linear system for the 2nd derivatives
        a = pp * qtw + p * r
        b = np.diff(dy_dx, axis=1).T

        u = la.spsolve(a, b)
        if u.ndim < 2:
            u = u[np.newaxis]
        if y.shape[0] == 1:
            u = u.T

        dx = dx[:, np.newaxis]

        vpad = functools.partial(np.pad, pad_width=[(1, 1), (0, 0)], mode='constant')

        d1 = np.diff(vpad(u), axis=0) / dx
        d2 = np.diff(vpad(d1), axis=0)

        diags_w_recip = 1. / w
        w = sp.diags(diags_w_recip, 0, (pcount, pcount))

        yi = y.T - (pp * w) @ d2
        pu = vpad(p * u)

        c1 = np.diff(pu, axis=0) / dx
        c2 = 3. * pu[:-1, :]
        c3 = np.diff(yi, axis=0) / dx - dx * (2. * pu[:-1, :] + pu[1:, :])
        c4 = yi[:-1, :]

        c_shape = (4, pcount - 1) + shape[1:]
        c = np.vstack((c1, c2, c3, c4)).reshape(c_shape)

        # As calculating the GCV is a relatively expensive operation, we store the degrees of freedom
        # required for the GCV calculation
        if calculate_degrees_of_freedom:
            degrees_of_freedom = p * (la.inv(p * w + ((1-p) * 6 * qt.T @ la.inv(r) @ qt)) @ w).trace()
            return c, p, degrees_of_freedom
        else:
            return c, p, None
