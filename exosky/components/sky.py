import random

import numpy as np
import pygame
from pydantic import BaseModel

from exosky._data.simbad import StarData
from exosky.state import AppState
from exosky.transform import Rotation, Transform, Translation

from .component import Component
from .star_data import StarDataComponent

ROTATION_SPEED = 0.03


def tuple_dist2(t1: tuple[int, int], t2: tuple[int, int]) -> float:
    return (t1[0] - t2[0]) ** 2 + (t1[1] - t2[1]) ** 2


class CameraState(BaseModel):
    field_of_view: float = -720
    distance_to_focal_point: float = 0.0000001
    transform: Transform = Transform()


class SkyComponent(Component):
    surface: pygame.Surface = pygame.Surface((1920, 1080))
    stars: StarDataComponent = StarDataComponent()
    camera: CameraState = CameraState()
    constellation_colors: dict[str, tuple[int, int, int]] = {}
    screen_projections: dict[str, tuple[int, int]] = {}

    def model_post_init(self, _):
        self.constellation_colors = {
            constellation: (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            for constellation in self.stars.constellations
        }
        self.constellation_colors["Sol"] = (255, 255, 255)

    def move_to_star(self, star_name: str) -> None:
        star = self.stars.get_star(star_name)
        if star is None:
            return
        self.camera.transform.translation = Translation.from_array(self.stars.star_cartesian_coords(star_name))
        self.need_redraw = True

    def update_camera(self, state: AppState):
        new_rotation = Rotation()

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
                    self.need_redraw = True
                case _:
                    pass
        if any(v != 0 for v in [new_rotation.yaw, new_rotation.pitch, new_rotation.roll]):
            self.need_redraw = True
            R = self.camera.transform.rotation.__array__()
            delta_R = new_rotation.__array__()
            self.camera.transform.rotation = Rotation.from_matrix(R @ delta_R.T)

    def update(self, state: AppState, time_delta: float):
        self.update_camera(state)

    def _refresh(self):
        self.surface.fill((0, 0, 0))
        if len(self.stars.cartesian_coords) == 0:
            return
        coords_from_camera = self.camera.transform.apply_inverse(self.stars.cartesian_coords)
        width, height = self.surface.get_size()
        scren_center = np.array([width // 2, height // 2], dtype=np.int32)
        _z = coords_from_camera[:, 2]
        z_safe = np.where(_z == 0, 1e-6, np.abs(_z))
        screen_projection = (coords_from_camera[:, :2] * self.camera.field_of_view / z_safe[:, np.newaxis]).astype(
            np.int32
        ) + scren_center
        stars_projection = {
            star: (x, y, z)
            for (x, y), z, star in zip(screen_projection, coords_from_camera[:, 2], self.stars.polar_data)
        }
        self.screen_projections.clear()
        for (x, y), z, (star, star_data) in zip(screen_projection, _z, self.stars.polar_data.items()):
            # skip if star is behind the camera, or outside the screen
            if z >= 0 or not 0 <= x <= self.surface.width or not 0 <= y <= self.surface.height:
                continue

            color = self.constellation_colors[star_data.constellation]
            self.screen_projections[star] = (x, y)
            # draw star
            radius = 2 if star != "Sol" else 4  # let's make our star bigger, so we can identify it more easily
            pygame.draw.circle(self.surface, color, (x, y), radius)

            # draw the lines
            for other_star in self.stars.star_connections[star]:
                if other_star not in stars_projection:
                    continue
                other_x, other_y, *_ = stars_projection[other_star]
                pygame.draw.line(self.surface, color, (x, y), (other_x, other_y))

    def draw(self, state: AppState, surface: pygame.Surface):
        if self.need_redraw:
            self._refresh()
            self.need_redraw = False
        surface.blit(self.surface, self.surface.get_rect())

    def screen_closest_star(self, position: tuple[int, int], max_distance: float = 25) -> StarData | None:
        proj = self.screen_projections
        if len(proj) == 0:
            return None
        star = min(proj, key=lambda star: tuple_dist2(self.screen_projections[star], position))
        return self.stars.polar_data[star] if tuple_dist2(proj[star], position) < max_distance**2 else None
