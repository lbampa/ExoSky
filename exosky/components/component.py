from typing import Iterable, Self

import pygame
from pydantic import BaseModel, ConfigDict

from exosky.state import AppState

Events = Iterable[pygame.event.Event]


class Component(BaseModel):
    children: list[Self] = []
    need_update: bool = True
    need_redraw: bool = True
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def process_events(self, state: AppState, events: Events) -> AppState:
        for child in self.children:
            state = child.process_events(state, events)
        return state

    def update(self, state: AppState, time_delta: float):
        for child in self.children:
            child.update(state, time_delta)

    def draw(self, state: AppState, surface: pygame.Surface):
        for child in self.children:
            child.draw(state, surface)

    def add(self, child: Self) -> None:
        self.children.append(child)
