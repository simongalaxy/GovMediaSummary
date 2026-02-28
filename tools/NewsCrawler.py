from unittest import result
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig, MemoryAdaptiveDispatcher, LLMConfig, LLMExtractionStrategy
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy

from tools.DataProcessor import generate_date_urls, consolidate_news_urls


from pprint import pformat
import asyncio, json, re, os
from pydantic import BaseModel, Field
from typing import List

from dotenv import load_dotenv
load_dotenv()

class Summary(BaseModel):
    keywords: List[str] = Field(description="content keywords no more than 5 words")
    organizations: List[str] = Field(description="all organizations mentioned in the content")
    summary: str = Field(description="content summary no more than 700 words")
    
   
class NewsCrawler:
    def __init__(self, logger, db_handler, document_generator):
        self.logger = logger
        self.db_handler = db_handler
        self.document_generator = document_generator
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
            instruction="Summarize the content no more than 700 words, extract keywords and organizations mentioned.",
            chunk_token_threshold=1500,
            overlap_rate=0.1,
            apply_chunking=True,
            input_format="markdown",
            extra_args={"temperature": 0.1, "max_tokens": 1500},
            verbose=True
        )
        self.crawl_config_newsPage = CrawlerRunConfig(
            scraping_strategy=LXMLWebScrapingStrategy(),
            exclude_all_images=True,
            exclude_external_links=True,
            exclude_social_media_domains=True,
            target_elements=['span[id="PRHeadlineSpan"]', 'span[id="pressrelease"]'],
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=self.llm_extraction,
            stream=True # Enable streaming 
        )
        self.dispatcher = MemoryAdaptiveDispatcher(
            memory_threshold_percent=80,
            check_interval=1,
            max_session_permit=3
        )
    
    
    # crawling functions.
    async def _crawl_date_pages(self, urls: list[str]):
        async with AsyncWebCrawler(
            config=self.browser_config,
            max_concurrency=3, 
            headless=True, 
            disable_images=True, 
            disable_css=True, 
            disable_scripts=True, 
            disable_pdf=True, 
            disable_video=True, 
            disable_audio=True, 
            extraction_mode="light",
            ) as crawler:
            
            results = await crawler.arun_many(
                urls=urls,
                config=self.crawl_config_datePage,
                dispatcher=self.dispatcher
            )
        news_links = consolidate_news_urls(results=results, logger=self.logger)
        
        return news_links
 

    async def _crawl_news_pages(self, urls: list[str]) -> None:
        async with AsyncWebCrawler(
            config=self.browser_config,
            max_concurrency=3, 
            headless=True, 
            disable_images=True, 
            disable_css=True, 
            disable_scripts=True, 
            disable_pdf=True, 
            disable_video=True, 
            disable_audio=True, 
            extraction_mode="light") as crawler:
            
            async for result in await crawler.arun_many(
                urls=urls,
                config=self.crawl_config_newsPage,
                dispatcher=self.dispatcher
            ):
            
                if result.success:
                    try:
                        data = json.loads(result.extracted_content)[0]
                        ids, metadatas, all_splits = self.document_generator.generate_documents(data=data, result=result)
                        self.db_handler.add_documents_to_chromadb(ids=ids, metadatas=metadatas, documents=all_splits)
                    except Exception as e:
                        self.logger.error(f"JSON loading error: {e}")
                    if not data:
                        self.logger.error(f"No data extracted from url: {result.url}")
                        continue
                else:
                    self.logger.error(f"Failed to crawl URL: {result.url}")
            
        return None
    
    

    def fetch_news_by_dates(self, startDate: str, endDate: str) -> None:
        urls = generate_date_urls(startDate=startDate, endDate=endDate, logger=self.logger)
    
        # crawl page links of press release.
        news_links = asyncio.run(self._crawl_date_pages(urls=urls))
        
        # get the data dictionaries from press releases and save results to chromadb.
        asyncio.run(self._crawl_news_pages(urls=news_links))
        
        return