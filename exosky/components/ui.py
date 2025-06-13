from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Protocol, Self

import pygame
import pygame_gui
from pygame_gui.elements import UILabel, UIPanel

from exosky._data.simbad import StarData
from exosky.state import AppState

from .component import Component, Events
from .sky import SkyComponent

DEFAULT_THEME = "themes/default.json"
DEFAULT_FONT = "default"

ANCHOR_LEFT = {"left": "left"}
ANCHOR_RIGHT = {"right": "right"}
ANCHOR_TOP = {"top": "top"}
ANCHOR_BOTTOM = {"bottom": "bottom"}

UI_DEFAULT_ANCHORS = ANCHOR_LEFT | ANCHOR_TOP

MSG_TAB_TO_SHOW = "Pulsa Tab para mostrar interfaz"
MSG_TAB_TO_HIDE = "Pulsa Tab para ocultar interfaz"


class FontHelperProtocol(Protocol):
    def size(self, text: str) -> tuple[int, int]: ...


@dataclass
class UIHelper:
    manager: pygame_gui.UIManager = field(default_factory=lambda: pygame_gui.UIManager((1920, 1080), DEFAULT_THEME))

    def get_font(self, font: str | None = None) -> FontHelperProtocol:
        fonts = [f for f in (font, DEFAULT_FONT) if f]
        return self.manager.get_theme().get_font(fonts)

    def get_text_size(self, text: str, font: FontHelperProtocol | str | None = None):
        if font is None or isinstance(font, str):
            return self.get_font(font).size(text)
        return font.size(text)


@dataclass
class PanelBasedElement:
    panel: UIPanel
    margin: tuple[int, int]

    @property
    def size(self) -> tuple[int, int]:
        x, y = self.panel.relative_rect.size
        return int(x), int(y)

    @staticmethod
    def register_panel(
        manager: pygame_gui.UIManager,
        anchors: dict[str, str] = UI_DEFAULT_ANCHORS,
        container: UIPanel | None = None,
    ) -> UIPanel:
        panel = UIPanel(relative_rect=(0, 0, 0, 0), manager=manager, object_id="panel", container=container)
        panel.background_colour = pygame.Color(0x80, 0x80, 0x80, 0x66)
        panel.set_anchors(anchors)  # type: ignore

        return panel

    @classmethod
    def register(
        cls: type[Self],
        manager: pygame_gui.UIManager,
        anchors: dict[str, str] = UI_DEFAULT_ANCHORS,
        container: UIPanel | None = None,
    ) -> Self:
        panel = cls.register_panel(manager, anchors, container)
        return cls(panel=panel, margin=(20, 20))

    def resize(self, size: tuple[int, int]) -> None:
        self.panel.set_dimensions(size)
        self.panel.rebuild()
        margin_x, margin_y = self.margin
        relative_x = margin_x if "left" in self.panel.anchors else -(self.panel.relative_rect.width + margin_x)
        relative_y = margin_y if "top" in self.panel.anchors else -(self.panel.relative_rect.height + margin_y)
        self.panel.set_relative_position((relative_x, relative_y))
        self.panel.rebuild()

    def hide(self):
        self.panel.hide()

    def show(self):
        self.panel.show()


@dataclass
class ResizableMultiLabelPanel(PanelBasedElement):
    labels: dict[str, UILabel] = field(default_factory=dict[str, UILabel])
    text_padding: tuple[int, int] = field(default_factory=lambda: (8, 8))
    margin: tuple[int, int] = field(default_factory=lambda: (20, 20))

    def add_label(self, name: str, text: str = "") -> None:
        l_rect = pygame.Rect(0, 0, 0, 0)
        self.labels[name] = UILabel(
            relative_rect=l_rect, text=text, manager=self.panel.ui_manager, container=self.panel
        )

    def update_label(self, label_name: str, text: str) -> None:
        label = self.labels[label_name]
        font = label.font or UIHelper().get_font()
        text_width, text_height = font.size(text)
        label.set_text(text)
        label.set_dimensions((text_width, text_height))
        width = int(max(label.relative_rect.width for label in self.labels.values())) + self.text_padding[0] * 2
        height = int(sum(label.relative_rect.height for label in self.labels.values()) + self.text_padding[1] * 2)
        self.resize((width, height))

    def resize(self, size: tuple[int, int]):
        super().resize(size)
        left_padding, last_height = self.text_padding
        for label in self.labels.values():
            label.set_relative_position((left_padding, last_height))
            last_height += label.relative_rect.height
            label.rebuild()
        self.panel.rebuild()


@dataclass
class ResizableLabelPanel(ResizableMultiLabelPanel):
    @classmethod
    def register(
        cls: type[Self],
        manager: pygame_gui.UIManager,
        anchors: dict[str, str] = UI_DEFAULT_ANCHORS,
        container: UIPanel | None = None,
    ) -> Self:
        base = super().register(manager, anchors, container)
        base.add_label("label")
        return base

    def update_text(self, text: str):
        self.update_label("label", text)


