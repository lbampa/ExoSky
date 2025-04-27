import pandas
import numpy


def read_data(filename: str) -> pandas.DataFrame:
    """
    Read the data from a CSV file and return it as a pandas DataFrame.
    """
    df = pandas.read_csv(filename)

    # convert the RA and DEC columns to x, y, z coordinates
    # in the dataset, the columns are named "RA_deg" and "Dec_deg", and they are in degrees
    # also, the distance is "Distance_ly" in light years

    # convert the RA and DEC columns to radians
    df["RA_rad"] = numpy.radians(df["RA_deg"])
    df["Dec_rad"] = numpy.radians(df["Dec_deg"])

    # convert the RA and DEC columns to x, y, z coordinates
    df["x"] = df["Distance_ly"] * numpy.cos(df["Dec_rad"]) * numpy.cos(df["RA_rad"])
    df["y"] = df["Distance_ly"] * numpy.cos(df["Dec_rad"]) * numpy.sin(df["RA_rad"])
    df["z"] = df["Distance_ly"] * numpy.sin(df["Dec_rad"])

    # return only the columns we need: x, y, z, name, mag, constellation
    df = df[["x", "y", "z", "name", "mag", "constellation"]]

    return df

print(read_data("tests/official_constellation_figure_stars.csv").head())