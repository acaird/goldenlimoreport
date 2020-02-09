from bs4 import BeautifulSoup
from pprint import pprint
from tabulate import tabulate
import argparse
import logging
import os
import sys

LOG_FORMAT = "%(levelname)s: %(asctime)s %(message)s"
logging.basicConfig(format=LOG_FORMAT, level=os.environ.get("LOGLEVEL", "INFO"))


def process_GridViewExport(fname, fields):
    """Parse the HTML from the "xls" file into a dict of lists

    Parameters
    ----------

    fname: (str) full path, including filename, to the downloaded file
    from https://goldenlimo.liverycoach.com

    fields: (list(str)) list of columns from the input to include in
    the output; assuming this never changes, the default list is nice;
    it will probably change and then you'll have to look at the file
    to see what the choices are

    Returns
    -------

    A dictionary with the keys from the list in `fields` and each key
    being an ordered list of the values for that key

    """
    try:
        with open(fname, "rb") as f:
            data = f.read()
    except FileNotFoundError:
        logging.fatal(f"Couldn't find the file \"{fname}\"")
        sys.exit(1)

    soup = BeautifulSoup(data, "html.parser")

    table_rows = soup.find_all("tr")

    # 0th row has to be headings
    headings = table_rows[0].find_all("th")
    if len(headings) < 1:
        logging.fatal("No table headings, can't process the data")
        sys.exit(1)

    headings = [h.text for h in headings]

    logging.debug("HEADINGS: {}".format(", ".join(headings)))
    # the other rows are trip information
    data_rows = []
    for r in range(1, len(table_rows)):
        row = [td.text for td in table_rows[r].find_all("td")]
        logging.debug("Row {}: {}".format(r, ", ".join(row)))
        data_rows.append(row)

    d = {}
    for item, k in enumerate(headings):
        if k not in fields:
            continue
        d[k] = []
        for dr in data_rows:
            d[k].append(dr[item].strip())

    logging.debug(d)
    return d


if __name__ == "__main__":
    """Print a table of hired car trip information

    Based on the command-line options (or their defaults) read a file
    downloaded from https://goldenlimo.liverycoach.com/ and produce a
    text-based tabular version of it with only the fields of interest
    """

    parser = argparse.ArgumentParser(
        description="Process the downloaded Golden Limo XLS file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--filename",
        "-f",
        default="/Users/acaird/Downloads/GridViewExport.xls",
        help="path to the GridViewExport.xls file",
    )
    parser.add_argument(
        "--headings",
        nargs="+",
        help=(
            "Ordered list of headings parsed from the input and included "
            "in the output, should be space-separated and headings with "
            "spaces in them should be enclosed in quotes"
        ),
        default=[
            "Pickup Date",
            "Pickup Location",
            "Dropoff Location",
            "Passenger List",
            "Trip ID",
        ],
    )
    parser.add_argument(
        "--output",
        "-o",
        help=(
            "Output format, good choices are plain, grid, fancy_grid, "
            "github, orgtbl, rst, and html"
        ),
        default="orgtbl",
    )

    args = parser.parse_args()

    rows = process_GridViewExport(args.filename, args.headings)

    table = []
    table.append(args.headings)
    # flip the dict of lists into lists of lists for tabulate
    for r in range(len(rows[args.headings[0]])):
        table.append([rows[k][r] for k in args.headings])

    print(tabulate(table[1:], tablefmt=args.output, headers=args.headings))
