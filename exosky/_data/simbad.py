import astropy.units as u
import polars
from astropy.coordinates import SkyCoord
from astroquery.simbad import Simbad
from pydantic import BaseModel

from .constellation_schemas import read_constellations


class SimbadStarData(BaseModel):
    name: str
    constellation: str
    ra: float
    dec: float
    mag: float
    distance: float


def get_simbad_data() -> list[SimbadStarData]:
    constellations = read_constellations()
    star_constellations = {
        star_name: constellation_name
        for constellation_name, constellation in constellations.items()
        for star_name in constellation.stars
    }

    all_star_names = list(star_constellations)

    Simbad.add_votable_fields("flux(V)", "ra", "dec")  # type: ignore
    simbad_results = Simbad.query_objects(all_star_names)

    coords = SkyCoord(ra=simbad_results["RA"], dec=simbad_results["DEC"], unit=(u.hourangle, u.deg))
    stars = [
        SimbadStarData(
            name=name,
            constellation=constellation,
            ra=coord.ra.deg,
            dec=coord.dec.deg,
            mag=mag,
        )
        for (name, constellation), mag, coord in zip(star_constellations.items(), simbad_results["FLUX_V"], coords)
    ]

    return stars


def save_constellation_stars() -> None:
    stars = get_simbad_data()
    df = polars.DataFrame([s.model_dump() for s in stars])
    df.write_csv("data/constellation_stars.csv")
