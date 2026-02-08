from unittest import result
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig, MemoryAdaptiveDispatcher, LLMConfig, LLMExtractionStrategy
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy

from pprint import pformat
import asyncio, json, re, os
# from pydantic import BaseModel, Field
# from typing import List
from datetime import datetime, timedelta, date, time
# from dotenv import load_dotenv
# load_dotenv()

# from tools.PostgresDatabase import News

# class Summary(BaseModel):
#     title: str = Field(description="title of the content")
#     organization: str = Field(description="organization issued the content")
#     pub_date: date = Field(description="date issued the content")
#     pub_time: time = Field(description="time issued the content")
#     keywords: list[str] = Field(description="Maximun 5 content keywords")
#     summary: str = Field(description="Summary of key points no more than 700 words")
    
   
class NewsCrawler:
    def __init__(self, logger):
        self.logger = logger
        # self.db_handler = db_handler
        self.browser_config = BrowserConfig(
            headless=True,
            text_mode=True,
            light_mode=True
        )
        self.crawl_config_datePage = CrawlerRunConfig(
            scraping_strategy=LXMLWebScrapingStrategy(),
            exclude_all_images=True,
            exclude_external_links=True,
            exclude_social_media_domains=True,
            target_elements=['div[class="leftBody"]'],
            cache_mode=CacheMode.BYPASS
        )
        self.llm_config = LLMConfig(
            provider=os.getenv("provider"),    # provider="ollama/mistral:latest"
            temperature=0.1
        )
        # self.llm_extraction = LLMExtractionStrategy(
        #     llm_config=self.llm_config,
        #     schema=Summary.model_json_schema(),
        #     extraction_type="schema",
        #     instruction="Extract the following items.",
        #     chunk_token_threshold=1200,
        #     overlap_rate=0.1,
        #     apply_chunking=True,
        #     input_format="markdown",
        #     extra_args={"temperature": 0.1, "max_tokens": 1000},
        #     verbose=True
        # )
        self.crawl_config_newsPage = CrawlerRunConfig(
            scraping_strategy=LXMLWebScrapingStrategy(),
            exclude_all_images=True,
            exclude_external_links=True,
            exclude_social_media_domains=True,
            target_elements=['div[id="PRHeadline"]', 'span[id="pressrelease"]'],
            cache_mode=CacheMode.BYPASS,
            # extraction_strategy=self.llm_extraction,
            # stream=True # Enable streaming 
        )
        self.dispatcher = MemoryAdaptiveDispatcher(
            memory_threshold_percent=80,
            check_interval=1,
            max_session_permit=3
        )
    
    # crawling functions.
    async def crawl_date_pages(self, urls: list[str]):
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            results = await crawler.arun_many(
                urls=urls,
                config=self.crawl_config_datePage,
                dispatcher=self.dispatcher
            )
        news_links = []
        for result in results:
            links = result.links.get("internal", [])
            for link in links:
                if re.search(pattern=r"P.*\.htm", string=link["href"]):
                        news_links.append(link["href"])
        
        return news_links
    
    
    async def crawl_news_pages(self, urls: list[str]) -> list[dict]:
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            results = await crawler.arun_many(
                urls=urls,
                config=self.crawl_config_newsPage,
                dispatcher=self.dispatcher
            )
        
        # for i, result in enumerate(results, start=1):
        #     self.logger.info(f"result: \n%s", pformat(result))
        
        return results
 
    # async def crawl_news_pages(self, urls: list[str]) -> None:
    #     async with AsyncWebCrawler(config=self.browser_config) as crawler:
    #         async for result in await crawler.arun_many(
    #             urls=urls,
    #             config=self.crawl_config_newsPage,
    #             dispatcher=self.dispatcher
    #         ):
            
    #             if result.success:
    #                 try:
    #                     data = json.loads(result.extracted_content)[0]
    #                 except Exception as e:
    #                     self.logger.error(f"JSON loading error: {e}")
    #                 if not data:
    #                     self.logger.error(f"No data extracted from url: {result.url}")
    #                     continue
                    
    #                 # save to chromadb.
    #                 news_item = News(
    #                     id=result.url.split("/")[-1].split(".")[0],
    #                     url=result.url,
    #                     title=data.get("title"), #result.metadata["title"],
    #                     pub_date=data.get("pub_date"), #self.transform_text_to_date(result.markdown.split("\n")[-4].split(", ", 1)[-1].strip()),
    #                     pub_time=data.get("pub_time"), #self.transform_text_to_time(result.markdown.split("\n")[-3].split(" ")[-2]),
    #                     organization=data.get("organization"),
    #                     summary=data.get("summary"),
    #                     keywords=data.get("keywords"),
    #                     content=result.markdown
    #                 )
    #                 # self.db_handler.create_News(news_item=news_item)
    #                 self.logger.info(f"News: \n%s", pformat(news_item.model_dump(), indent=2))
    #             else:
    #                 self.logger.error(f"Failed to crawl URL: {result.url}")
            
    #     return None
    
    # data processing functions.
    def generate_date_range(self, startDate: str, endDate: str) -> list[str]:
        start_date = datetime.strptime(startDate, "%Y%m%d")
        end_date = datetime.strptime(endDate, "%Y%m%d")
        
        dates = []
        current = start_date
        while current <= end_date:
            dates.append(current.strftime("%Y%m%d"))
            current += timedelta(days=1)
        
        self.logger.info(f"Generated date range from {startDate} to {endDate}: {dates}")
        
        return dates
    
    
    def generate_date_urls(self, startDate: str, endDate: str) -> list[str]:
        dates = self.generate_date_range(startDate=startDate, endDate=endDate)
        urls = [f"https://www.info.gov.hk/gia/general/{date[:-2]}/{date[-2:]}.htm" for date in dates]
        self.logger.info(f"Generated {len(urls)} date URLs: {urls}")
        
        return urls
