from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup as bs
from urllib.parse import unquote
import pandas as pd
import numpy as np
import time


def loadingContents(driver, height, speed):
    """
    This function scrolls though the webpage of the
    site. This function is necessary because the
    contents of the page doesn't load unless we've
    scrolled passed them.

    Args:
        driver      : Selenium Driver.
        height (int): How much the driver will scroll.
        speed (int):  Speed at which the driver will scroll.
    """
    for i in range(height):
        driver.execute_script("window.scrollTo(0,{})".format(i*speed))


def linkScraper(driver, slinks):
    """
    This function scrapes the links of the products.

    Args:
        driver:         Selenium Driver.
        slinks (list):  Where to save all the links.
    """
    html = driver.page_source
    soup = bs(html, 'lxml')

    container = soup.find("div", attrs={"class": "css-13l3l78 e1nlzfl10"})
    product_list = container.find_all('div', attrs={"class": "css-bk6tzz e1nlzfl3"})
    
    for link in container.find_all('a'):
        link = unquote(link.get('href'))
        link = link[link.find('https://www'):]
        link = link[: link.find('?')]
        slinks.append(link)


def bodyParser(df, soup, link):
    """
    This function parses thought the contents of
    each of the product links and extracts the
    required elements.

    Args:
        df               (pd.df): Dataframe of the webpages
        soup (bs4.BeautifulSoup): BeautifulSoupHTML Parser.
        link               (str): Link of product.
    """
    name = soup.find("h1", attrs={"data-testid": "lblPDPDetailProductName"}).text         
    description = soup.find("div", attrs={"role": "tabpanel"}).text
    price = soup.find("div", attrs={"class": "price"}).text
    price = int(price.replace("Rp", "").replace(".", "", 3))

    rating = soup.find("span", attrs={"data-testid": "lblPDPDetailProductRatingNumber"})
    if (rating == None):
        rating = "NULL"
    else:
        rating = soup.find("span", attrs={"data-testid": "lblPDPDetailProductRatingNumber"}).text
        
    store = soup.find("a", attrs={"class": "css-1n8curp"}).text
    img_links = []
    image_link = soup.find_all("img", attrs={"crossorigin": "anonymous"})
    for src in (image_link):
        img_links.append((src.get('src')))

    product_info = {'link': link,
            'name': name,
            'description': description,
            'image_link': img_links,
            'price': price,
            'rating':rating,
            'store': store}
    
    index = df.index[df['link']==link].tolist()
    index = index[0]
    df.iloc[index:index+1, 1:] = [name, description, price, rating, store, img_links]


def scraper(driver, df, scraped_links, try_count):
    """
    This function iterates through all the
    pages and parses them.

    Args:
        driver               : Selenium Driver.
        scraped_links (pd.df): Dataframe of the webpages.
        try_count       (int): Times attempted to load a page.
    """
    for link in range(len(scraped_links)):

        while True:

            print(link+1, "/", len(scraped_links))
            
            try:
                driver.get(scraped_links[link])
                loadingContents(driver, 50, 1)

                time.sleep(2)  # Sleepy Time ^_^
                html = driver.page_source
                soup = bs(html, 'lxml')

                bodyParser(df, soup, scraped_links[link])
                time.sleep(4) # Sleepy Time ^_^
                try_count = 1
                print("Scraping", link + 1, "out of", len(scraped_links), "products.")

            except AttributeError as atr:

                try_count = try_count + 1
                if (try_count == 5):
                    print("Webpage not loading. Moving on to the next product.")
                    try_count = 0
                    
                    index = df.index[df['link']==scraped_links[link]].tolist()
                    index = index[0]
                    df.iloc[index:index+1, 1:] = [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan]
                    break

                else:
                    print("Retrying in", 10 * try_count, "seconds...")
                    time.sleep(10 * try_count)
                    continue
            break


def to_csv(df):
    """
    This function removes the first column
    of the df and outputs a csv file.

    Args:
        df (pd.df): Dataframe of products

    """
    df = df.iloc[:, 1:]
    df.to_csv("Top100Handphones.csv", index=False)
    


def main():
    options = Options()
    options.page_load_strategy = 'normal'

    driver = webdriver.Chrome(options=options)

    links = ['https://www.tokopedia.com/p/handphone-tablet/handphone',
        'https://www.tokopedia.com/p/handphone-tablet/handphone?page=2']

    scraped_links = []
    
    print("Going through all the list of products.")
    for i in range(len(links)):
        driver.get(links[i])
        driver.maximize_window()    
        loadingContents(driver, 325, 15)
        linkScraper(driver, scraped_links)

    len(scraped_links)
    scraped_links = scraped_links[:100]    # we need to scrape 100

    columns = ['link', 'name', 'description', 'price', 'rating', 'store', 'img_links']
    df = pd.DataFrame(columns=columns) 
    df['link'] = scraped_links

    dfx = df.copy()

    while True:
        if (df.isnull().values.any()):
            
            scraper(driver, df, dfx['link'], 1)
            dfx = df[df.isna().any(axis=1)].copy()
            dfx=dfx.reset_index(drop=True)
            print("Retrying the webpages that wouldn't load...")
            to_csv(df)
        else:
            break

    driver.quit()

if __name__ == "__main__":
    print("Starting Scraper")
    main()