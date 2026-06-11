import csv
import math
import re
from importlib import resources
import color_conversions.data as data_files


### NCS
def ncs_to_rgb(ncs: str):
    """
    Convert an NCS color code to an RGB dictionary with keys 'r', 'g', and 'b'.

    Parameters
    ----------
    ncs : str
        The NCS color code to convert.

    Returns
    -------
    dict
        A dictionary with keys 'r', 'g', and 'b' representing the RGB values of the color.
        If the NCS color code is invalid, returns False.

    Notes
    -----
    The NCS color code should be in the format 'NCS XX-[N|Y|R|G|B]XX[Y|R|G|B]',
    where XX is a 2-digit number representing the black value and XXXX is a 4-digit
    number representing the chroma value. The optional [Y|R|G|B]XX[Y|R|G|B] part
    represents the black color and percentage, and is optional.
    The RGB values are normalized to the range 0-255.
    The function uses mathematical approximations to estimate RGB values.

    """
    ncs = ncs.strip().upper().replace("(", "").replace(")", "")
    ncs = re.sub(r"\s+", " ", ncs.replace("NCS", "NCS "))

    if "NCS" not in ncs:
        ncs = "NCS " + ncs

    match = re.match(r"^(?:NCS|NCS\sS)\s(\d{2})(\d{2})-(N|[A-Z])(\d{2})?([A-Z])?$", ncs)
    if not match:
        return False

    black = int(match[1])
    chroma = int(match[2])
    bc = match[3]
    percent = int(match[4]) if match[4] else 0

    if bc not in "NYRBG":
        return False

    if bc != "N":
        black1: float = 1.05 * black - 5.25
        chroma1: float = chroma
        red1: float = 0.0
        green1: float = 0.0
        blue1: float = 0.0
        factor1: float = 0.0

        if bc == "Y" and percent <= 60:
            red1 = 1
        elif (bc == "Y" and percent > 60) or (bc == "R" and percent <= 80):
            factor1 = percent - 60 if bc == "Y" else percent + 40
            red1 = (math.sqrt(14884 - factor1**2) - 22) / 100
        elif (bc == "R" and percent > 80) or (bc == "B"):
            red1 = 0
        elif bc == "G":
            factor1 = percent - 170
            red1 = (math.sqrt(33800 - factor1**2) - 70) / 100

        if bc == "Y" and percent <= 80:
            blue1 = 0
        elif (bc == "Y" and percent > 80) or (bc == "R" and percent <= 60):
            factor1 = (percent - 80) + 20.5 if bc == "Y" else (percent + 20) + 20.5
            blue1 = (104 - math.sqrt(11236 - factor1**2)) / 100
        elif (bc == "R" and percent > 60) or (bc == "B" and percent <= 80):
            factor1 = (percent - 60) - 60 if bc == "R" else (percent + 40) - 60
            blue1 = (math.sqrt(10000 - factor1**2) - 10) / 100
        elif (bc == "B" and percent > 80) or (bc == "G" and percent <= 40):
            factor1 = (percent - 80) - 131 if bc == "B" else (percent + 20) - 131
            blue1 = (122 - math.sqrt(19881 - factor1**2)) / 100
        elif bc == "G" and percent > 40:
            blue1 = 0

        if bc == "Y":
            green1 = (85 - 17 / 20 * percent) / 100
        elif bc == "R" and percent <= 60:
            green1 = 0
        elif bc == "R" and percent > 60:
            factor1 = (percent - 60) + 35
            green1 = (67.5 - math.sqrt(5776 - factor1**2)) / 100
        elif bc == "B" and percent <= 60:
            factor1 = percent - 68.5
            green1 = (6.5 + math.sqrt(7044.5 - factor1**2)) / 100
        elif (bc == "B" and percent > 60) or (bc == "G" and percent <= 60):
            green1 = 0.9
        elif bc == "G" and percent > 60:
            factor1 = percent - 60
            green1 = (90 - (1 / 8 * factor1)) / 100

        factor1 = (red1 + green1 + blue1) / 3
        red2 = ((factor1 - red1) * (100 - chroma1) / 100) + red1
        green2 = ((factor1 - green1) * (100 - chroma1) / 100) + green1
        blue2 = ((factor1 - blue1) * (100 - chroma1) / 100) + blue1

        max_val = max(red2, green2, blue2, (red2 + green2 + blue2) / 3)
        factor2 = 1 / max_val

        r = int((red2 * factor2 * (100 - black1) / 100) * 255)
        g = int((green2 * factor2 * (100 - black1) / 100) * 255)
        b = int((blue2 * factor2 * (100 - black1) / 100) * 255)

        r, g, b = min(255, max(0, r)), min(255, max(0, g)), min(255, max(0, b))
    else:
        grey = int((1 - black / 100) * 255)
        grey = min(255, max(0, grey))
        r = g = b = grey

    return {"r": r, "g": g, "b": b}


