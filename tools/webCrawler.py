from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig, MemoryAdaptiveDispatcher, LLMConfig, LLMExtractionStrategy
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy

from pprint import pprint
import asyncio, json, re
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime, timedelta

class Summary(BaseModel):
    summary: str = Field(description="content summary")
    
    
class NewsSummarizer:
    def __init__(self):
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
            provider="ollama/mistral:latest",
            temperature=0.1
        )
        self.llm_extraction = LLMExtractionStrategy(
            llm_config=self.llm_config,
            schema=Summary.model_json_schema(),
            extraction_type="schema",
            instruction="Summarize the content no more than 400 words.",
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
            extraction_strategy=self.llm_extraction
        )
        self.dispatcher = MemoryAdaptiveDispatcher(
            memory_threshold_percent=70,
            check_interval=1,
            max_session_permit=3
        )
    
    
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
    
    
    async def crawl_news_pages(self, urls: list[str]):
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            results = await crawler.arun_many(
                urls=urls,
                config=self.crawl_config_newsPage,
                dispatcher=self.dispatcher
            )
            dicts = []
            for i, result in enumerate(results, start=1):
                if result.success:
                    dict = {
                        "id": result.url.split("/")[-1].split(".")[0],
                        "url": result.url,
                        "title": result.metadata["title"],
                        "date": result.markdown.split("\n")[-4].split(", ", 1)[-1].strip(),
                        "time": result.markdown.split("\n")[-3].split(" ")[-2],
                        "content": result.markdown,
                        "summary": self.consolidate_summary(result=result)
                    }
                    print(f"No. {i}:")
                    pprint(dict)
        
        return dicts
    
    
    def generate_date_range(self, startDate: str, endDate: str) -> list[str]:
        start_date = datetime.strptime(startDate, "%Y%m%d")
        end_date = datetime.strptime(endDate, "%Y%m%d")
        
        dates = []
        current = start_date
        while current <= end_date:
            dates.append(current.strftime("%Y%m%d"))
            current += timedelta(days=1)
        
        return dates
    
    
    def generate_date_urls(self, startDate: str, endDate: str) -> list[str]:
        dates = self.generate_date_range(startDate=startDate, endDate=endDate)
        urls = [f"https://www.info.gov.hk/gia/general/{date[:-2]}/{date[-2:]}.htm" for date in dates]
        
        return urls

    def consolidate_summary(self, result) -> list[str]:
        
        summary_text = []
        for item in json.loads(result.extracted_content):
            try:
                summary_text.append(item["summary"])
            except KeyError:
                print("Missing summary key:", item)
                summary_text.append("")   # or skip it

        return summary_text