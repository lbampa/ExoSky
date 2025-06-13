import itertools
from typing import Iterable, Self

import polars

from exosky._data.constellation_schemas import Constellation
from .component import Component
from exosky._data.simbad import StarData
from numpy.typing import NDArray
import numpy as np

from functools import cached_property


class StarDataComponent(Component):
    polar_data: dict[str, StarData] = {}
    constellations: dict[str, Constellation] = {}

    @cached_property
    def cartesian_coords(self) -> NDArray[np.float64]:
        coords = np.array([star.cartesian_coord for star in self.polar_data.values()], dtype=np.float64)
        return coords

    @cached_property
    def star_index(self) -> dict[str, int]:
        return {key: index for index, key in enumerate(self.polar_data.keys())}

    def star_cartesian_coords(self, star_name: str) -> NDArray[np.float64]:
        if star_name not in self.polar_data:
            raise KeyError(f"Star {star_name} not found in the stars data")
        index = self.star_index[star_name]
        return self.cartesian_coords[index]

    def invalidate_caches(self) -> None:
        for name, attr in self.__class__.__dict__.items():
            if isinstance(attr, cached_property) and name in self.__dict__:
                del self.__dict__[name]

    def add_stars(self, data: StarData | Iterable[StarData]) -> None:
        if isinstance(data, StarData):
            self.polar_data[data.name] = data
        else:
            for star in data:
                self.polar_data[star.name] = star
        self.invalidate_caches()

    @classmethod
    def from_csv(cls: type[Self], filename: str) -> Self:
        df = polars.read_csv(filename)
        df = df.filter(polars.col("Distance_ly").is_not_nan())
        stars = [StarData(**row) for row in df.to_dicts()]
        star_data_component = cls()
        star_data_component.add_stars(stars)
        return star_data_component

    def get_star(self, star_name: str) -> StarData | None:
        return self.polar_data.get(star_name)

    @cached_property
    def star_connections(self) -> dict[str, list[str]]:
        connections: dict[str, list[str]] = {name: list() for name in self.polar_data}
        for constellation in self.constellations.values():
            for line in constellation.lines:
                for first, second in itertools.pairwise(line):
                    if first in connections:
                        connections[first].append(second)
                    if second in connections:
                        connections[second].append(first)

        return connections