### RAL
def load_ral_colors():
    """
    Load RAL colors from a CSV file into a dictionary.

    This function reads the RAL color codes and their corresponding RGB values from a CSV file,
    normalizes the RGB values to a range of 0-1, and stores them in a dictionary.

    Returns
    -------
    dict
        A dictionary where the keys are RAL color codes (e.g., "RAL 1000") and the values are
        tuples containing the normalized RGB values.

    Notes
    -----
    The function expects the CSV file to have a header and to use semicolons as delimiters.
    RGB values are converted to a range of 0-1 for easier use in graphics and rendering.

    """
    ral_dict = {}
    with resources.files(data_files).joinpath("ral_rgb.csv").open("r", encoding="utf-8") as file:
        reader = csv.reader(file, delimiter=";")
        next(reader)  # Skip header
        for row in reader:
            ral_code = row[0].strip()  # Keep "RAL 1000" format
            rgb_values = tuple(
                int(v) / 255 for v in row[1].split("-")
            )  # Convert to range 0-1
            ral_dict[ral_code] = rgb_values
    return ral_dict


def ral_to_rgb(ral_code, ral_dict):
    """
    Convert RAL code to normalized RGB values (0-1 range).

    This function looks up the given RAL color code in the provided RAL dictionary and returns
    the corresponding normalized RGB values. If the RAL code is not found (None, None, None).

    Parameters
    ----------
    ral_code : str
        The RAL color code (e.g., "RAL 1000").

    ral_dict : dict
        The dictionary containing RAL codes as keys and normalized RGB values as values.

    Returns
    -------
    tuple
        A tuple containing the normalized RGB values (R, G, B) in the range 0-1. If the RAL
        code is not found, it returns (None, None, None).

    Notes
    -----
    The RAL code is normalized to ensure consistency with the dictionary, and the prefix "RAL "
    is added if not present in the input.

    """
    ral_code = ral_code.strip().upper()
    if not ral_code.startswith("RAL "):
        ral_code = f"RAL {ral_code}"  # Add prefix if missing

    return ral_dict.get(ral_code, (None, None, None))  # Ensure unpacking works


### ProfelColor
def load_profel_colors():
    """
    Load Profel color codes from a CSV file into a dictionary.

    This function reads the Profel color codes and their corresponding RGB values from a CSV file,
    normalizes the RGB values to a range of 0-1, and stores them in a dictionary.

    Returns
    -------
    dict
        A dictionary where the keys are Profel color codes and the values are tuples containing
        the normalized RGB values.

    Notes
    -----
    The function expects the CSV file to have a header and to use semicolons as delimiters.
    RGB values are converted to a range of 0-1 for easier use in graphics and rendering.

    """
    profel_dict = {}
    with resources.files(data_files).joinpath("profel_rgb.csv").open("r", encoding="utf-8") as file:
        reader = csv.reader(file, delimiter=";")
        next(reader)  # Skip header
        for row in reader:
            profel_code = row[0].strip()  # Keep original profile code format
            rgb_values = tuple(
                int(v) / 255 for v in row[1].split("-")
            )  # Normalize RGB (0-1)
            profel_dict[profel_code] = rgb_values
    return profel_dict


def profel_to_rgb(profel_code, profel_dict):
    """
    Convert Profile color code to normalized RGB values (0-1 range).

    This function looks up the given Profel color code in the provided Profel dictionary and returns
    the corresponding normalized RGB values. If the Profel code is not found (None, None, None).

    Parameters
    ----------
    profel_code : str
        The Profel color code.
    profel_dict : dict
        The dictionary containing Profel color codes as keys and normalized RGB values as values.

    Returns
    -------
    tuple
        A tuple containing the normalized RGB values (R, G, B) in the range 0-1. If the Profel code
        is not found, it returns (None, None, None).

    Notes
    -----
    The Profel code is normalized to ensure consistency with the dictionary.

    """
    profel_code = profel_code.strip().upper()  # Normalize input
    return profel_dict.get(profel_code, (None, None, None))  # Return RGB or None


### DB (Deutsche Bahn)
def load_db_colors():
    """
    Load DB (Deutsche Bahn) color codes from a CSV file into a dictionary.

    This function reads the DB color codes and their corresponding RGB values from a CSV file,
    normalizes the RGB values to a range of 0-1, and stores them in a dictionary.

    Returns
    -------
    dict
        A dictionary where the keys are DB color codes (e.g., "DB703") and the values are
        tuples containing the normalized RGB values.

    Notes
    -----
    The function expects the CSV file to have a header and to use semicolons as delimiters.
    RGB values are converted to a range of 0-1 for easier use in graphics and rendering.

    """
    db_dict = {}
    with resources.files(data_files).joinpath("db_rgb.csv").open("r", encoding="utf-8") as file:
        reader = csv.reader(file, delimiter=";")
        next(reader)  # Skip header
        for row in reader:
            db_code = row[0].strip()  # Keep format like "DB701"
            rgb_values = tuple(
                int(v) / 255 for v in row[1].split("-")
            )  # Convert to range 0-1
            db_dict[db_code] = rgb_values
    return db_dict


