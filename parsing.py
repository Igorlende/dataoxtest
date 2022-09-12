import bs4
import re
from datetime import datetime, timedelta
import time
from sqlalchemy.orm import Session
from db.models import Ads
from db.models import engine
from downloader import Downloader
from tqdm import tqdm


class Parser:

    _headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "uk,ru-RU;q=0.9,ru;q=0.8,en-US;q=0.7,en;q=0.6",
        'sec-ch-ua': '"Chromium";v="104", " Not A;Brand";v="99", "Google Chrome";v="104"',
        "sec-ch-ua-mobile": "?1",
        'sec-ch-ua-platform': '"Android"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Mobile Safari/537.36"
    }

    @staticmethod
    def parse_page(page) -> list:

        def delete_spaces_and_other_rubbish(text):
            text = re.sub('\\n +', '', text)
            text = text.replace('\n', '')
            return text

        def find_date_by_hours(date):
            hours = int(re.search("\d+", date).group(0))
            d = datetime.today() - timedelta(hours=hours, minutes=0)
            return d.strftime("%d/%m/%Y")

        def find_date_by_minutes(date):
            minutes = int(re.search("\d+", date).group(0))
            d = datetime.today() - timedelta(minutes=minutes)
            return d.strftime("%d/%m/%Y")

        soup = bs4._soup(page, "html.parser")
        ads = soup.find_all('div', {'data-listing-id': re.compile('^\d+$')})
        result = []
        for ad in ads:

            data = {
                "title": None,
                "city": None,
                "date": None,
                "price": None,
                "description": None,
                "image": None,
                "beds": None,
                "currency": None,
                "link": None
            }

            title = ad.find("div", {"class": "title"}).get_text()
            title = delete_spaces_and_other_rubbish(title)
            city = ad.find("div", {"class": "location"}).find("span").get_text()
            city = delete_spaces_and_other_rubbish(city)
            date = ad.find("span", {"class": "date-posted"}).get_text()
            date = delete_spaces_and_other_rubbish(date)
            if "hour" in date:
                date = find_date_by_hours(date)
            elif "minute" in date:
                date = find_date_by_minutes(date)
            elif "Yesterday" in date:
                d = datetime.today() - timedelta(hours=24)
                date = d.strftime("%d/%m/%Y")

            date = date.replace("/", "-")
            price = ad.find("div", {"class": "price"}).get_text()
            price = delete_spaces_and_other_rubbish(price)
            currency = None
            if "$" in price:
                currency = "$"
                price = price.replace("$", "")

            description = ad.find("div", {"class": "description"}).get_text()
            description = delete_spaces_and_other_rubbish(description)
            image = ad.find("div", {"class": "image"}).find("img").get("data-src")
            if image is not None:
                image = image.replace("rule=kijijica-200", "rule=kijijica-640")
            beds = ad.find("span", {"class": "bedrooms"}).get_text()
            beds = delete_spaces_and_other_rubbish(beds)
            beds = beds.replace("Beds:", "")

            link = "https://www.kijiji.ca" + ad.find("div", {"class": "title"}).find("a").get("href")

            data["title"] = title
            data["city"] = city
            data["date"] = date
            data["price"] = price
            data["description"] = description
            data["image"] = image
            data["beds"] = beds
            data["currency"] = currency
            data["link"] = link

            result.append(data)

        return result

    @staticmethod
    async def get_urls() -> list:
        url = "https://www.kijiji.ca/b-apartments-condos/city-of-toronto/c37l1700273"
        response = await Downloader.download_page(url, headers=Parser._headers)

        soup = bs4._soup(response, "html.parser")
        count_results = soup.find("span", {"class": re.compile("resultsShowingCount-\d+")}).get_text()

        count_results = re.search("\d+ results", count_results).group(0)
        count_results = re.search("\d+", count_results).group(0)

        count_results = int(count_results)
        count_ads_in_page = 40
        count = 0
        page = 1
        urls = []

        while count <= count_results:
            url = f"https://www.kijiji.ca/b-apartments-condos/city-of-toronto/page-{page}/c37l1700273"
            urls.append(url)
            page += 1
            count += count_ads_in_page

        return urls

    """
    def is_there_next_page(page):
        soup = bs4._soup(page, "html.parser")
        next = soup.find("a", {"title": "Next"})
        if next is None:
            return False
        return "https://www.kijiji.ca/" + next.get("src")
    """

    @staticmethod
    def delete_previous_ads_in_db() -> bool:
        session = Session(engine)
        try:
            num_rows_deleted = session.query(Ads).delete()
            session.commit()
        except Exception:
            session.rollback()
            session.close()
            return False

        session.close()
        return True

    @staticmethod
    def add_ads_to_db(ads) -> bool:

        session = Session(engine)

        for ad in ads:
            session.add(Ads(title=ad["title"], city=ad["city"], date=ad["date"],
                            description=ad["description"], image=ad["image"],
                            beds=ad["beds"], price=ad["price"], currency=ad["currency"],
                            link=ad["link"]))

        try:
            session.commit()
        except Exception:
            session.rollback()
            session.close()
            return False

        session.close()
        return True

    @staticmethod
    def get_headers(len_pages) -> list:
        headers = []
        for page in range(1, len_pages):
            new_headers = Parser._headers
            new_headers["referer"] = f"referer: https://www.kijiji.ca/b-apartments-condos/city-of-toronto/page-{page}" \
                                     f"/c37l1700273"
            headers.append(new_headers)

        return headers

    @staticmethod
    async def main():

        urls = await Parser.get_urls()
        headers = Parser.get_headers(len(urls))
        count = 0
        pbar = tqdm(total=len(urls), desc='Parsing')
        if Parser.delete_previous_ads_in_db() is False:
            raise Exception("cannot delete previous ads in db")

        async for res in Downloader.download_pages_with_different_headers_for_each_url(urls, headers):
            for page in res:
                data = Parser.parse_page(page)
                """
                print(f"---count={count}---")
                print(urls[count])
                for el in data:
                    print(el)
                """
                if Parser.add_ads_to_db(data) is False:
                    raise Exception("cannot add ads to db")
                if len(data) == 0:
                    """
                    with open(f"error{count}.html", "w", encoding="utf-8") as f:
                        f.write(page)
                    """
                    urls.append(urls[count])
                count += 1
                pbar.update(1)
            time.sleep(60)
        pbar.close()
        return True

