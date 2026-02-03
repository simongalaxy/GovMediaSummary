from unittest import result
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig, MemoryAdaptiveDispatcher, LLMConfig, LLMExtractionStrategy
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy

from pprint import pformat
import asyncio, json, re, os
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime, timedelta, date, time
from dotenv import load_dotenv
load_dotenv()

from tools.PostgresDatabase import News

class Summary(BaseModel):
    summary: str = Field(description="Summary of content no more than 700 words")
    keywords: list[str] = Field(description="5 keywords of the content")
    organization: str = Field(description="Subject Department or Bureau")

class NewsCrawler:
    def __init__(self, logger, db_handler):
        self.logger = logger
        self.db_handler = db_handler
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
        self.llm_extraction = LLMExtractionStrategy(
            llm_config=self.llm_config,
            schema=Summary.model_json_schema(),
            extraction_type="schema",
            instruction="Summarize the content and extract the items.",
            chunk_token_threshold=1200,
            overlap_rate=0.1,
            apply_chunking=True,
            input_format="markdown",
            extra_args={"temperature": 0.1, "max_tokens": 1000},
            verbose=True
        )
        self.crawl_config_newsPage = CrawlerRunConfig(
            scraping_strategy=LXMLWebScrapingStrategy(),
            exclude_all_images=True,
            exclude_external_links=True,
            exclude_social_media_domains=True,
            target_elements=['div[id="PRHeadline"]', 'span[id="pressrelease"]'],
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=self.llm_extraction,
            stream=True # Enable streaming 
        )
        self.dispatcher = MemoryAdaptiveDispatcher(
            memory_threshold_percent=75,
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
   
 
    async def crawl_news_pages(self, urls: list[str]) -> None:
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            async for result in await crawler.arun_many(
                urls=urls,
                config=self.crawl_config_newsPage,
                dispatcher=self.dispatcher
            ):
            
                if result.success:
                    try:
                        data = json.loads(result.extracted_content)[0]
                    except Exception as e:
                        self.logger.error(f"JSON loading error: {e}")
                    if not data:
                        self.logger.error(f"No data extracted from url: {result.url}")
                        continue
                    
                    news_item = News(
                        id=result.url.split("/")[-1].split(".")[0],
                        url=result.url,
                        title=result.metadata["title"],
                        pub_date=self.transform_text_to_date(result.markdown.split("\n")[-4].split(", ", 1)[-1].strip()),
                        pub_time=self.transform_text_to_time(result.markdown.split("\n")[-3].split(" ")[-2]),
                        organization=data.get("organization"),
                        content=result.markdown,
                        summary=data.get("summary"),
                        keywords=data.get("keywords")
                    )
                    self.db_handler.create_News(news_item=news_item)
                    self.logger.info(f"News: \n%s", pformat(news_item.model_dump(), indent=2))
                else:
                    self.logger.error(f"Failed to crawl URL: {result.url}")
            
        return None
    
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


    def consolidate_summary(self, result) -> list[str]:
        summary_text = []
        for item in json.loads(result.extracted_content):
            try:
                summary_text.append(item["summary"])
            except KeyError:
                self.logger.info("Missing summary key:", item)
                summary_text.append("")   # or skip it

        return summary_text


    def transform_text_to_date(self, date_str: str) -> str:
        try:
            date_obj = datetime.strptime(date_str, "%B %d, %Y")
            return date_obj.strftime("%Y-%m-%d")
        except ValueError as e:
            self.logger.error(f"Date conversion error for '{date_str}': {e}")
            return date_str
    
    
    def transform_text_to_time(self, time_str: str) -> str:
        try:
            time_obj = datetime.strptime(time_str, "%H:%M")
            return time_obj.strftime("%H:%M:%S")
        except ValueError as e:
            self.logger.error(f"Time conversion error for '{time_str}': {e}")
            return time_str