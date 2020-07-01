# -*- coding: utf-8 -*-

from typing import NamedTuple

import pytest
import numpy as np


class UnivariateData(NamedTuple):
    x: np.ndarray
    y: np.ndarray
    xi: np.ndarray
    yi: np.ndarray
    smooth: float


@pytest.fixture(scope='session')
def univariate_data() -> UnivariateData:
    """Univariate exponential noisy data sample
    """

    x = np.linspace(-5., 5., 25)
    y = np.array([
        0.015771474002402, 0.161329316958106, 0.133494845724251, 0.281006799675995, 0.343006057841707,
        0.278153538271205, 0.390818717714371, 0.679913441859782, 0.868622194535066, 0.981580573494033,
        0.942184497801730, 1.062903014773386, 1.145038880551641, 1.126415085211218, 0.945914543251488,
        0.887159638891092, 0.732105338022297, 0.443482323476481, 0.539727427655155, 0.461168113877247,
        0.218479110576478, 0.230018078091912, 0.024790896515009, 0.085343887446749, 0.238257669483491,
    ])

    xi = np.linspace(-5., 5., 100)
    yi = np.array([
        0.027180620841235, 0.055266722842603, 0.081889893919483, 0.105587203147386, 0.124895719601823,
        0.138845028755704, 0.149340839533796, 0.159329894062361, 0.171760370375527, 0.189200881318870,
        0.210916416800576, 0.234470952365328, 0.257414405587860, 0.277378327575793, 0.293102526279226,
        0.304125512134026, 0.310003428419162, 0.310378253365020, 0.306866169084541, 0.303057561573221,
        0.302628651777970, 0.309224604926640, 0.325083877194873, 0.350493015304832, 0.385594789501554,
        0.430522770904909, 0.484297436489629, 0.543777468816333, 0.605573174066145, 0.666295736381613,
        0.723192861937517, 0.775270813640449, 0.821836995165352, 0.862198810187169, 0.895800934807012,
        0.922637134830661, 0.942838448490065, 0.956535914017174, 0.964201067822575, 0.968293836555378,
        0.971993858758319, 0.978481765680190, 0.990589029304687, 1.008108142826666, 1.029266848660349,
        1.052279957395322, 1.075372085392223, 1.096900972159461, 1.115320296869396, 1.129085856740936,
        1.136683629726760, 1.137293750656333, 1.130790511235904, 1.117078383905495, 1.096086194963815,
        1.068845910308547, 1.037920180955498, 1.005984407266240, 0.975701613072527, 0.948237262097737,
        0.921848333557257, 0.894457640361302, 0.863988793631958, 0.828944108099870, 0.789424716879042,
        0.745805539756215, 0.698461496518133, 0.648486500475627, 0.599850439035886, 0.557242193130187,
        0.525350643689810, 0.507735527292642, 0.501362772528695, 0.500811632605449, 0.500658068764342,
        0.495835799645429, 0.484392358284163, 0.465978560872775, 0.440258473877521, 0.407065767289394,
        0.368536648551231, 0.328466725991911, 0.290688242301654, 0.258885509945327, 0.233340446204702,
        0.210932573178451, 0.188393482739897, 0.162519263868190, 0.133027485558460, 0.103689479346398,
        0.078575174479879, 0.061741087177262, 0.055620757085748, 0.059495661916820, 0.072285127585087,
        0.092908288203052, 0.120145221354215, 0.152391824997807, 0.187978208969687, 0.225234483105709,
    ])

    smooth = 0.992026535689226

    return UnivariateData(x, y, xi, yi, smooth)


@pytest.fixture(scope='session')
def surface_data():
    """2-d surface data (61, 51)
    """
    np.random.seed(12345)

    xdata = [np.linspace(-3.0, 3.0, 61), np.linspace(-3.5, 3.5, 51)]
    i, j = np.meshgrid(*xdata, indexing='ij')

    ydata = (3 * (1 - j) ** 2. * np.exp(-(j ** 2) - (i + 1) ** 2)
             - 10 * (j / 5 - j ** 3 - i ** 5) * np.exp(-j ** 2 - i ** 2)
             - 1 / 3 * np.exp(-(j + 1) ** 2 - i ** 2))

    ydata = ydata + (np.random.randn(*ydata.shape) * 0.75)

    return xdata, ydata
