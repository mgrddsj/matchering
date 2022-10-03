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
from pedalboard.io import ReadableAudioFile

from .log import Code, warning, info, debug, ModuleError
from . import Config
from .dsp import size, is_mono, is_stereo, mono_to_stereo, count_max_peaks
from .utils import time_str


def __check_sample_rate(
    file: ReadableAudioFile,
    required_sample_rate: int,
    name: str,
    log_handler,
    log_code: Code,
) -> tuple[np.ndarray, int]:
    
    if file.samplerate != required_sample_rate:
        debug(
            f"Resampling {name} audio from {file.samplerate} Hz to {required_sample_rate} Hz..."
        )
        re_file = file.resampled_to(required_sample_rate)
        log_handler(log_code)
        array = re_file.read(re_file.frames)
        re_file.close()
    else:
        array = file.read(file.frames)

    return np.rot90(array,k=1,axes=(1,0)), required_sample_rate


def __check_length(
    file: ReadableAudioFile,
    max_length: int,
    min_length: float,
    name: str,
    error_code_max: Code,
    error_code_min: Code,
) -> None:
    length = file.duration
    debug(f"{name} audio length: {time_str(length)}")
    if length > max_length and name == "TARGET":
        raise ModuleError(error_code_max)
    elif length < min_length:
        raise ModuleError(error_code_min)


def __check_channels(
    array: np.ndarray, info_code_mono: Code, error_code_not_stereo: Code
) -> np.ndarray:
    if is_mono(array):
        info(info_code_mono)
        array = mono_to_stereo(array)
    elif not is_stereo(array):
        raise ModuleError(error_code_not_stereo)
    return array


def __check_clipping_limiting(
    array: np.ndarray,
    clipping_samples_threshold: int,
    limited_samples_threshold: int,
    warning_code_clipping: Code,
    warning_code_limiting: Code,
) -> None:
    max_value, max_count = count_max_peaks(array)
    if max_count > clipping_samples_threshold:
        if np.isclose(max_value, 1.0):
            warning(warning_code_clipping)
        elif max_count > limited_samples_threshold:
            warning(warning_code_limiting)


def check(
    file: ReadableAudioFile, config: Config, name: str
) -> (np.ndarray, int):
    name = name.upper()

    __check_length(
        file,
        config.max_length,
        config.fft_size  / file.samplerate,
        name,
        Code.ERROR_TARGET_LENGTH_IS_EXCEEDED
        if name == "TARGET"
        else Code.ERROR_REFERENCE_LENGTH_LENGTH_IS_EXCEEDED,
        Code.ERROR_TARGET_LENGTH_IS_TOO_SMALL
        if name == "TARGET"
        else Code.ERROR_REFERENCE_LENGTH_LENGTH_TOO_SMALL,
    )

    
    array, sample_rate = __check_sample_rate(
        file,
        config.internal_sample_rate,
        name,
        warning if name == "TARGET" else info,
        Code.WARNING_TARGET_IS_RESAMPLED
        if name == "TARGET"
        else Code.INFO_REFERENCE_IS_RESAMPLED,
    )

    array = __check_channels(
        array,
        Code.INFO_TARGET_IS_MONO if name == "TARGET" else Code.INFO_REFERENCE_IS_MONO,
        Code.ERROR_TARGET_NUM_OF_CHANNELS_IS_EXCEEDED
        if name == "TARGET"
        else Code.ERROR_REFERENCE_NUM_OF_CHANNELS_IS_EXCEEDED,
    )


    if name == "TARGET":
        __check_clipping_limiting(
            array,
            config.clipping_samples_threshold,
            config.limited_samples_threshold,
            Code.WARNING_TARGET_IS_CLIPPING,
            Code.WARNING_TARGET_LIMITER_IS_APPLIED,
        )

    return array, sample_rate


def check_equality(target: np.ndarray, reference: np.ndarray) -> None:
    if target.shape == reference.shape and np.allclose(target, reference):
        raise ModuleError(Code.ERROR_TARGET_EQUALS_REFERENCE)
