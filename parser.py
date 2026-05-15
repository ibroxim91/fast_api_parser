# import time

import random

from playwright.async_api import async_playwright
# import json
# from rapidfuzz import fuzz
USER_AGENTS = [
    # Windows Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",

    # Windows Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",

    # MacOS Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Safari/605.1.15",

    # Linux Chrome
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",

    # Android Chrome
    "Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36",

    # iPhone Safari
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile Safari/605.1.15",
]


class AgodaHotelScraper:
    """Agoda veb-saytidan otel ma'lumotlarini to'plash"""

    def __init__(self, query: str):
        self.query = query
        self.page = None
        self.browser = None
        self.context = None
        self.hotel_data = {
            "name": None,
            "url": None,
            "rating": None,
            "amenities": [],
            "images": [],
            "nearby": [],
            "rooms": []
        }

    async def launch_browser(self):
        p = await async_playwright().start()
        self.browser = await p.chromium.launch(headless=True)
        ua = random.choice(USER_AGENTS)
        self.context = await self.browser.new_context(
            user_agent=ua,
            viewport={"width": 1280, "height": 800},
            locale="ru-RU"
        )
        self.page = await self.context.new_page()

    async def search_hotel(self):
        await self.page.goto("https://www.agoda.com/ru-ru/", timeout=120000)
        search_input = self.page.locator('input[data-selenium="textInput"]')
        await search_input.click()
        await search_input.fill("")
        await search_input.type(self.query, delay=200)
        await self.page.locator('span[data-testid="break-down-highlight-text"]').first.wait_for(timeout=10000)
        first_span = self.page.locator('span[data-testid="break-down-highlight-text"]').first
        await first_span.click()
        search_button = self.page.locator('button[data-element-name="search-button"]')
        await search_button.click()
        await self.page.wait_for_load_state("domcontentloaded")
        matched = await self.choose_matching_hotel()
        if not matched:
            return False
        return True


    

    async def choose_matching_hotel(self):
        """Topilgan birinchi 3 ta hotelni tekshirib, queryga mosini tanlash"""
        await self.page.locator('a[data-testid="property-name-link"]').first.wait_for(timeout=70000)
        hotels = await self.page.locator('a[data-testid="property-name-link"]').all()
        for hotel in hotels[:3]:
            # Locator emas, element handle olish
            h3_handle = await hotel.element_handle()

            if h3_handle:
                h3 = await h3_handle.query_selector("h3")
                if h3:
                    hotel_name = (await h3.inner_text()).strip()
                    print()
                    print("hotel_name.lower() : ", hotel_name.lower(), " self.query.lower() " , self.query.lower()) 
                    print()
                    if self.query.lower() in hotel_name.lower() or hotel_name.lower() in self.query.lower():
                        self.hotel_data["name"] = hotel_name
                        hotel_link = await hotel.get_attribute("href")
                        self.hotel_data["url"] = f"https://www.agoda.com{hotel_link}"
                        return True
        return False



   
    async def navigate_to_detail(self):
        await self.page.goto(self.hotel_data["url"], timeout=120000, wait_until="domcontentloaded")

    async def extract_rooms(self):
        """Hotel sahifasidan room name'larni olish"""
        print("Room name'larni olishga harakat qilinmoqda...")
        try:
            for step in range(3):  # 3 marta scroll
                await self.page.evaluate("window.scrollBy(0, window.innerHeight * 2)")
                await self.page.wait_for_timeout(2000)  # yuklanishi uchun kutish
            # Room name divlarini kutish
            await self.page.locator("div[data-testid='room-name']").first.wait_for(timeout=10000)
            items = await self.page.query_selector_all("div[data-testid='room-name']")
            for item in items:
                h4 = await item.query_selector("h4")
                if h4:
                    text = (await h4.inner_text()).strip()
                    self.hotel_data.get("rooms", []).append(text)
        except Exception as e:
            print(f"Room name olishda xatolik: {e}")

    
    async def extract_rating(self):
        print("Ratingni olishga harakat qilinmoqda...")
        try:
            await self.page.evaluate("window.scrollBy(0, window.innerHeight * 2)")
            await self.page.wait_for_timeout(4000)
            await self.page.locator('div[data-selenium="mosaic-hotel-rating"]').first.wait_for(timeout=10000)
            rating_div = await self.page.query_selector('div[data-selenium="mosaic-hotel-rating"]')
            if rating_div:
                full_text = (await rating_div.inner_text()).strip()
                for line in full_text.split("\n"):
                    if "Количество звезд" in line:
                        self.hotel_data["rating"] = line.strip()
                        break
        except Exception as e:
            print(f"Rating olishda xatolik: {e}")
            self.hotel_data["rating"] =  "3"

    async def extract_amenities(self):
        print("Amenitiesni olishga harakat qilinmoqda...")
        try:
            await self.page.locator("div[data-element-name='atf-top-amenities-item']").first.wait_for(timeout=10000)
            items = await self.page.query_selector_all("div[data-element-name='atf-top-amenities-item']")
            for item in items:
                text = await item.query_selector("p")
                if text:
                    self.hotel_data["amenities"].append((await text.inner_text()).strip())
        except Exception as e:
            print(f"Amenities olishda xatolik: {e}")

    async def extract_images(self):
        print("Rasmlarni olishga harakat qilinmoqda...")
        # await self.page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
        # await self.page.wait_for_timeout(5000)
        try:
            await self.page.locator("button[data-element-name='hotel-mosaic-tile'] img").first.wait_for(timeout=10000)
            items = await self.page.query_selector_all("button[data-element-name='hotel-mosaic-tile'] img")
            for item in items:
                src = await item.get_attribute("src")
                if src:
                    if src.startswith("//"):
                        src = "https:" + src
                    self.hotel_data["images"].append(src)
        except Exception as e:
            print(f"Rasm olishda xatolik: {e}")

    async def extract_nearby_locations(self):
        print("Yaqin-atrof locationlarni olishga harakat qilinmoqda...")
        await self.page.locator('div[data-element-name="nearby-location-box"]').first.wait_for(timeout=60000)
        poi_items = await self.page.query_selector_all('div[data-element-name="poi-image-tooltip-property-feature"]')
        for poi in poi_items:
            name_el = await poi.query_selector("span.kite-js-Typography")
            spans = await poi.query_selector_all("span")
            dist_el = spans[-1] if spans else None
            name = (await name_el.inner_text()).strip() if name_el else None
            dist = (await dist_el.inner_text()).strip() if dist_el else None
            if name and dist:
                self.hotel_data["nearby"].append({"name": name, "distance": dist})

    async def save_to_json(self):
        # with open("agoda_detail.json", "w", encoding="utf-8") as f:
        #     json.dump(self.hotel_data, f, ensure_ascii=False, indent=4)
        await self.browser.close()
        return self.hotel_data

    async def run(self):
        await self.launch_browser()
        hotel = await self.search_hotel()
        if not hotel:
            print("Hotel topilmadi, jarayon to'xtatildi.")
            await self.browser.close()
            return   self.hotel_data
        await self.navigate_to_detail()
        await self.extract_rating()
        await self.extract_amenities()
        await self.extract_images()
        await self.extract_rooms()
        await self.extract_nearby_locations()
        data  = await self.save_to_json()
        return data 
