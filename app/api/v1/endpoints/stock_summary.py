import urllib.request
from bs4 import BeautifulSoup
import os
from langchain_community.utilities import BingSearchAPIWrapper
from langchain_openai import ChatOpenAI
from langchain.docstore.document import Document
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
from pydantic import BaseModel
from typing import Optional
import concurrent.futures
import re
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from cachetools import cached, TTLCache
from hashlib import sha256
from typing import Tuple

from dotenv import load_dotenv

from app.config.logs import MyLogger

my_logger = MyLogger()
logger = my_logger.get_logger()

load_dotenv()
router = APIRouter()

# Setting up Bing search URL
BING_SUBSCRIPTION_KEY = os.getenv("BING_SUBSCRIPTION_KEY")
os.environ["BING_SEARCH_URL"] = "https://api.bing.microsoft.com/v7.0/search"


class SummarizerRequest(BaseModel):
    """Data class for summarizer API input"""

    stock_name: str


class SummarizerOutput(BaseModel):
    """Data class for summarizer API output"""

    summary: str
    token_count: int


class SummarizerInput(BaseModel):
    """Data class for summarizer chain input"""

    query: str
    system_prompt: Optional[str] = None


def hash_request(txt, stock_name) -> Tuple:
    # Extract hashable attributes from the request and combine them into a tuple
    hashable_attributes = stock_name
    # Convert the tuple into a hashable representation using SHA-256
    print("hashing completed")
    return sha256(str(hashable_attributes).encode()).hexdigest()


@cached(cache=TTLCache(maxsize=512, ttl=6000), key=hash_request)
def generate_summary_openai(
    txt: str, stock_name: str, temperature: float = 0.2
) -> SummarizerOutput:
    """Generate summary using OpenAI model"""
    # summary = f"Unable to fetch summary for: {stock_name}"
    # try:
    logger.info(f"stock_summary api: Summarizing news for : {stock_name}")
    llm = ChatOpenAI(temperature=temperature, model_name="gpt-3.5-turbo", request_timeout=60)
    text_splitter = CharacterTextSplitter()
    texts = text_splitter.split_text(txt)
    docs = [Document(page_content=t) for t in texts]
    system_prompt_template = """You are a financial analyst. Your job is to summarize given news articles for given stock. If numerical figures are present in news, comment on those as well. Return output string having details stock summary. GIve at least 200 words summary. Stock for which to generate summary is: {stock_name}."""
    prompt = PromptTemplate.from_template(system_prompt_template)
    chain = load_summarize_chain(
        llm, chain_type="stuff", prompt=prompt, document_variable_name="stock_name"
    )
    summary = chain.run(docs)
    # except Exception as e:
    #     logger.error(f"stock_summary api: Error while Summarizing: {e}")
    output = SummarizerOutput(summary=summary, token_count=1)
    return output


bing_cache = TTLCache(maxsize=512, ttl=6000)


@cached(cache=bing_cache)
def get_bing_result(stock_name, no_news) -> list:
    """Get Bing search results"""
    bing_result = []
    try:
        logger.info(f"stock_summary api: Getting bing results for : {stock_name}")
        search = BingSearchAPIWrapper()
        # bing_result = search.results(
        #     f"{stock_name} stock",
        #     no_news,
        # )

        bing_result = search.results(
            f"{stock_name} company profile - recent-events",
            no_news,
        )
    except Exception as e:
        logger.error(f"stock_summary api: Error while fetching bing results: {e}")
    return bing_result


@cached(cache=TTLCache(maxsize=512, ttl=6000))
def scrap_webpage(web_url) -> str:
    """Scrape webpage content"""
    logger.info(f"stock_summary api: scraping webpage: {web_url}")
    if "www.nseindia.com" in web_url or "www.bseindia.com" in web_url:
        return ""
    else:
        all_content = ""
        try:
            with urllib.request.urlopen(web_url, timeout=8) as webpage:
                content = webpage.read().decode("utf-8")

            soup = BeautifulSoup(content, "html.parser")
            paragraphs = soup.find_all("p")

            for p in paragraphs:
                all_content += (
                    p.get_text()
                    .strip()
                    .replace("\n", "")
                    .replace("\t", "")
                    .replace("\r", "")
                )

        except Exception as e:
            logger.error(f"stock_summary api: Error while in scrap_webpage: {e}")
        return all_content


def collect_news(bing_result) -> str:
    """Collect news content from Bing search results"""
    stock_news = ""
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(scrap_webpage, page["link"]) for page in bing_result]
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                stock_news += "Different article:  "
                stock_news += result
            except Exception as e:
                logger.error(f"stock_summary api: Error while collecting news: {e}")
    logger.info("stock_summary api: All news gathered")
    return stock_news


def clean_text(txt):
    txt = txt.replace("<b>", "")
    txt = txt.replace("</b>", "")
    txt = txt.replace("&amp;", "")
    txt = txt.replace("...", "")
    txt = re.sub(" +", " ", txt)
    return txt


def get_sources(bing_result):
    sources = []
    for i in bing_result:
        curr = {}
        curr["Headline"] = clean_text(i["title"])
        curr["Link"] = i["link"]
        sources.append(curr)
    return sources


@router.post("/stock_summary/{stock_name}")
async def get_stock_news(request: SummarizerRequest) -> JSONResponse:
    """API endpoint to get stock news summary"""
    stock_name = request.stock_name
    try:
        # Getting Bing search results
        bing_result = get_bing_result(stock_name, no_news=7)

        # bing_result in bing_cache.values()

        if len(bing_result) == 0:
            raise HTTPException(
                status_code=400, detail="Stock summary not available for selected stock"
            )

        # Collecting news content
        stock_news_all = collect_news(bing_result)

        if not stock_news_all:
            raise HTTPException(
                status_code=400, detail="Stock summary not available for selected stock"
            )
        # sending just 8k characters
        if len(stock_news_all) > 8000:
            stock_news_all = stock_news_all[:8000]
        # Generating summary using OpenAI
        summarized_content = generate_summary_openai(
            txt=stock_news_all, stock_name=stock_name
        )
        stock_summ = summarized_content.summary

        sources = get_sources(bing_result)

        response = {
            "stock_name": stock_name,
            "stock_summary": stock_summ,
            "sources": sources,
        }
        return JSONResponse(content=response, status_code=200)
    except Exception as e:
        logger.error(f"Error occurred in stock_summary api endpoint: {e}")
        raise HTTPException(status_code=400, detail=str(e))
