import pygame

from exosky.state import AppState

from .component import Component, Events


class MouseComponent(Component):
    def process_events(self, state: AppState, events: Events) -> AppState:
        mouse_state = state.ui_state.mouse
        mouse_state.position_delta = (0, 0)
        for event in events:
            match event.type:
                case pygame.MOUSEBUTTONDOWN:
                    button = int(event.button)
                    mouse_state.set_button(button)
                case pygame.MOUSEBUTTONUP:
                    button = int(event.button)
                    mouse_state.reset_button(button)
                case pygame.MOUSEMOTION:
                    mouse_state.update_position(pygame.mouse.get_pos())
                case _:
                    pass

        return super().process_events(state, events)


class KeyboardComponent(Component):
    def process_events(self, state: AppState, events: Events) -> AppState:
        keyboard = state.ui_state.keyboard
        for event in events:
            if event.type not in [pygame.KEYDOWN, pygame.KEYUP]:
                continue
            key = int(event.key)
            if event.type == pygame.KEYDOWN:
                keyboard.set_key(key)
            else:
                keyboard.reset_key(key)

        return super().process_events(state, events)
