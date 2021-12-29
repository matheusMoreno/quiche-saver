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
    """Parse data for cea.com.br.

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
    # If it doesn't exist, the item is unavailable
    else:
        item_json = soup.find("i", {"class": "js-wishlist"})["data-product"]
        item_info = json.loads(item_json)

        item["name"] = item_info["name"]
        item["available"] = False
        item["price"] = 0.0

    return item


def submarino_parser(html):
    """Parse data for submarino.com.br.

    Available products have a span tag with the sale's price and a h1 tag
    with the product's name. Unavailable products have neither.
    """
    item = {}

    # Creating the BeautifulSoup object
    soup = BeautifulSoup(html, "lxml")

    # Getting the <span> tag with the price
    price_tag = soup.find("span", {"class": "sales-price"})

    if price_tag:
        item["name"] = soup.find("h1", id="product-name-default").string
        item["price"] = brl_converter(price_tag.string)
        item["available"] = True
    else:
        item["name"] = soup.find("h1", id="product-name-stock").string
        item["price"] = 0.0
        item["available"] = False

    return item


def americanas_parser(html):
    """Parse data for americanas.com.br.

    Similar to submarino.com.br, but with minor differences on tags.
    """
    item = {}

    # Creating the BeautifulSoup object
    soup = BeautifulSoup(html, "lxml")

    # In this website, every item has a product-name-default
    item["name"] = soup.find("h1", id="product-name-default").string

    # Getting the <span> tag with the price, this time with a regex
    regex = re.compile('.*SalesPrice.*')
    price_tag = soup.find("span", {"class": regex})

    if price_tag:
        item["price"] = brl_converter(price_tag.string)
        item["available"] = True
    else:
        item["price"] = 0.0
        item["available"] = False

    return item


def shoptime_parser(html):
    """Parse data for shoptime.com.br. Exactly the same as submarino.com.br."""
    return submarino_parser(html)


def casasbahia_parser(html):
    """Parse data for casasbahia.com.br.

    Very simple: a Javascript object containing everything we need.
    """
    item = {}

    # Creating the BeautifulSoup object
    soup = BeautifulSoup(html, "lxml")
    pattern = re.compile(r'var\s+siteMetadata\s*=\s*(\{.*?\})\s*;\s*')

    # Get the pattern, and transform the JS object string into a dict
    script = soup.find("script", text=pattern).string
    item_json = pattern.search(script).group().strip('var siteMetadata = ;')
    item_info = json.loads(item_json)

    # Retrieving the item information
    item["name"] = item_info["page"]["name"]
    item["price"] = item_info["page"]["product"]["salePrice"]
    item["available"] = item_info["page"]["product"]["StockAvailability"]

    return item


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


PARSERS = {
    "cea.com.br": cea_parser,
    "boadica.com.br": boadica_parser,
    "magazineluiza.com.br": magazineluiza_parser,
    "submarino.com.br": submarino_parser,
    "americanas.com.br": americanas_parser,
    "shoptime.com.br": shoptime_parser,
    "casasbahia.com.br": casasbahia_parser,
    "kabum.com.br": kabum_parser,
}
