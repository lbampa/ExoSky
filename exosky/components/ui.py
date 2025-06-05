from dataclasses import dataclass
from functools import cached_property
from typing import Any, Protocol

import pygame
import pygame_gui
from .component import Component, Events
from exosky.state import AppState
from pygame_gui.elements import UIPanel, UILabel

DEFAULT_THEME = "themes/default.json"
DEFAULT_FONT = "default"


class FontHelperProtocol(Protocol):
    def size(self, text: str) -> tuple[int, int]: ...


@dataclass
class UIHelper:
    manager: pygame_gui.UIManager

    def get_font(self, font: str | None = None) -> FontHelperProtocol:
        fonts = [f for f in (font, DEFAULT_FONT) if f]
        return self.manager.get_theme().get_font(fonts)

    def get_text_size(self, text: str, font: FontHelperProtocol | str | None = None):
        if font is None or isinstance(font, str):
            return self.get_font(font).size(text)
        return font.size(text)


@dataclass
class Layout:
    tab_panel: UIPanel

    @staticmethod
    def initialize(manager: pygame_gui.UIManager) -> "Layout":
        return Layout(tab_panel=Layout._tab_panel(manager))

    @staticmethod
    def _tab_panel(manager: pygame_gui.UIManager) -> UIPanel:
        text = "Pulsa Tab para mostrar interfaz"
        text_padding = 8
        text_width, text_height = UIHelper(manager).get_text_size(text)
        panel_rect = pygame.Rect(0, 0, text_width + text_padding * 2, text_height + text_padding * 2)
        panel_rect.topright = (-20, 20)
        panel = UIPanel(
            relative_rect=panel_rect,
            manager=manager,
            object_id="#transparent_panel",
            anchors={"top": "top", "right": "right"},
        )
        # Override panel background to fully transparent and rebuild
        panel.background_colour = pygame.Color(0, 0, 0, 128)
        panel.rebuild()

        _ = UILabel(
            relative_rect=pygame.Rect(text_padding, text_padding, text_width, text_height),
            text=text,
            manager=manager,
            object_id="label",
            container=panel,
        )
        return panel


class UIComponent(Component):
    surface: pygame.Surface
    manager: pygame_gui.UIManager

    def model_post_init(self, context: Any) -> None:
        _ = self.layout
        return super().model_post_init(context)

    @cached_property  # cache the result and return it without executing again
    def layout(self) -> Layout:
        return Layout.initialize(self.manager)

    def process_events(self, state: AppState, events: Events) -> AppState:
        for event in events:
            self.manager.process_events(event)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                state.ui_state.enabled = not state.ui_state.enabled
        return super().process_events(state, events)

    def update(self, state: AppState, time_delta: float):
        if not state.ui_state.enabled:
            self.layout.tab_panel.hide()
        else:
            self.layout.tab_panel.show()
            # self.layout.tab_panel.rebuild()

        self.manager.update(time_delta)
        return super().update(state, time_delta)

    def draw(self, state: AppState, surface: pygame.Surface):
        self.surface.fill((0, 0, 0, 0))
        self.manager.draw_ui(self.surface)
        surface.blit(self.surface, surface.get_rect())


def UIComponentFactory(surface_size: tuple[int, int], theme: str = DEFAULT_THEME) -> UIComponent:
    ui_surface = pygame.Surface(surface_size, pygame.SRCALPHA).convert_alpha()
    manager = pygame_gui.UIManager(surface_size, theme_path=theme)
    return UIComponent(surface=ui_surface, manager=manager)
