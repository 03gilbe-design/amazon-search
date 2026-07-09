from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('file:///C:/Users/Gilberto Bizzo/Downloads/agent_animations_v3.html')
    page.wait_for_timeout(2000)  # Wait for animations to start
    page.screenshot(path='C:/Users/Gilberto Bizzo/Downloads/v3_screenshot.png', full_page=True)
    browser.close()
    print('Screenshot saved to C:/Users/Gilberto Bizzo/Downloads/v3_screenshot.png')
