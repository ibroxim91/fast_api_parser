from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel
from parser import AgodaHotelScraper

app = FastAPI()

class ScrapeRequest(BaseModel):
    hotel_name: str
    region_name_uz: Optional[str]
    region_name_ru: Optional[str]
    country_name: Optional[str]
    destination: Optional[str] = None

@app.post("/scrape")
async def scrape(request: ScrapeRequest):
    scraper = AgodaHotelScraper(request.hotel_name, 
                                region_name_uz=request.region_name_uz,
                                  region_name_ru=request.region_name_ru,
                                    country_name=request.country_name,
                                    destination=request.destination)
    hotel_data = await scraper.run()
    return {"hotel_name": request.hotel_name, "hotel_data": hotel_data}
