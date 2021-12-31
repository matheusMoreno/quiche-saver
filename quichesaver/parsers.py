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


def boadica_parser(html):
    """Parse data for boadica.com.br.

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


def magazineluiza_parser(html):
    """Parse data for magazineluiza.com.br.

    There's an attribute with a JSON containing all the info we need when
    the item is available. When it isn't, we must retrieve the info from
    another JSON, one much less complete (without best price).
    """
    item = {}

    # Creating the BeautifulSoup object
    soup = BeautifulSoup(html, "lxml")

    # Checking if the class 'header-product__title' exists
    if soup.find('h1', {'class': "header-product__title"}):
        div_string = soup.find('div', {'class': "js-header-product"})
        item_info = json.loads(div_string["data-product"])

        item["name"] = item_info["fullTitle"]
        item["available"] = True
        item["price"] = brl_converter(item_info["bestPriceTemplate"])
    else:
        # If it doesn't exist, the item is unavailable
        item_json = soup.find("i", {"class": "js-wishlist"})["data-product"]
        item_info = json.loads(item_json)

        item["name"] = item_info["name"]
        item["available"] = False
        item["price"] = 0.0

    return item


def americanas_parser(html):
    """Parse data for americanas.com.br.

    There's a script somewhere on the page with a JSON containing the
    data for the desired product.
    """
    item = {}

    # Creating the BeautifulSoup object
    soup = BeautifulSoup(html, "lxml")

    # Retrieve de JSON
    data_raw = soup.find("script", type="application/ld+json").string
    data = json.loads(data_raw)["@graph"]
    data = next(x for x in data if x["@type"] == "Product")

    # Retrieving the information
    item = {
        "name": data.get("name"),
        "price": data.get("offers", {}).get("lowPrice", 0.0),
    }
    item["available"] = bool(item["price"])

    return item


def submarino_parser(html):
    """Parse data for submarino.com.br.

    Exactly the same as americanas.com.br.
    """
    return americanas_parser(html)


def shoptime_parser(html):
    """Parse data for shoptime.com.br.

    Exactly the same as americanas.com.br.
    """
    return americanas_parser(html)


def casasbahia_parser(html):
    """Parse data for casasbahia.com.br.

    Retrieve data from the HTML itself.
    """
    item = {}

    # Creating the BeautifulSoup object
    soup = BeautifulSoup(html, "lxml")

    # Getting product name and price
    name = soup.find("h1").string
    price_str = soup.find("span", id="product-price")

    # Retrieving the information
    item = {
        "name": name,
        "price": brl_converter(price_str.string) if price_str else 0.0,
        "available": bool(price_str),
    }

    return item


def extra_parser(html):
    """Parse data for extra.com.br.

    Exactly the same as casasbahia.com.br.
    """
    return casasbahia_parser(html)


def pontofrio_parser(html):
    """Parse data for pontofrio.com.br.

    Exactly the same as casasbahia.com.br.
    """
    return casasbahia_parser(html)


def kabum_parser(html):
    """Parse data for kabum.com.br.

    There's a script at the end of the page with a JSON containing the
    data for the desired product.
    """
    item = {}

    # Creating the BeautifulSoup object
    soup = BeautifulSoup(html, "lxml")

    # Getting the data dict
    data_raw = soup.find("script", id="__NEXT_DATA__").string
    data = json.loads(data_raw)["props"]["pageProps"]["productData"]

    # Retrieving the information
    item = {
        "name": data.get("name"),
        "price": data.get("priceDetails", {}).get("discountPrice", 0.0),
        "available": data.get("available"),
    }

    return item


def fastshop_parser(html):
    """Parse data for fastshop.com.br.

    Retrieve data from the HTML itself.
    """
    item = {}

    # Creating the BeautifulSoup object
    soup = BeautifulSoup(html, "lxml")

    # Getting product name and price
    name = soup.find("h1", {"class": "title"})
    price_str_fraction = soup.find("span", {"class": "price-fraction"})
    price_str_cents = soup.find("span", {"class": "price-cents"})

    # This store does not display the page if the item doesn't exist
    if not name:
        return {
            "name": None,
            "price": 0.0,
            "available": False,
        }

    # Convert name and price
    name = name.string
    price = brl_converter(
        price_str_fraction.string + price_str_cents.string
    ) if (price_str_fraction and price_str_cents) else 0.0

    # Retrieving the information
    item = {
        "name": name,
        "price": price,
        "available": bool(price),
    }

    return item


def amazon_parser(html):
    """Parse data for amazon.com.br.

    Retrieve data from the HTML itself.
    """
    item = {}

    # Creating the BeautifulSoup object
    soup = BeautifulSoup(html, "lxml")

    # Getting product name
    name = soup.find("span", id="productTitle").string

    # Getting product price
    price_span = soup.find("span", {"class": "priceToPay"})
    if price_span is None:
        price_span = soup.find("span", {"class": "apexPriceToPay"})
    price_str = price_span.find("span", {"class": "a-offscreen"}) \
        if price_span is not None else None

    # Retrieving the information
    item = {
        "name": name.strip(),
        "price": brl_converter(price_str.string) if price_str else 0.0,
        "available": bool(price_str),
    }

    return item


PARSERS = {
    "boadica.com.br": boadica_parser,
    "magazineluiza.com.br": magazineluiza_parser,
    "submarino.com.br": submarino_parser,
    "americanas.com.br": americanas_parser,
    "shoptime.com.br": shoptime_parser,
    "casasbahia.com.br": casasbahia_parser,
    "extra.com.br": extra_parser,
    "pontofrio.com.br": pontofrio_parser,
    "kabum.com.br": kabum_parser,
    "fastshop.com.br": fastshop_parser,
    "amazon.com.br": amazon_parser,
}
