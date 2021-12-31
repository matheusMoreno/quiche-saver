# Quiche Saver

Quiche Saver (_queish_, cash... get it?) is a Telegram bot that monitors products
for you. It checks when a product is available and when its price is lower than a
maximum value provided. It uses [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/)
to parse HTMLs and the [Python Telegram Bot](https://python-telegram-bot.readthedocs.io/en/stable/)
to work.

Yes, there are some price monitors out there, but my motivation was exactly because
a lot of those price monitors are unrealiable. I recommend using this bot when
there's a product out there that you _really_ want and don't want to miss any
possible updates.

## Installation

First, you need to [create a bot with the BotFather](https://core.telegram.org/bots#creating-a-new-bot).
After setting up a name and an username, he will give you a token. You must create
the file `quichesaver/conf/.env` and write:

```
TELEGRAM_TOKEN=<YOUR_TOKEN_HERE>
```

Next, install the Gecko Driver necessary for Selenium:

```bash
# Linux
sudo apt-get install geckodriver

# MacOS
brew install geckodriver
```

Finally, install the necessary requirements with `pip install -r requirements.txt`
(preferably on a virtual environment) and run `python -m quichesaver.quichesaver`.

## Important considerations

If you want to change the delay between checks, you can change the `MONITOR_INTERVAL`
constant on `quichesaver/quichesaver.py`. In the same file, there's a constant called
`ITEM_INTERVAL`; this is the delay between individual checks (per product). This is
an important constant because some websites can block you if you make too many requests
in a short period of time.

Also, I must say that this is minimal working version. Only two stores are implemented
(for now), and both are brazilian. By simply adding a new parser logic to
`quichesaver/parsers.py`, you can add that store to your version.

**Current stores supported:**
- [Boa Dica](https://www.boadica.com.br/)
- [Magazine Luiza](https://www.magazineluiza.com.br/)
- [Submarino](https://www.submarino.com.br/)
- [Americanas](https://www.americanas.com.br/)
- [Shoptime](https://www.shoptime.com.br/)
- [Casas Bahia](https://www.casasbahia.com.br/)
- [Extra](https://www.extra.com.br/)
- [Ponto Frio](https://www.pontofrio.com.br/)
- [Kabum](https://www.kabum.com.br/)
- [Fast Shop](https://www.fastshop.com.br/)
- [Amazon](https://www.amazon.com.br/)
