from services.scraper import scrape_treccani, scrape_treccani_multiple

if __name__ == '__main__':
  print(scrape_treccani("zotico").model_dump())