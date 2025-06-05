from pydantic import BaseModel
import itertools
import json

DEFAULT_SOURCE = "data/iau_constellation_lines.json"


class Constellation(BaseModel):
    id: str
    names: list[dict[str, str]]
    lines: list[list[str]]
    IAU: str

    @property
    def name(self) -> str:
        if not self.names:
            return "unknown"
        return self.names[0].get("native", "unknown")

    @property
    def stars(self) -> set[str]:
        return set(star_id for star_id in itertools.chain.from_iterable(self.lines))
        # return set(name.replace("* ", "") for name in itertools.chain.from_iterable(self.lines))


class ConstellationSource(BaseModel):
    constellations: list[Constellation]


def read_constellations(filename: str = DEFAULT_SOURCE) -> dict[str, Constellation]:
    with open(filename, "r") as f:
        data = json.load(f)
        constellations = ConstellationSource(**data).constellations
        return {constellation.name: constellation for constellation in constellations}
