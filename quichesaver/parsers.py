"""
Defines functions to parse store's htmls.

To work with the Product object, each parser must return a dictionary
with three keys:
    - name: the product's name
    - price: the product's best price
    - available: the product's availability

To create a new parser, simply define the function, and then add an entry
to the dict "parsers" at the end of the file.
"""

import re
import json

from bs4 import BeautifulSoup


def brl_converter(string):
    """Convert a BRL price (R$ XXX.XXX,XX) to a float."""
    return float(string.strip("R$ ").replace('.', '').replace(',', '.'))


def cea_parser(html):
    """
    Parser for cea.com.br.

    They have a Javascript code inside a <script> tag, with an object called
    skuJson_0, which contains all the information we want.
    """

    item = {}

    # Creating the BeautifulSoup object and regex pattern
    soup = BeautifulSoup(html, "lxml")
    pattern = re.compile(r'var\s+skuJson_0\s*=\s*(\{.*?\})\s*;\s*')

    # Get the pattern, and transform the JS object string into a dict
    script = soup.find("script", text=pattern).string
    item_json = pattern.search(script).group().strip('var skuJson_0 = ;')
    item_info = json.loads(item_json)

    # Retrieving the item information
    item["name"] = item_info["name"]
    item["available"] = item_info["skus"][0]["available"]

    # Calculating the price considering further discounts
    price_best = 0.95 * float(item_info["skus"][0]["bestPrice"]) / 100
    item["price"] = round(price_best, 2)

    return item


def boadica_parser(html):
    """
    Parser for boadica.com.br.

    The values are scattered throughout the site; the price is already
    formatted, and to check availability we need to see if min = max.
    """

    item = {}

    # Creating the BeautifulSoup object
    soup = BeautifulSoup(html, "lxml")

    # Get the item name and min and max values
    item["name"] = soup.findAll('div', {'class': 'nome'})[0].string.strip()
    min_str, max_str = [x.text for x in
                        soup.findAll('span', text=re.compile(r"^R\$"))]

    # Check if the min and max values are the same
    if min_str == "R$ 0,00" and max_str == "R$ 0,00":
        item["available"] = False
        item["price"] = 0.0
    else:
        item["available"] = True
        item["price"] = brl_converter(min_str)

    return item


PARSERS = {"cea.com.br": cea_parser,
           "boadica.com.br": boadica_parser}
