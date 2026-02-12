from pprint import pformat, pprint
import asyncio
import json, re

from tools.logger import Logger
from tools.NewsCrawler import NewsCrawler
from tools.ChromaDBHandler import ChromaDBHandler


def main():
    
    # declare classes.
    logger = Logger(__name__).get_logger()
    db_handler = ChromaDBHandler(logger=logger)
    crawler = NewsCrawler(logger=logger, db_handler=db_handler)
    
    # generate urls by date range.
    startDate = "20260101"
    endDate = "20260107"
    urls = crawler.generate_date_urls(startDate=startDate, endDate=endDate)
    
    # crawl page links of press release.
    news_links = asyncio.run(crawler.crawl_date_pages(urls=urls))
    
    # get the data dictionaries from press releases and save results to chromadb.
    asyncio.run(crawler.crawl_news_pages(urls=news_links))
    
  
    # # generate report.
    # while True:
    #     question = input("Enter the question or type 'q' for quit: ")
    #     logger.info(f"question entered: {question}")
    #     if question.lower() == "q":
    #         logger.info("User quit.")
    #         break
    #     query_str = sql_generator.generate_sql(question=question)
    #     logger.info(f"query_str: {query_str}")
        
    return
        
        
    
    
if __name__ == "__main__":
    main()
