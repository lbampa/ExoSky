import math

import numpy as np
import pytest
from numpy.typing import NDArray

from exosky.transform import Rotation, Transform, Translation


def test_translation_ndarray_arithmetic():
    t = Translation(x=1, y=2, z=3)
    a = np.array([4, 5, 6])
    expected_result = np.array([5, 7, 9])
    result = a + t
    assert np.all(result == expected_result)


VX = np.array([1, 0, 0])
VY = np.array([0, 1, 0])
VZ = np.array([0, 0, 1])

DEG_90 = math.pi / 2

ROT_NULL = Rotation(yaw=0, pitch=0, roll=0)
ROT_YAW_90 = Rotation(yaw=DEG_90, pitch=0, roll=0)
ROT_PITCH_90 = Rotation(yaw=0, pitch=DEG_90, roll=0)
ROT_ROLL_90 = Rotation(yaw=0, pitch=0, roll=DEG_90)
ROT_YAW_90_PITCH_90 = Rotation(yaw=DEG_90, pitch=DEG_90, roll=0)
ROT_YAW_90_ROLL_90 = Rotation(yaw=DEG_90, pitch=0, roll=DEG_90)
ROT_PITCH_90_ROLL_90 = Rotation(yaw=0, pitch=DEG_90, roll=DEG_90)


@pytest.mark.parametrize(
    "vector, rotation, expected_result",
    [
        pytest.param(VX, ROT_NULL, VX, id="vx @ null = vx"),
        pytest.param(VY, ROT_NULL, VY, id="vy @ null = vy"),
        pytest.param(VZ, ROT_NULL, VZ, id="vz @ null = vz"),
        pytest.param(VX, ROT_YAW_90, -VZ, id="vx @ yaw90 = -vz"),
        pytest.param(VY, ROT_YAW_90, VY, id="vy @ yaw90 = vy"),
        pytest.param(VZ, ROT_YAW_90, VX, id="vz @ yaw90 = vx"),
        pytest.param(VX, ROT_PITCH_90, VX, id="vx @ pitch90 = vx"),
        pytest.param(VY, ROT_PITCH_90, VZ, id="vy @ pitch90 = vz"),
        pytest.param(VZ, ROT_PITCH_90, -VY, id="vz @ pitch90 = -vy"),
        pytest.param(VX, ROT_ROLL_90, VY, id="vx @ roll90 = vy"),
        pytest.param(VY, ROT_ROLL_90, -VX, id="vy @ roll90 = -vx"),
        pytest.param(VZ, ROT_ROLL_90, VZ, id="vz @ roll90 = vz"),
        pytest.param(VX, ROT_YAW_90_PITCH_90, VY, id="vx @ yaw90pitch90 = vy"),
        pytest.param(VY, ROT_YAW_90_PITCH_90, VZ, id="vy @ yaw90pitch90 = vz"),
        pytest.param(VZ, ROT_YAW_90_PITCH_90, VX, id="vz @ yaw90pitch90 = vx"),
        pytest.param(VX, ROT_YAW_90_ROLL_90, -VZ, id="vx @ yaw90roll90 = -vz"),
        pytest.param(VY, ROT_YAW_90_ROLL_90, -VX, id="vy @ yaw90roll90 = -vx"),
        pytest.param(VZ, ROT_YAW_90_ROLL_90, VY, id="vz @ yaw90roll90 = vy"),
        pytest.param(VX, ROT_PITCH_90_ROLL_90, VY, id="vx @ pitch90roll90 = vy"),
        pytest.param(VY, ROT_PITCH_90_ROLL_90, VZ, id="vy @ pitch90roll90 = vz"),
        pytest.param(VZ, ROT_PITCH_90_ROLL_90, VX, id="vz @ pitch90roll90 = vx"),
    ],
)
def test_rotation_multiplication(
    vector: NDArray[np.float64],
    rotation: Rotation,
    expected_result: NDArray[np.float64],
):
    result = rotation @ vector
    assert np.allclose(result, expected_result, rtol=1e-5, atol=1e-8)

@pytest.mark.parametrize(
    "rotation",
    [
        pytest.param(ROT_NULL, id="null rotation"),
        pytest.param(ROT_YAW_90, id="yaw90"),
        pytest.param(ROT_PITCH_90, id="pitch90"),
        pytest.param(ROT_ROLL_90, id="roll90"),
        pytest.param(ROT_YAW_90_PITCH_90, id="yaw90pitch90"),
        pytest.param(ROT_YAW_90_ROLL_90, id="yaw90roll90"),
        pytest.param(ROT_PITCH_90_ROLL_90, id="pitch90roll90"),

    ]
)
def test_rotation_from_matrix(rotation: Rotation):
    expected_R = rotation.__array__()
    result = Rotation.from_matrix(expected_R)
    R = result.__array__()
    assert np.allclose(R, expected_R, atol=1e-7)
    # assert math.isclose(result.yaw, rotation.yaw)
    # assert math.isclose(result.pitch, rotation.pitch)
    # assert math.isclose(result.roll, rotation.roll)


TRANSFORM_NULL = Transform()
TRANSFORM_SCALE = Transform(scaling=2)
TRANSFORM_TRANSLATE = Transform(translation=Translation.from_array(VY))
TRANSFORM_ROTATE = Transform(rotation=ROT_PITCH_90_ROLL_90)
TRANSFORM_MIXED = Transform(
    translation=Translation.from_array(VY), rotation=ROT_PITCH_90_ROLL_90, scaling=2
)
POINTS_BASE = np.array([VX, VY, VZ])


@pytest.mark.parametrize(
    "transform, points, expected_result",
    [
        pytest.param(TRANSFORM_NULL, VX, VX, id="null on vx"),
        pytest.param(TRANSFORM_SCALE, VX, 2 * VX, id="scale on vx"),
        pytest.param(TRANSFORM_TRANSLATE, VX, VX + VY, id="translate vx by vy"),
        pytest.param(TRANSFORM_ROTATE, VX, VY, id="rotate vx with pitch90roll90"),
        pytest.param(
            TRANSFORM_MIXED,
            VX,
            VY * 2 + VY,
            id="rotation, translation and scaling of vx",
        ),
        pytest.param(
            TRANSFORM_MIXED,
            POINTS_BASE,
            np.array([VY * 2 + VY, VZ * 2 + VY, VX * 2 + VY]),
            id="mixed transform of multiple points"
        ),
    ],
)
def test_transform(
    transform: Transform,
    points: NDArray[np.float64],
    expected_result: NDArray[np.float64],
):
    result = transform.apply(points)
    assert np.allclose(result, expected_result, rtol=1e-5, atol=1e-8)
    inverse_result = transform.apply_inverse(result)
    assert np.allclose(points, inverse_result, rtol=1e-5, atol=1e-8)
