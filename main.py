from pprint import pprint
import asyncio
import json, re

from tools.webCrawler import NewsSummarizer 


def main():
    
    # declare classes.
    summarizer = NewsSummarizer()
    
    # generate urls by date range.
    startDate = "20251130"
    endDate = "20251130"
    urls = summarizer.generate_date_urls(startDate=startDate, endDate=endDate)
    print(f"Generated urls by dates: {urls}")
    
    # crawl page links of press release.
    news_links = asyncio.run(summarizer.crawl_date_pages(urls=urls))
    
    # get the data dictionaries from press releases.
    dicts = asyncio.run(summarizer.crawl_news_pages(urls=news_links))
    

if __name__ == "__main__":
    main()
