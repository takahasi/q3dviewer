"""
Copyright 2024 Panasonic Advanced Technology Development Co.,Ltd. (Liu Yang)
Distributed under MIT license. See LICENSE for more information.
"""

from OpenGL.GL import *
import numpy as np


def set_uniform(shader, content, name):
    location = glGetUniformLocation(shader, name)
    if location == -1:
        raise ValueError(
            f"Uniform '{name}' not found in shader program {shader}.")

    if isinstance(content, int):
        glUniform1i(location, content)
    elif isinstance(content, float):
        glUniform1f(location, content)
    elif isinstance(content, np.ndarray):
        if content.ndim == 1:
            if content.shape[0] == 2:
                glUniform2f(location, *content)
            elif content.shape[0] == 3:
                glUniform3f(location, *content)
            else:
                raise ValueError(
                    f"Unsupported 1D array size: {content.shape}.")
        elif content.ndim == 2:
            if content.shape == (4, 4):
                glUniformMatrix4fv(location, 1, GL_FALSE,
                                   content.T.astype(np.float32))
            else:
                raise ValueError(
                    f"Unsupported 2D array size: {content.shape}.")
        else:
            raise ValueError(f"Unsupported array dimension: {content.ndim}.")
    else:
        raise TypeError(
            f"Unsupported type for uniform '{name}': {type(content)}.")


def frustum(left, right, bottom, top, near, far):
    # see https://www.khronos.org/registry/OpenGL-Refpages/gl2.1/xhtml/glFrustum.xml
    if near <= 0 or far <= 0 or near >= far or left == right or bottom == top:
        print("Invalid frustum parameters.")
        return None
    matrix = np.zeros((4, 4), dtype=np.float32)
    matrix[0, 0] = 2.0 * near / (right - left)
    matrix[0, 2] = (right + left) / (right - left)
    matrix[1, 1] = 2.0 * near / (top - bottom)
    matrix[1, 2] = (top + bottom) / (top - bottom)
    matrix[2, 2] = -(far + near) / (far - near)
    matrix[2, 3] = -2.0 * far * near / (far - near)
    matrix[3, 2] = -1.0
    return matrix
