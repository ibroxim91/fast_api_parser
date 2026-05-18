from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel
from parser import AgodaHotelScraper

app = FastAPI()

class ScrapeRequest(BaseModel):
    hotel_name: str
    region_name: Optional[str]

@app.post("/scrape")
async def scrape(request: ScrapeRequest):
    scraper = AgodaHotelScraper(request.hotel_name, region_name=request.region_name)
    hotel_data = await scraper.run()
    return {"hotel_name": request.hotel_name, "hotel_data": hotel_data}
