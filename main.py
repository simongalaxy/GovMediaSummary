from pprint import pprint
import asyncio
import json, re

from tools.logger import Logger
from tools.NewsCrawler import NewsCrawler
from tools.PostgresDatabase import PostgresDBHandler
from tools.ReportGenerator import ReportGenerator

def main():
    
    # declare classes.
    logger = Logger(__name__).get_logger()
    DBHandler = PostgresDBHandler(logger=logger)
    DBHandler.check_and_create_table()
    crawler = NewsCrawler(logger=logger, db_handler=DBHandler)
    generator = ReportGenerator(logger=logger)
    
    # generate urls by date range.
    # startDate = "20260101"
    # endDate = "20260123"
    # urls = crawler.generate_date_urls(startDate=startDate, endDate=endDate)
    
    # # crawl page links of press release.
    # news_links = asyncio.run(crawler.crawl_date_pages(urls=urls))
    
    # # get the data dictionaries from press releases.
    # asyncio.run(crawler.crawl_news_pages(urls=news_links))
    
    # generate report.
    query_dict = {"date": "2026-01-01"}
    generator.generate_report(query=query_dict)
    
if __name__ == "__main__":
    main()
