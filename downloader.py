import aiohttp
import asyncio
import time


class Downloader:

    _nums_threads = 10
    _max_count_attempts = 5

    @staticmethod
    def segmentation(iter, length):
        i = 0
        while True:
            l = len(iter)
            if i + length <= l:
                yield iter[i: i + length]
                i += length
            else:
                yield iter[i:]
                break

    @staticmethod
    async def download_page_with_given_session(url, session, method="GET", **kwargs):
        count_attempts = 0
        response_status = None
        exception = None
        while True:
            count_attempts += 1
            if count_attempts >= Downloader._max_count_attempts:
                return {"count_attempts": count_attempts, "response_status": response_status, "exception": exception}
            try:
                async with session.request(method, url, **kwargs) as response:
                    if 200 <= response.status < 299:
                        page = await response.text()
                        return page
                    else:
                        response_status = response.status
                        count_attempts += 1
            except Exception as ex:
                exception = ex

    @staticmethod
    async def download_page(url, method="GET", **kwargs):
        count_attempts = 0
        response_status = None
        exception = None
        while True:
            count_attempts += 1
            if count_attempts >= Downloader._max_count_attempts:
                return {"count_attempts": count_attempts, "response_status": response_status, "exception": exception}
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.request(method, url, **kwargs) as response:
                        if 200 <= response.status < 299:
                            page = await response.text()
                            return page
                        else:
                            response_status = response.status
                            count_attempts += 1
            except Exception as ex:
                print(ex)
                exception = ex

    @staticmethod
    async def download_pages(urls, method="GET", **kwargs):
        async with aiohttp.ClientSession() as session:
            for l_urls in Downloader.segmentation(urls, Downloader._nums_threads):
                tasks = [Downloader.download_page_with_given_session(url, session, method, **kwargs) for url in l_urls]
                yield await asyncio.gather(*tasks)

    @staticmethod
    async def download_pages_with_new_session_in_each_segmentation(urls, method="GET", **kwargs):
        for l_urls in Downloader.segmentation(urls, Downloader._nums_threads):
            async with aiohttp.ClientSession() as session:
                tasks = [Downloader.download_page_with_given_session(url, session, method, **kwargs) for url in l_urls]
                yield await asyncio.gather(*tasks)

    @staticmethod
    async def download_pages_with_different_headers_for_each_url(urls, list_headers, method="GET", **kwargs):
        async with aiohttp.ClientSession() as session:
            for l_urls in Downloader.segmentation(urls, Downloader._nums_threads):
                tasks = [Downloader.download_page_with_given_session(urls[i], session, method, headers=list_headers[i],
                                                                     **kwargs) for i in range(len(l_urls))]
                yield await asyncio.gather(*tasks)

