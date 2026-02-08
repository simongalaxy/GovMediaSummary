from pprint import pformat, pprint
import asyncio
import json, re

from tools.logger import Logger
from tools.NewsCrawler import NewsCrawler
from tools.DocumentGenerator import DocumentGenerator
from tools.ChromaDBHandler import ChromaDBHandler


def main():
    
    # declare classes.
    logger = Logger(__name__).get_logger()
    crawler = NewsCrawler(logger=logger)
    DocGenerator = DocumentGenerator(logger=logger)
    Chroma = ChromaDBHandler(logger=logger)
    
    
    # generate urls by date range.
    startDate = "20260201"
    endDate = "20260201"
    urls = crawler.generate_date_urls(startDate=startDate, endDate=endDate)
    
    # crawl page links of press release.
    news_links = asyncio.run(crawler.crawl_date_pages(urls=urls))
    
    # get the data dictionaries from press releases.
    results = asyncio.run(crawler.crawl_news_pages(urls=news_links))
    
    # save crawled results to chromaDB.
    for result in results:
        documents = DocGenerator.create_Documents_from_news(result=result)
        Chroma.add_splits_to_db(documents=documents)
    
    ids = Chroma.get_unique_ids_from_metadata()
    logger.info(f"all ids: {ids}")
    
    for id in ids:
        list = Chroma.get_all_splits_by_id(metadata_id=id)
        for item in list:
            logger.info("item: \n%s", pformat(item, indent=2))
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
