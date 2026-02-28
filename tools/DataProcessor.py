from datetime import datetime, timedelta, date, time
from crawl4ai import CrawlResult
from typing import List
import re


from tools.logger import Logger

# data processing functions.
def generate_date_range(startDate: str, endDate: str, logger: Logger) -> list[str]:
    start_date = datetime.strptime(startDate, "%Y%m%d")
    end_date = datetime.strptime(endDate, "%Y%m%d")
    
    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current.strftime("%Y%m%d"))
        current += timedelta(days=1)
    
    logger.info(f"Generated date range from {startDate} to {endDate}: {dates}")
    
    return dates


def generate_date_urls(startDate: str, endDate: str, logger: Logger) -> list[str]:
    dates = generate_date_range(startDate=startDate, endDate=endDate, logger=logger)
    urls = [f"https://www.info.gov.hk/gia/general/{date[:-2]}/{date[-2:]}.htm" for date in dates]
    logger.info(f"Generated {len(urls)} date URLs: {urls}")
    
    return urls


def consolidate_news_urls(results: List[CrawlResult], logger: Logger) -> list[str]:
    news_links = []
    for result in results:
        links = result.links.get("internal", [])
        for link in links:
            if re.search(pattern=r"P.*\.htm", string=link["href"]):
                    news_links.append(link["href"])
    
    logger.info(f"Extracted {len(news_links)} news URLs from crawl results.")
    logger.info(f"Consolidated news URLs: {news_links}")
    
    return news_links


def date_to_unix(date_str: str) -> int: 
    dt = datetime.strptime(date_str, "%B %d, %Y") 
    
    return int(dt.timestamp())


def transform_text_to_date(date_str: str, logger: Logger) -> str:
    try:
        date_obj = datetime.strptime(date_str, "%B %d, %Y")
        return date_obj.strftime("%Y-%m-%d")
    except ValueError as e:
        logger.error(f"Date conversion error for '{date_str}': {e}")
        return date_str

def transform_text_to_time(time_str: str, logger: Logger) -> str:
    try:
        time_obj = datetime.strptime(time_str, "%H:%M")
        return time_obj.strftime("%H:%M:%S")
    except ValueError as e:
        logger.error(f"Time conversion error for '{time_str}': {e}")
        return time_str