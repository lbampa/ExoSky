import numpy
import polars
from polars.datatypes import DataTypeClass

stars_schema: dict[str, DataTypeClass] = {
    "x": polars.Float64,
    "y": polars.Float64,
    "z": polars.Float64,
    "magnitude": polars.Float64,
    "name": polars.Utf8,
    "constellation": polars.Utf8,
}


def read_data(filename: str) -> polars.DataFrame:
    """
    Read the data from a CSV file and return it as a pandas DataFrame.
    """
    df = polars.read_csv(filename)
    deg_to_rad = numpy.pi / 180
    df = df.filter(polars.col("Distance_ly").is_not_nan())
    df = df.with_columns(
        [
            (polars.col("RA_deg") * deg_to_rad).alias("RA_rad"),
            (polars.col("Dec_deg") * deg_to_rad).alias("Dec_rad"),
        ]
    )

    df = df.with_columns(
        [
            (-polars.col("Distance_ly") * polars.col("Dec_rad").cos() * polars.col("RA_rad").cos()).alias("x"),
            (-polars.col("Distance_ly") * polars.col("Dec_rad").cos() * polars.col("RA_rad").sin()).alias("y"),
            (-polars.col("Distance_ly") * polars.col("Dec_rad").sin()).alias("z"),
        ]
    )

    df = df.select(["x", "y", "z", "magnitude", "name", "constellation"])
    df2 = polars.DataFrame(df, stars_schema)
    return df2
