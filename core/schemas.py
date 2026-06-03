from datetime import datetime
from pydantic import BaseModel


class StockArticle(BaseModel):
    title: str
    source: str
    published_date: datetime
    link: str
    summary: str
