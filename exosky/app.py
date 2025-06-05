import logging
import traceback

import pygame
from pydantic import BaseModel

from exosky.components import Component, KeyboardComponent, MouseComponent, SkyComponent, Star
from exosky.data import read_data
from exosky.state import AppState


class AppConfig(BaseModel):
    # default resolution: full-hd
    screen_width: int = 1920
    screen_height: int = 1080
    frame_rate: int = 60
    full_screen: bool = True

    @property
    def screen_size(self) -> tuple[int, int]:
        return self.screen_width, self.screen_height


class StopAppException(Exception):
    pass


class App:
    def __init__(self, config: AppConfig = AppConfig()):
        self.config = config
        self.clock = pygame.time.Clock()
        # df = read_data("tests/official_constellation_figure_stars.csv")
        df = read_data("data/simbad_constellation_stars.csv")
        stars = [Star(**row) for row in df.to_dicts()]
        self.components: list[Component] = [
            KeyboardComponent(),
            MouseComponent(),
            SkyComponent(stars_data=stars),
        ]
        self.state = AppState()
        self.surface: pygame.Surface

    def initialize(self):
        pygame.init()
        display_flags = 0  # | (pygame.FULLSCREEN if self.config.full_screen else 0)
        self.surface = pygame.display.set_mode(self.config.screen_size, display_flags)

    def run(self):
        try:
            self.initialize()
            while True:
                self.process_events()
                time_delta = self.clock.tick(self.config.frame_rate) / 1000
                self.update(time_delta)
                self.draw()
        except StopAppException:
            print("exit signal received from")
            print(traceback.format_exc())
        except Exception as e:
            print(f"unhandled exception {e}")
            print(traceback.format_exc())
        finally:
            self.shutdown()

    def process_events(self):
        events = pygame.event.get()
        if any(event.type == pygame.QUIT for event in events):
            raise StopAppException()
        for component in self.components:
            component.process_events(self.state, events)

    def update(self, time_delta: float):
        if pygame.K_ESCAPE in self.state.ui_state.keyboard.active_keys():
            raise StopAppException()
        for component in self.components:
            component.update(self.state, time_delta)

    def draw(self):
        self.surface.fill((0, 0, 0))
        for component in self.components:
            component.draw(self.state, self.surface)
        pygame.display.flip()

    def shutdown(self):
        pygame.display.quit()
        pygame.quit()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    App().run()
