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

from fastapi import APIRouter
from dotenv import load_dotenv

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


def generate_summary_openai(
    txt: str, stock_name: str, temperature: float = 0.2
) -> SummarizerOutput:
    """Generate summary using OpenAI model"""
    summary = f"Unable to fetch summary for: {stock_name}"
    try:
        print(f"Summarizing news for : {stock_name}")
        llm = ChatOpenAI(
            temperature=temperature, model_name="gpt-4", request_timeout=60
        )
        text_splitter = CharacterTextSplitter()
        texts = text_splitter.split_text(txt)
        docs = [Document(page_content=t) for t in texts]
        system_prompt_template = """You are a financial analyst. Your job is to summarize given news articles for given stock. Return output string having details stock summary. Stock for which to generate summary is: {stock_name}."""
        prompt = PromptTemplate.from_template(system_prompt_template)
        chain = load_summarize_chain(
            llm, chain_type="stuff", prompt=prompt, document_variable_name="stock_name"
        )
        summary = chain.run(docs)
    except Exception as e:
        print(f"Error: {e}")
    output = SummarizerOutput(summary=summary, token_count=1)
    return output


def get_bing_result(stock_name, no_news) -> list:
    """Get Bing search results"""
    bing_result = []
    try:
        print(f"Getting bing results for : {stock_name}")
        search = BingSearchAPIWrapper()
        bing_result = search.results(f"{stock_name} stock", no_news)
    except Exception as e:
        print(e)
    return bing_result


def scrap_webpage(web_url) -> str:
    """Scrape webpage content"""
    print(f"scraping webpage: {web_url}")
    if "www.nseindia.com" in web_url or "www.bseindia.com" in web_url:
        return ""
    else:
        all_content = ""
        try:
            with urllib.request.urlopen(web_url, timeout=15) as webpage:
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

        except urllib.error.URLError as e:
            print(f"Error fetching content: {e}")
        return all_content


def collect_news(bing_result) -> str:
    """Collect news content from Bing search results"""
    stock_news = ""
    for page in bing_result:
        stock_news += "Different article:  "
        stock_news += scrap_webpage(page["link"])
    print("All news gathered")
    return stock_news


@router.post("/stock_summary/{stock_name}")
async def get_stock_news(request: SummarizerRequest) -> dict:
    """API endpoint to get stock news summary"""
    stock_name = request.stock_name
    try:
        # Getting Bing search results
        bing_result = get_bing_result(stock_name, no_news=10)

        # Collecting news content
        stock_news_all = collect_news(bing_result)

        # Generating summary using OpenAI
        summarized_content = generate_summary_openai(
            txt=stock_news_all, stock_name=stock_name
        )
        stock_summ = summarized_content.summary

        return {"stock_name": stock_name, "stock_summary": stock_summ}
    except Exception as e:
        return {"error": str(e)}
