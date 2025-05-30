from typing import Any

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel


class Translation(BaseModel):
    x: float = 0
    y: float = 0
    z: float = 0

    def __array__(self, dtype: Any | None = None) -> NDArray[np.float64]:
        return np.array([self.x, self.y, self.z])

    @staticmethod
    def from_array(array: NDArray[np.float64]) -> "Translation":
        return Translation(x=array[0], y=array[1], z=array[2])


class Rotation(BaseModel):
    yaw: float = 0
    pitch: float = 0
    roll: float = 0

    def __array__(self):
        cy = np.cos(self.yaw)
        sy = np.sin(self.yaw)
        cx = np.cos(self.pitch)
        sx = np.sin(self.pitch)
        cz = np.cos(self.roll)
        sz = np.sin(self.roll)

        return np.array(
            [
                [cz * cy - sz * sx * sy, -cx * sz, cz * sy + cy * sz * sx],
                [cy * sz + cz * sx * sy, cz * cx, sz * sy - cz * cy * sx],
                [-cx * sy, sx, cx * cy],
            ]
        )

    def inv(self) -> NDArray[np.float64]:
        return np.linalg.matrix_transpose(self.__array__())

    @staticmethod
    def from_matrix(R: NDArray[np.float64]) -> "Rotation":
        sx = R[2, 1]  # sin(pitch)
        pitch = np.arcsin(sx)

        cx = np.cos(pitch)
        eps = 1e-6

        if abs(cx) > eps:
            yaw = np.arctan2(-R[2, 0], R[2, 2])
            roll = np.arctan2(-R[0, 1], R[1, 1])
        else:
            # Gimbal lock: pitch = ±90°, yaw arbitrary
            yaw = np.arctan2(R[1, 0], R[0, 0])
            roll = 0.0

        return Rotation(yaw=yaw, pitch=pitch, roll=roll)


class Transform(BaseModel):
    translation: Translation = Translation()
    rotation: Rotation = Rotation()
    scaling: float = 1

    def apply(self, points: NDArray[np.float64]) -> NDArray[np.float64]:
        R = np.asarray(self.rotation)
        t = np.asarray(self.translation)

        if points.ndim == 1:
            return (R @ points) * self.scaling + t
        else:
            return points @ R.T * self.scaling + t
        # return (self.rotation @ points) * self.scaling + self.translation

    def apply_inverse(self, points: NDArray[np.float64]) -> NDArray[np.float64]:
        R = np.asarray(self.rotation)
        t = np.asarray(self.translation)
        if len(points) == 0:
            return points
        if points.ndim == 1:
            return R.T @ (points - t) / self.scaling
        else:
            return (points - t) @ R / self.scaling
        # return (self.rotation.inv() @ (points - self.translation)) / self.scaling
