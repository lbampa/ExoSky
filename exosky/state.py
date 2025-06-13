from collections import defaultdict
from typing import Iterable

import pygame
from pydantic import BaseModel, Field

from exosky._data.simbad import StarData
from exosky.transform import Transform

KeyCode = int
MouseButton = int


class CameraState(BaseModel):
    field_of_view: float = -720
    distance_to_focal_point: float = 0.0000001
    transform: Transform = Transform()


class KeyboardState(BaseModel):
    pressed_keys: defaultdict[KeyCode, bool] = Field(default_factory=lambda: defaultdict(lambda: False))

    def active_keys(self) -> Iterable[KeyCode]:
        return (key for key, status in self.pressed_keys.items() if status)

    def set_key(self, key: KeyCode) -> None:
        self.pressed_keys[key] = True

    def reset_key(self, key: KeyCode) -> None:
        self.pressed_keys.pop(key, False)


class MouseState(BaseModel):
    pressed_buttons: defaultdict[MouseButton, bool] = Field(default_factory=lambda: defaultdict(lambda: False))
    position: tuple[int, int] = (0, 0)
    position_delta: tuple[int, int] = (0, 0)

    def is_dragging(self) -> bool:
        return self.pressed_buttons[pygame.BUTTON_LEFT] and self.position_delta != (0, 0)

    def set_button(self, button: MouseButton) -> None:
        self.pressed_buttons[button] = True

    def reset_button(self, button: MouseButton) -> None:
        self.pressed_buttons.pop(button, False)

    def active_buttons(self) -> Iterable[MouseButton]:
        return (button for button, status in self.pressed_buttons.items() if status)

    def update_position(self, new_position: tuple[int, int]) -> None:
        new_x, new_y = new_position
        cur_x, cur_y = self.position
        self.position_delta = (new_x - cur_x, new_y - cur_y)
        self.position = new_position


class UIState(BaseModel):
    keyboard: KeyboardState = KeyboardState()
    mouse: MouseState = MouseState()
    enabled: bool = True
    need_update: bool = True
    star_data: StarData | None = None


class AppState(BaseModel):
    ui_state: UIState = UIState()
