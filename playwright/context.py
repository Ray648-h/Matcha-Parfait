from playwright.sync_api import sync_playwright


class BrowserManager:
    def __init__(self):
        self.playwright = sync_playwright().start()

    def launch_taobao(self):
        context = self.playwright.chromium.launch_persistent_context(
            user_data_dir="user_data/taobao",
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ]
        )

        context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        })
        """)

        return context

    def launch_xianyu(self):
        return self.playwright.chromium.launch_persistent_context(
            user_data_dir="user_data/xianyu",
            headless=False,
            args=["--start-maximized"]
        )

    def launch_wajueji(self):
        return self.playwright.chromium.launch_persistent_context(
            user_data_dir="user_data/wajueji",
            headless=False,
            args=["--start-maximized"]
        )