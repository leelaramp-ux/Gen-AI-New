from playwright.sync_api import sync_playwright, TimeoutError


def main():
    with sync_playwright() as p:

        # Run headed first so we can watch the browser.
        browser = p.chromium.launch(headless=False)

        page = browser.new_page()

        try:
            print("Opening Cricbuzz...")

            page.goto(
                "https://www.cricbuzz.com/",
                wait_until="domcontentloaded",
                timeout=30000
            )

            # This selector should be replaced with the selector
            # you find by inspecting the current Cricbuzz page.
            score = page.locator("YOUR_SCORE_SELECTOR").first

            print("Waiting for the live score...")

            # Wait for the actual element instead of using sleep().
            score.wait_for(
                state="visible",
                timeout=20000
            )

            score_text = score.inner_text().strip()

            if score_text:
                print("\nLive Score:")
                print(score_text)

                page.screenshot(
                    path="score.png",
                    full_page=True
                )

                print("\nScreenshot saved as score.png")

            else:
                print("No live score found.")

        except TimeoutError:
            print("No live match/score appeared within the expected time.")

            # Still save a screenshot so we can see the page state.
            page.screenshot(
                path="score.png",
                full_page=True
            )

        except Exception as e:
            print(f"Error: {e}")

        finally:
            browser.close()


if __name__ == "__main__":
    main()
    
