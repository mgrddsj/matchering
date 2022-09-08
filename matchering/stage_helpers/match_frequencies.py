# -*- coding: utf-8 -*-

"""
Matchering - Audio Matching and Mastering Python Library
Copyright (C) 2016-2022 Sergree

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import numpy as np
from time import time
from scipy import signal, interpolate

from ..log import debug
from .. import Config
from ..dsp import ms_to_lr, smooth_lowess, butter_bandpass_filter
from ..utils import debugger_is_active

def __average_fft(
    loudest_pieces: np.ndarray, sample_rate: int, fft_size: int
) -> np.ndarray:
    *_, specs = signal.stft(
        loudest_pieces,
        sample_rate,
        window="boxcar",
        nperseg=fft_size,
        noverlap=0,
        boundary=None,
        padded=False,
    )
    return np.abs(specs).mean((0, 2))


def __smooth_exponentially(matching_fft: np.ndarray, config: Config) -> np.ndarray:
    
    grid_linear = (
        config.internal_sample_rate * 0.5 * np.linspace(0, 1, config.fft_size // 2 + 1)
    )

    grid_logarithmic = (
        config.internal_sample_rate
        * 0.5
        * np.logspace(
            np.log10(4 / config.fft_size),
            0,
            (config.fft_size // 2) * config.lin_log_oversampling + 1,
        )
    )

    interpolator = interpolate.interp1d(grid_linear, matching_fft, "cubic")
    matching_fft_log = interpolator(grid_logarithmic)

    matching_fft_log_filtered = smooth_lowess(
        matching_fft_log, config.lowess_frac, config.lowess_it, config.lowess_delta
    )

    interpolator = interpolate.interp1d(
        grid_logarithmic, matching_fft_log_filtered, "cubic", fill_value="extrapolate"
    )
    matching_fft_filtered = interpolator(grid_linear)

    matching_fft_filtered[0] = 0
    

    return matching_fft_filtered


def get_fir(
    target_loudest_pieces: np.ndarray,
    reference_loudest_pieces: np.ndarray,
    name: str,
    config: Config,
) -> np.ndarray:
    debug(f"Calculating the {name} FIR for the matching EQ...")

    target_average_fft = __average_fft(
        target_loudest_pieces, config.internal_sample_rate, config.fft_size
    )
    
    if config.reference_preset:
        reference_average_fft = np.load('ref_'+ name +'.npy')
    else:
        reference_average_fft = __average_fft(
            reference_loudest_pieces, config.internal_sample_rate, config.fft_size
        )
    # np.save('ref_'+ name +'.npy',reference_average_fft)

    fft_size = config.internal_sample_rate/2/len(reference_average_fft)
    
    target_peak = target_average_fft[:int(config.low_filter/fft_size)].argmax().min()
    reference_peak = reference_average_fft[:int(config.low_filter/fft_size)].argmax().min()

    if target_peak > reference_peak/1.5 and target_peak < reference_peak*1.5: # within +/- a perfect 5th
        # transpose in terms of FFT numpy
        peak_diff = target_peak - reference_peak
        if peak_diff < 0:
            reference_average_fft = np.delete(reference_average_fft,range(abs(peak_diff)))
            reference_average_fft = np.append(reference_average_fft, reference_average_fft[peak_diff:])
        if peak_diff > 0:
            reference_average_fft = reference_average_fft[:-peak_diff]
            reference_average_fft = np.insert(reference_average_fft,0,reference_average_fft[0:peak_diff])

    np.maximum(config.min_value, target_average_fft, out=target_average_fft)
    matching_fft = reference_average_fft / target_average_fft
    if name == "mid":
        # if the target is poor in low range, avoid boosting
        if target_average_fft.argmax().min() > config.low_filter/fft_size:
            for x in range(int(config.low_filter/fft_size)):
                if matching_fft[x] > 1:
                    matching_fft[x] = 1
        # high filter, taming filter for more natural character of music
        for x in range(int(config.high_filter/fft_size),len(matching_fft)):
            if matching_fft[x] > 1:
                matching_fft[x] = 0.5 * matching_fft[x]
    if name == "side":
        # low filter, avoid gaining low range => muddiness
        for x in range(int(max(config.low_filter/fft_size, target_average_fft.argmax().min()))):
            if matching_fft[x] > 1:
                matching_fft[x] = 1
        # high filter, taming filter for more natural character of music, leave out high freq air
        for x in range(int(config.high_filter/fft_size),int(len(matching_fft)/2)):
            if matching_fft[x] > 1:
                matching_fft[x] = 0.5 * matching_fft[x]

    matching_fft_filtered = __smooth_exponentially(matching_fft, config)

    fir = np.fft.irfft(matching_fft_filtered)
    fir = np.fft.ifftshift(fir) * signal.windows.hann(len(fir))

    import matplotlib.pyplot as plt
    if debugger_is_active():
        fig, (ax_orig,ax_ref, ax_mag) = plt.subplots(3, 1)
        ax_orig.plot(target_average_fft)
        ax_orig.set_xscale('log')
        ax_orig.set_title('original_fft')
        ax_ref.plot(reference_average_fft)
        ax_ref.set_xscale('log')
        ax_ref.set_title('ref_fft')
        ax_mag.plot(matching_fft_filtered)
        ax_mag.set_xscale('log')
        ax_mag.set_title('filter')
        fig.tight_layout()
    # if __debug__:
        fig.show()

    return fir


def convolve(
    target_mid: np.ndarray,
    mid_fir: np.ndarray,
    target_side: np.ndarray,
    side_fir: np.ndarray,
) -> (np.ndarray, np.ndarray):
    debug("Convolving the TARGET audio with calculated FIRs...")
    timer = time()
    result_mid = signal.fftconvolve(target_mid, mid_fir, "same")
    result_side = signal.fftconvolve(target_side, side_fir, "same")
    debug(f"The convolution is done in {time() - timer:.2f} seconds")

    debug("Converting MS to LR...")
    result = ms_to_lr(result_mid, result_side)

    return result, result_mid
