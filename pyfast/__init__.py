"""
pyfast
======

Author: David Coss, PhD
License: GNU Public License version 3

Package for Fourier Amplitude Sensitivity Testing

Makes use of Equations from Cukier, R., Schaibly, J., Shuler, K.,
J. Chem. Phys., 1975, 26: 1-42

Gained code inspiration from the R package, fast, which is released
under GPL at http://cran.r-project.org/web/packages/fast/index.html

Adapted code from SALib by "Jon Herman, Patrick Reed and others"
available under LGPL at https://github.com/jdherman/SALib

"""

import pkg_resources
__version__ = pkg_resources.require("pyfast")[0].version


# Cukier et al 1975 Table VI, Omega_n column
CUKIER_FREQUENCIES = [0, 0, 1, 5, 11, 1, 17, 23, 19, 25, 41, 31, 23,
                      87, 67, 73, 58, 143, 149, 99, 119, 237, 267, 283,
                      151, 385, 157, 215, 449, 163, 337, 253, 375, 441,
                      673, 773, 875, 873, 587, 849, 623, 637, 891, 943,
                      1171, 1225, 1335, 1725, 1663, 2019]

# Cukier et al 1975 Table VI, d_n column
CUKIER_FREQ_OFFSETS = [4, 8, 6, 10, 20, 22, 32, 40, 38, 26, 56, 62, 46,
                       76, 96, 60, 86, 126, 134, 112, 92, 128, 154, 196,
                       34, 416, 106, 208, 328, 198, 382, 88, 348, 186, 140,
                       170, 284, 568, 302, 438, 410, 248, 448, 388, 596, 217,
                       100, 488, 166]

DEFAULT_M = 4


def freq(m, i=1, omega_0=0, omega_0_list=CUKIER_FREQUENCIES,
         delta_omega_list=CUKIER_FREQ_OFFSETS):
    if i <= 1:
        omega = omega_0_list[m - 1]
        return [omega] + list(freq(m, i + 1, omega))

    o = omega_0 + delta_omega_list[m - i]

    if i == m:
        return [o]

    return [o] + freq(m, i + 1, o)


def get_fast_parameters(mins, maxs, omegas, factor=1):
    from pyfast.parameters import generate_samples

    return generate_samples(mins, maxs, omegas, factor)


def double_series(x):
    from numpy import append
    if len(x) == 0:
        return x

    return append(x, x[-2::-1])


def fast(model, num_params, M=DEFAULT_M):
    from pyfast.parameters import MIN_RUNS_CUKIER75
    import numpy as np

    nsamples = len(model)

    # TODO: Add model dimension checks

    FF = np.abs(np.fft.fft(double_series(model))) / nsamples
    FF = FF[0:nsamples + 1]
    #FF = np.abs(np.fft.fft(model))/nsamples
    num_freqs = len(FF)

    # Frequencies
    cukier = freq(num_params)
    frequencies = np.outer(cukier, np.arange(1, M + 1))

    # Sensitivity Values
    total = np.sum(FF[1:] ** 2)
    sensitivities = []
    for i in xrange(0, frequencies.shape[0]):
        frequency_vals = []
        for frequency in frequencies[i, :]:
            if frequency + 1 >= num_freqs:
                continue
            frequency_vals.append(FF[frequency])
        frequency_vals = np.array(frequency_vals)
        sensitivities.append(np.sum(frequency_vals ** 2) / total)

    return sensitivities


def efast_freq(num_params, M=DEFAULT_M):
    from pyfast.parameters import MIN_RUNS_CUKIER75
    import numpy as np

    omega = np.zeros(num_params)
    nsamples = MIN_RUNS_CUKIER75[num_params]
    omega[0] = np.floor((nsamples - 1) / (2 * M))
    m = int(np.floor(omega[0] / (2 * M)))
    if m >= num_params - 1:
        omega[1:] = np.linspace(1, m, num_params - 1)
    else:
        omega[1:] = [(i % num_params) + 1 for i in xrange(0, num_params - 1)]

    curr_omega = np.zeros(num_params)
    frequencies = []
    for i in xrange(0, num_params):
        # Setup current omega values for i
        for j in xrange(0, num_params):
            if j == i:
                curr_omega[j] = omega[0]
            elif j > i:
                curr_omega[j] = omega[1 + j - 1]
            else:
                curr_omega[j] = omega[1 + j]
        frequencies.append(list(curr_omega))

    return frequencies


def efast_first_order(model, omega, M=DEFAULT_M):
    import numpy as np
    FF = np.fft.fft(model)
    num_samples = len(model)
    Lambdasqrd = np.power(np.absolute(FF[range(1, int(num_samples / 2))])
                          / num_samples, 2)
    V = 2 * np.sum(Lambdasqrd)
    D1 = 2 * np.sum(Lambdasqrd[list(np.arange(1, M) * int(omega) - 1)])

    return D1 / V


def efast_total_order(model, omega, M=DEFAULT_M):
    import numpy as np
    FF = np.fft.fft(model)
    num_samples = len(model)
    Lambdasqrd = np.power(np.absolute(FF[range(1, int(num_samples / 2))])
                          / num_samples, 2)
    V = 2 * np.sum(Lambdasqrd)
    Dt = 2 * sum(Lambdasqrd[range(int(omega / 2))])


    return (1 - Dt / V)
