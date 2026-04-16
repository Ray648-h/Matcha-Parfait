from playwright.sync_api import sync_playwright


class BrowserManager:
    def __init__(self):
        self.playwright = sync_playwright().start()

    def _launch(self, user_data_dir: str):
        """统一持久化浏览器启动"""
        return self.playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            args=[
                "--start-maximized",
                "--disable-blink-features=AutomationControlled"
            ]
        )

    def launch_taobao(self):
        return self._launch("user_data/taobao")

    def launch_xianyu(self):
        return self._launch("user_data/xianyu")

    def launch_wajueji(self):
        return self._launch("user_data/wajueji")