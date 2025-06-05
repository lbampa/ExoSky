import itertools
import random

import numpy as np
import pygame
from numpy.typing import NDArray
from pydantic import BaseModel

from exosky._data.constellation_schemas import read_constellations
from exosky.components import Component
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


class StarScreenProjection(BaseModel):
    x: int
    y: int
    z: float
    data: Star


class SkyComponent(Component):
    surface: pygame.Surface = pygame.Surface((1920, 1080))
    stars_data: list[Star] = []
    stars_coords: NDArray[np.float64] = np.array([])
    camera: CameraState = CameraState()
    constellation_colors: dict[str, tuple[int, int, int]] = {}
    _need_redraw: bool = True
    constellation_lines: dict[str, list[tuple[str, str]]] = {}
    star_connections: dict[str, list[str]] = {}

    def model_post_init(self, _):
        self.stars_coords = np.array([[s.x, s.y, s.z] for s in self.stars_data])
        constellation_names = {star.constellation for star in self.stars_data}
        self.constellation_colors = {
            constellation: (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            for constellation in constellation_names
        }
        self.constellation_colors["Sol"] = (255, 255, 255)
        self.constellation_colors["Orion"] = (255, 0, 0)
        self.constellation_colors["Ursa Major"] = (0, 255, 255)

        constellations = read_constellations()
        self.constellation_lines = {name: list() for name in constellations}
        star_names = itertools.chain.from_iterable(c.stars for c in constellations.values())
        self.star_connections = {name: list() for name in star_names}
        for name, constellation in constellations.items():
            for line in constellation.lines:
                self.constellation_lines[name].extend(itertools.pairwise(line))
                for first, second in itertools.pairwise(line):
                    self.star_connections[first].append(second)
                    self.star_connections[second].append(first)

    def update_camera(self, state: AppState):
        mouse = state.ui_state.mouse
        new_rotation = Rotation()
        if mouse.is_dragging():
            # this should be improved so that the same camera ray always stays under the cursor.
            # this will give a beter feel, like you're actually dragging the universe around you
            new_rotation.pitch -= mouse.position_delta[1] * 0.3
            new_rotation.yaw += mouse.position_delta[0] * 0.3

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
                    self._need_redraw = True
                case pygame.K_t:
                    self.camera.transform.translation = Translation.from_array(self.stars_coords[1])
                case _:
                    pass
        if any(v != 0 for v in [new_rotation.yaw, new_rotation.pitch, new_rotation.roll]):
            self._need_redraw = True
            R = self.camera.transform.rotation.__array__()
            delta_R = new_rotation.__array__()
            self.camera.transform.rotation = Rotation.from_matrix(R @ delta_R.T)

    def update(self, state: AppState, time_delta: float):
        self.update_camera(state)

    def _refresh(self):
        self.surface.fill((0, 0, 0))
        coords_from_camera = self.camera.transform.apply_inverse(self.stars_coords)
        width, height = self.surface.get_size()
        scren_center = np.array([width // 2, height // 2], dtype=np.int32)
        _z = coords_from_camera[:, 2]
        z_safe = np.where(_z == 0, 1e-6, np.abs(_z))
        screen_projection = (coords_from_camera[:, :2] * self.camera.field_of_view / z_safe[:, np.newaxis]).astype(
            np.int32
        ) + scren_center
        stars_projection = {
            star.name: (x, y, z)
            for (x, y), z, star in zip(screen_projection, coords_from_camera[:, 2], self.stars_data)
        }
        for (x, y), z, star in zip(screen_projection, coords_from_camera[:, 2], self.stars_data):
            color = self.constellation_colors[star.constellation]
            # skip if star is behind the camera, or outside the screen
            if z >= 0 or not 0 <= x <= self.surface.width or not 0 <= y <= self.surface.height:
                continue
            # draw star

            pygame.draw.circle(self.surface, color, (x, y), 2)
            # draw the lines
            for other_star in self.star_connections[star.name]:
                if other_star not in stars_projection:
                    continue
                other_x, other_y, *_ = stars_projection[other_star]
                pygame.draw.line(self.surface, color, (x, y), (other_x, other_y))

    def draw(self, state: AppState, surface: pygame.Surface):
        if self._need_redraw:
            self._refresh()
            self._need_redraw = False
        surface.blit(self.surface, self.surface.get_rect())
