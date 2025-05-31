import numpy as np
import pygame
from numpy.typing import NDArray
from pydantic import BaseModel

from exosky.components import Component

# from exosky.data import read_data
from exosky.state import AppState
from exosky.transform import Rotation, Transform, Translation

ROTATION_SPEED = 0.03


class CameraState(BaseModel):
    field_of_view: float = -720
    distance_to_focal_point: float = 0.0000001
    transform: Transform = Transform()


class Star(BaseModel):
    x: float
    y: float
    z: float
    magnitude: float
    name: str
    constellation: str


class SkyComponent(Component):
    surface: pygame.Surface = pygame.Surface((1920, 1080))
    stars_data: list[Star] = []
    stars_coords: NDArray[np.float64] = np.array([])
    camera: CameraState = CameraState()
    counter: int = 0

    def model_post_init(self, _):
        self.stars_coords = np.array([[s.x, s.y, s.z] for s in self.stars_data])

    def update_camera(self, state: AppState):
        mouse = state.ui_state.mouse
        new_rotation = Rotation()
        if mouse.dragging:
            # this should be improved so that the same camera ray always stays under the cursor.
            # this will give a beter feel, like you're actually dragging the universe around you
            new_rotation.pitch -= mouse.position_delta[1] * 0.03
            new_rotation.yaw += mouse.position_delta[0] * 0.03
            # self.camera.transform.rotation.yaw -= mouse.position_delta[0] * 0.1
            # self.camera.transform.rotation.pitch -= mouse.position_delta[1] * 0.1

        keyboard = state.ui_state.keyboard
        for key in keyboard.active_keys():
            match key:
                case pygame.K_q:
                    new_rotation.roll += ROTATION_SPEED
                case pygame.K_e:
                    new_rotation.roll -= ROTATION_SPEED
                case pygame.K_w:
                    new_rotation.pitch += ROTATION_SPEED
                case pygame.K_s:
                    new_rotation.pitch -= ROTATION_SPEED
                case pygame.K_a:
                    new_rotation.yaw += ROTATION_SPEED
                case pygame.K_d:
                    new_rotation.yaw -= ROTATION_SPEED
                case pygame.K_r:
                    self.camera.transform = Transform()
                case pygame.K_t:
                    self.camera.transform.translation = Translation.from_array(self.stars_coords[1])
                case _:
                    pass
        R = self.camera.transform.rotation.__array__()
        delta_R = new_rotation.__array__()
        self.camera.transform.rotation = Rotation.from_matrix(R @ delta_R.T)

    def update(self, state: AppState, time_delta: float):
        self.counter += 1
        if self.counter == 10:
            self.counter = 0
        self.update_camera(state)
        # if self.counter == 0:
        #     print(self.camera.transform)

    def draw(self, state: AppState, surface: pygame.Surface):
        # to be implemented
        self.surface.fill((0, 0, 0))
        projected_points = self.camera.transform.apply_inverse(self.stars_coords)
        for point, star in zip(projected_points, self.stars_data):
            # if the star is behind the camera, we don't draw it
            if point[2] >= 0:
                # if self.counter == 0:
                #     print(f"skipping star {star}")
                continue
            # make it bigger or smaller based on distance (to be improved)
            scale = self.camera.field_of_view / np.abs(point[2])
            width, height = surface.get_size()
            x = int(point[0] * scale) + width // 2  # Centrar en la pantalla
            y = int(point[1] * scale) + height // 2  # Invertir Y y centrar

            # Cambiar tamaño según la distancia (coordenada Z)
            distance_factor = 10 / (1 + point.dot(point)) ** 2
            # distance_factor = 0.002 / point.dot(point)

            # make distance_factor
            distance_factor = max(0.2, distance_factor)

            point_size = int(0.2 * distance_factor)  # Tamaño según distancia
            point_size = 1

            # Generar color de la estrella basado en la distancia
            constellation_colors = {
                "Ursa Major": (0, 255, 255),
                "Orion": (255, 0, 0),
                "Scorpius   ": (0, 255, 0),
                "Sol": (255, 255, 255),
            }

            star_color = constellation_colors[star.constellation]

            # Dibujar el punto con su color y tamaño
            # if self.counter == 0:
            #     print(f"plotting star {star.name} on display coords ({x}, {y})")
            pygame.draw.circle(surface, star_color, (x, y), point_size)
        # surface.blit(self.surface, (0, 0))
