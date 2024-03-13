import asyncio
from urllib.parse import urljoin

import aiohttp
import pandas as pd
from bs4 import BeautifulSoup

from orpi_scrap.formatting import bcolors

DOMAIN = 'https://www.orpi.com'


async def fetch_html(session, url):
    async with session.get(url) as response:
        html = await response.text()
    print(f"{bcolors.OKGREEN}Data received from {url}{bcolors.ENDC}")
    return html


async def find_all_cards(session, url):
    html = await fetch_html(session, url)
    soup = BeautifulSoup(html, 'html.parser')
    return soup.find_all('article', class_='')


async def parse_agencies(session, url):
    agencies = await find_all_cards(session, url)
    tasks = []
    for agency in agencies:
        link = agency.find('a', class_='c-link')
        if link is None:
            continue
        url = urljoin(DOMAIN, link['href'])
        tasks.append(parse_agency_page(session, url))
    return await asyncio.gather(*tasks)


async def parse_agency_page(session, url):
    agency_html = await fetch_html(session, url)
    soup = BeautifulSoup(agency_html, 'html.parser')
    name = soup.find('h1')
    try:
        return {
            'name': name.text if name else None,
            'address': soup.find('address').text if soup.find('address') else None
        }
    except AttributeError:
        print(f"Failed to parse agency page: {url}")


async def parse_and_fetch_suburls(url):
    async with aiohttp.ClientSession() as session:
        data = await parse_agencies(session, url)
        export_data(data)


def export_data(data):
    pd.DataFrame(data).to_csv('orpi_agencies.csv', index=False)


async def main():
    await parse_and_fetch_suburls(urljoin(DOMAIN, 'agences-immobilieres'))


if __name__ == "__main__":
    asyncio.run(main())
