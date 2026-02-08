from pprint import pformat, pprint
import asyncio
import json, re

from tools.logger import Logger
from tools.NewsCrawler import NewsCrawler
<<<<<<< HEAD
from tools.DocumentGenerator import DocumentGenerator
from tools.ChromaDBHandler import ChromaDBHandler
=======
from tools.PostgresDatabase import PostgresDBHandler
# from tools.ReportGenerator import ReportGenerator
# from tools.SQLGenerator import SQLGenerator
from tools.writeReport import write_report


# async def process_press_release_question(user_question: str, Rptgenerator: ReportGenerator, SQLgenerator: SQLGenerator):
#     sql = await SQLgenerator.generate_sql(user_question=user_question)
#     rows = SQLgenerator.query_to_db(sql=sql)
#     report = await Rptgenerator.generate_report(sql=sql, rows=rows)
    
#     return report
>>>>>>> 3864561a08e95430ee068c22aee40675c45a25be


def main():
    
    # declare classes.
    logger = Logger(__name__).get_logger()
<<<<<<< HEAD
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
=======
    DBHandler = PostgresDBHandler(logger=logger)
    DBHandler.check_and_create_table()
    crawler = NewsCrawler(logger=logger, db_handler=DBHandler)
    # report_generator = ReportGenerator(logger=logger)
    # sql_generator = SQLGenerator(logger=logger)
    
    # generate urls by date range.
    startDate = "20260202"
    endDate = "20260202"
    urls = crawler.generate_date_urls(startDate=startDate, endDate=endDate)
    
    # crawl page links of press release.
    news_links = asyncio.run(crawler.crawl_date_pages(urls=urls))
    
    # get the data dictionaries from press releases.
    asyncio.run(crawler.crawl_news_pages(urls=news_links))
    
    # # generate report.
    # while True:
    #     question = input("Enter the question or type 'q' for quit: ")
    #     if question.lower() == "q":
    #         logger.info("User quit.")
    #         break
    #     report = process_press_release_question(
    #         user_question=question,
    #         Rptgenerator=report_generator,
    #         SQLgenerator=sql_generator
    #     )
    #     logger.info(report)
    #     # if report is not None:
    #     #     write_report(markdown=report)
>>>>>>> 3864561a08e95430ee068c22aee40675c45a25be
        
    return
        
        
    
    
if __name__ == "__main__":
    main()
