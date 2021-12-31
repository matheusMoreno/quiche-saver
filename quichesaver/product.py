"""Defining the Product class and associated functions."""

import time
import logging
import tldextract

from selenium import webdriver
from selenium.common.exceptions import TimeoutException

from quichesaver.parsers import PARSERS


LOGGER = logging.getLogger(__name__)

DRIVER_OPTS = webdriver.FirefoxOptions()
DRIVER_OPTS.add_argument("--headless")


def store_domain(url):
    """Retrieve the store domain from an URL."""
    ext = tldextract.extract(url)
    return '.'.join([ext.domain, ext.suffix])


class Product():
    """Class for a monitored product."""

    stores = list(PARSERS.keys())

    def __init__(self, product_url, max_price):
        """Construct the Product class."""
        self.url = product_url
        self.store = store_domain(product_url)

        LOGGER.info("New product: %s at %s", self.url, self.store)

        # Check if the store has a corresponding parser
        if self.store not in Product.stores:
            raise ValueError(f"Store not implemented: {self.store}")

        self.update_product_info()
        self.unreachable_count = 0    # Count failures; for future versions
        self.max_price = max_price

        LOGGER.info("Product %s created with success.", self.name)

    def get_html(self):
        """Retrieve the HTML given an URL, using a Web Driver."""
        with webdriver.Firefox(options=DRIVER_OPTS) as driver:
            driver.set_page_load_timeout(20)

            try:
                driver.get(self.url)
                time.sleep(3)
            except TimeoutException as exc:
                self.unreachable_count += 1
                raise TimeoutException("Timeout for the data.") from exc

            html = driver.page_source

        return html

    def get_product_info(self):
        """Get the product's current info."""
        return {
            "name": self.name,
            "price": self.price,
            "available": self.available,
            "url": self.url
        }

    def update_product_info(self):
        """Update the product info from the product url."""
        html = self.get_html()
        info = PARSERS[self.store](html)

        self.name = info["name"]
        self.price = info["price"]
        self.available = info["available"]
        info["url"] = self.url

        return info
