import numpy as np

def rotate(points, angle_x: float, angle_y: float, angle_z: float):
    """
    Rotate points in 3D space using Euler angles.
    :param points: np.array of shape (n, 3)
    :param angle_x: rotation angle around x-axis in radians
    :param angle_y: rotation angle around y-axis in radians
    :param angle_z: rotation angle around z-axis in radians
    :return: rotated points
    """
    rotation_matrix = euler_to_rotation_matrix(angle_x, angle_y, angle_z)
    return points @ rotation_matrix


def rotation_x(theta):
    return np.array([
        [1, 0, 0],
        [0, np.cos(theta), -np.sin(theta)],
        [0, np.sin(theta), np.cos(theta)]
    ])


def rotation_y(theta):
    return np.array([
        [np.cos(theta), 0, np.sin(theta)],
        [0, 1, 0],
        [-np.sin(theta), 0, np.cos(theta)]
    ])


def rotation_z(theta):
    return np.array([
        [np.cos(theta), -np.sin(theta), 0],
        [np.sin(theta), np.cos(theta), 0],
        [0, 0, 1]
    ])


def project(points, angle_x: float, angle_y: float, angle_z: float, zoom = 1):
    rotation_matrix = euler_to_rotation_matrix(angle_x, angle_y, angle_z)
    rotated_points = points @ rotation_matrix
    rotated_points *= zoom
    return rotated_points


def euler_to_rotation_matrix(theta_x, theta_y, theta_z):
    # Matrices de rotación individuales
    R_x = rotation_x(theta_x)
    R_y = rotation_y(theta_y)
    R_z = rotation_z(theta_z)

    # Multiplicar las matrices de rotación en el orden Z * Y * X
    return R_z @ R_y @ R_x