def db_to_rgb(db_code, db_dict):
    """
    Convert DB color code to normalized RGB values (0-1 range).

    This function looks up the given DB color code in the provided dictionary and returns
    the corresponding normalized RGB values. If the code is not found, returns (None, None, None).

    Parameters
    ----------
    db_code : str
        The DB color code (e.g., "DB701").
    db_dict : dict
        The dictionary containing DB codes as keys and normalized RGB values as values.

    Returns
    -------
    tuple
        A tuple containing the normalized RGB values (R, G, B) in the range 0-1. If the
        code is not found, it returns (None, None, None).

    """
    db_code = db_code.strip().upper()
    return db_dict.get(db_code, (None, None, None))


### BS (British Standard)
def load_bs_colors():
    """
    Load British Standard (BS) color codes from a CSV file into a dictionary.

    This function reads the BS color codes and their corresponding RGB values from a CSV file,
    normalizes the RGB values to a range of 0-1, and stores them in a dictionary.

    Returns
    -------
    dict
        A dictionary where the keys are BS color codes (e.g., "BS18B25") and the values are
        tuples containing the normalized RGB values.

    Notes
    -----
    The function expects the CSV file to have a header and to use semicolons as delimiters.
    RGB values are converted to a range of 0-1 for easier use in graphics and rendering.

    """
    bs_dict = {}
    with resources.files(data_files).joinpath("bs_rgb.csv").open("r", encoding="utf-8") as file:
        reader = csv.reader(file, delimiter=";")
        next(reader)  # Skip header
        for row in reader:
            bs_code = row[0].strip()  # Keep format like "BS18B25"
            rgb_values = tuple(
                int(v) / 255 for v in row[1].split("-")
            )  # Convert to range 0-1
            bs_dict[bs_code] = rgb_values
    return bs_dict


def bs_to_rgb(bs_code, bs_dict):
    """
    Convert British Standard (BS) code to normalized RGB values (0-1 range).

    This function looks up the given BS color code in the provided dictionary and returns
    the corresponding normalized RGB values.

    Parameters
    ----------
    bs_code : str
        The BS color code (e.g., "BS18B25").
    bs_dict : dict
        The dictionary containing BS codes as keys and normalized RGB values as values.

    Returns
    -------
    tuple
        A tuple containing the normalized RGB values (R, G, B) in the range 0-1. If the
        code is not found, it returns (None, None, None).

    """
    bs_code = bs_code.strip().upper()
    return bs_dict.get(bs_code, (None, None, None))


### Granit
def load_granit_colors():
    """
    Load Granit color codes from a CSV file into a dictionary.

    This function reads the Granit color codes and their corresponding RGB values from a CSV file,
    normalizes the RGB values to a range of 0-1, and stores them in a dictionary.

    Returns
    -------
    dict
        A dictionary where the keys are Granit color codes (e.g., "G01") and the values are
        tuples containing the normalized RGB values.

    Notes
    -----
    The function expects the CSV file to have a header and to use semicolons as delimiters.
    RGB values are converted to a range of 0-1 for easier use in graphics and rendering.

    """
    granit_dict = {}
    with resources.files(data_files).joinpath("granit_rgb.csv").open("r", encoding="utf-8") as file:
        reader = csv.reader(file, delimiter=";")
        next(reader)  # Skip header
        for row in reader:
            granit_code = row[0].strip()  # Keep format like "G01"
            rgb_values = tuple(
                int(v) / 255 for v in row[1].split("-")
            )  # Convert to range 0-1
            granit_dict[granit_code] = rgb_values
    return granit_dict


def granit_to_rgb(granit_code, granit_dict):
    """
    Convert Granit color code to normalized RGB values (0-1 range).

    This function looks up the given Granit color code in the provided dictionary and returns
    the corresponding normalized RGB values.

    Parameters
    ----------
    granit_code : str
        The Granit color code (e.g., "G01").
    granit_dict : dict
        The dictionary containing Granit codes as keys and normalized RGB values as values.

    Returns
    -------
    tuple
        A tuple containing the normalized RGB values (R, G, B) in the range 0-1. If the
        code is not found, it returns (None, None, None).

    """
    granit_code = granit_code.strip().upper()
    return granit_dict.get(granit_code, (None, None, None))
