from typing import Annotated

import numpy as np
import math

from pydantic import BaseModel, Field


class StarData(BaseModel):
    name: str
    constellation: str
    ra: Annotated[float, Field(alias="RA_deg")]  # in degrees
    dec: Annotated[float, Field(alias="Dec_deg")]  # in degrees
    mag: Annotated[float, Field(alias="magnitude")]
    distance: Annotated[float, Field(alias="Distance_ly")]  # in light years

    model_config = {"populate_by_name": True}

    def __hash__(self):
        return self.model_dump_json().__hash__()

    @property
    def cartesian_coord(self) -> tuple[float, float, float]:
        return (
            -self.distance * math.cos(np.deg2rad(self.dec)) * math.cos(np.deg2rad(self.ra)),
            -self.distance * math.cos(np.deg2rad(self.dec)) * math.sin(np.deg2rad(self.ra)),
            -self.distance * math.sin(np.deg2rad(self.dec)),
        )
