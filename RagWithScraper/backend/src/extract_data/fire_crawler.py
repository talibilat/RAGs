import os
import json
from firecrawl import FirecrawlApp
from pathlib import Path
import time
import dotenv
import sys

dotenv.load_dotenv()

# Add parent directory to sys.path to allow relative imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import setup_logger

# Set up logger
logger = setup_logger(name="fire_crawler", log_to_file=True)

def run_crawler():
    """
    Run the web crawler and store the results in data folder
    Returns the path to the crawl results file if successful, None otherwise
    """
    # Set up data directories
    data_dir = Path("data")
    raw_data_dir = data_dir / "raw"
    
    # Create directories if they don't exist
    data_dir.mkdir(exist_ok=True)
    raw_data_dir.mkdir(exist_ok=True)
    
    logger.info("Starting web scraping process")
    logger.info(f"Raw data will be stored in: {raw_data_dir.absolute()}")
    
    # Get API key from environment
    api_key = os.getenv('FIRECRAWL_API_KEY')
    if not api_key:
        logger.error("FIRECRAWL_API_KEY not found in environment variables")
        return None
    
    app = FirecrawlApp(api_key=api_key)
    logger.info("FireCrawl app initialized")
    
    # Target URL to crawl
    target_url = 'https://joinvoy.zendesk.com/hc/en-gb'
    logger.info(f"Starting crawl for target URL: {target_url}")
    
    # Generate timestamp for this crawl
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    crawl_results_path = raw_data_dir / f"crawl_results_{timestamp}.json"
    crawl_status_path = raw_data_dir / f"crawl_status_{timestamp}.json"
    
    # Crawl a website:
    start_time = time.time()
    try:
        crawl_status = app.crawl_url(
            target_url, 
            params={
                'limit': 100, 
                'scrapeOptions': {'formats': ['markdown', 'html']}
            },
            poll_interval=30
        )
        
        # Save the crawl status response
        with open(crawl_status_path, "w") as f:
            json.dump(crawl_status, f, indent=2)
        
        logger.info(f"Saved crawl status to: {crawl_status_path}")
        
        crawl_time = time.time() - start_time
        logger.info(f"Crawl completed in {crawl_time:.2f} seconds with status: {crawl_status.get('status')}")
               
    except Exception as e:
        logger.error(f"Error during crawling: {e}")
        return None
    

if __name__ == "__main__":
    crawl_file = run_crawler()
    
    if crawl_file:
        logger.info(f"Crawling completed successfully. Results saved to: {crawl_file}")
        logger.info(f"Run the FAQ processor to extract FAQ content from the crawl results")
    else:
        logger.error("Crawling failed. Check logs for details")