@dataclass
class StarFieldsPanel(ResizableMultiLabelPanel):
    @classmethod
    def register(
        cls: type[Self],
        manager: pygame_gui.UIManager,
        anchors: dict[str, str] = UI_DEFAULT_ANCHORS,
        container: UIPanel | None = None,
    ) -> Self:
        panel = cls.register_panel(manager, anchors, container)
        base = cls(panel=panel)
        fields = ["constellation", "ra", "dec", "mag", "distance"]
        for label in fields:
            base.add_label(label)

        return base

    def update_data(self, star_data: StarData) -> None:
        self.update_label("constellation", f"Constellation: {star_data.constellation}")
        self.update_label("ra", f"Rect Ascension: {star_data.ra:.4f}")
        self.update_label("dec", f"Decline: {star_data.dec:.4f}")
        self.update_label("mag", f"Magnitude: {star_data.mag:.4f}")
        self.update_label("distance", f"Distance(light years): {star_data.distance:.2f}")


@dataclass
class TabPanel(ResizableLabelPanel):
    @classmethod
    def register(
        cls: type[Self],
        manager: pygame_gui.UIManager,
        anchors: dict[str, str] = ANCHOR_TOP | ANCHOR_RIGHT,
        container: UIPanel | None = None,
    ) -> Self:
        tab_panel = super().register(manager, anchors=anchors, container=container)
        tab_panel.update_text(MSG_TAB_TO_HIDE)
        return tab_panel


@dataclass
class StarInfoPanel(PanelBasedElement):
    title_panel: ResizableLabelPanel
    fields_panel: StarFieldsPanel

    @classmethod
    def register(
        cls: type[Self],
        manager: pygame_gui.UIManager,
        anchors: dict[str, str] = UI_DEFAULT_ANCHORS,
        container: UIPanel | None = None,
    ) -> Self:
        panel = cls.register_panel(manager, anchors, container)
        panel.set_anchors({"top": "top", "right": "right"})
        panel.background_colour = pygame.Color(0, 0, 0, 0)
        panel.border_colour = pygame.Color(0, 0, 0, 0)
        title_panel = ResizableLabelPanel.register(manager, container=panel)
        fields_panel = StarFieldsPanel.register(manager, container=panel)
        star_info_panel = cls(panel=panel, title_panel=title_panel, fields_panel=fields_panel, margin=(20, 50))
        return star_info_panel

    def update_data(self, star_data: StarData):
        self.title_panel.update_text(star_data.name)
        title_width, title_height = self.title_panel.size

        self.fields_panel.margin = (20, title_height + self.title_panel.margin[1])
        self.fields_panel.update_data(star_data)
        fields_width, fields_height = self.fields_panel.size
        panel_width = max(title_width, fields_width) + 20 * 2
        panel_height = title_height + fields_height + 20 * 2
        self.resize((panel_width, panel_height))


@dataclass
class Layout:
    tab_panel: TabPanel
    star_info_panel: StarInfoPanel

    @staticmethod
    def initialize(manager: pygame_gui.UIManager) -> "Layout":
        return Layout(
            tab_panel=TabPanel.register(manager),
            star_info_panel=StarInfoPanel.register(manager),
        )


class UIComponent(Component):
    surface: pygame.Surface
    manager: pygame_gui.UIManager
    sky: SkyComponent

    def model_post_init(self, context: Any) -> None:
        _ = self.layout
        return super().model_post_init(context)

    @cached_property  # cache the result and return it without executing again
    def layout(self) -> Layout:
        return Layout.initialize(self.manager)

    def process_events(self, state: AppState, events: Events) -> AppState:
        for event in events:
            self.manager.process_events(event)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    state.ui_state.enabled = not state.ui_state.enabled
                self.need_update = True
            elif event.type in [pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN]:
                self.need_update = True

        return super().process_events(state, events)

    def update(self, state: AppState, time_delta: float):
        if not self.need_update:
            return

        self.need_redraw = True
        if not state.ui_state.enabled:
            self.layout.tab_panel.update_text(MSG_TAB_TO_SHOW)
            self.layout.star_info_panel.hide()
        else:
            self.layout.tab_panel.update_text(MSG_TAB_TO_HIDE)
            self.layout.star_info_panel.show()

        star_data = state.ui_state.star_data = self.sky.screen_closest_star(state.ui_state.mouse.position)
        if star_data is not None:
            self.layout.star_info_panel.update_data(star_data)
            self.layout.star_info_panel.show()
        else:
            self.layout.star_info_panel.hide()

        if pygame.BUTTON_LEFT in state.ui_state.mouse.active_buttons() and star_data is not None:
            self.sky.move_to_star(star_data.name)

        self.manager.update(time_delta)
        self.need_update = False
        return super().update(state, time_delta)

    def redraw(self, state: AppState):
        if not self.need_redraw:
            return
        self.surface.fill((0, 0, 0, 0))
        star_data = state.ui_state.star_data
        if star_data:
            center = self.sky.screen_projections.get(star_data.name)
            if center is not None:
                pygame.draw.circle(self.surface, (255, 255, 255), center, 5, width=1)
        self.manager.draw_ui(self.surface)
        self.need_redraw = False

    def draw(self, state: AppState, surface: pygame.Surface):
        self.redraw(state)
        surface.blit(self.surface, surface.get_rect())


def UIComponentFactory(surface_size: tuple[int, int], sky: SkyComponent, theme: str = DEFAULT_THEME) -> UIComponent:
    ui_surface = pygame.Surface(surface_size, pygame.SRCALPHA).convert_alpha()
    manager = pygame_gui.UIManager(surface_size, theme_path=theme)
    return UIComponent(surface=ui_surface, sky=sky, manager=manager)
