
import requests
from bs4 import BeautifulSoup

URL = "https://www.bbc.com/news"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/130.0.0.0 Safari/537.36"
    )
}

try:
    # Step 1: Fetch the webpage
    response = requests.get(
        URL,
        headers=headers,
        timeout=15
    )

    # Step 2: Check status before parsing
    response.raise_for_status()

    # Step 3: Parse the HTML
    soup = BeautifulSoup(response.text, "html.parser")

    # Step 4: Select the headline elements.
    # Verify this selector against the current BBC HTML.
    items = soup.select("h2")

    # Step 5: Clean the text and remove duplicates
    headlines = []
    seen = set()

    for item in items:
        headline = item.get_text(" ", strip=True)

        if headline and headline not in seen:
            headlines.append(headline)
            seen.add(headline)

        if len(headlines) == 5:
            break

    # Step 6: Print up to five headlines
    if headlines:
        for number, headline in enumerate(headlines, start=1):
            print(f"{number}. {headline}")

        if len(headlines) < 5:
            print(
                f"Only {len(headlines)} unique headlines found."
            )
    else:
        print("No headlines found. Check the HTML selector.")

except requests.exceptions.HTTPError as error:
    print(f"HTTP error: {error}")

except requests.exceptions.RequestException as error:
    print(f"Request failed: {error}")
