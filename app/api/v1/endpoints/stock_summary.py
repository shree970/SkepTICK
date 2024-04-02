'''This code is used to summarise news articles about a stock.
This is fastapi API that will:
1. Read the stock names from "stock_names" from mongoDB
2. Use langchain agents to search for stock information, and news articles about the stock
3. Run summmary chain to summarise the news articles
4. Create the output format with dict["stock_name": str, "stock_info": str, "news_summary": str, "news_articles": list[str]]
'''

from fastapi import APIRouter
from pydantic import BaseModel

