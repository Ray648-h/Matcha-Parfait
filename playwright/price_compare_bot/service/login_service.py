# service/login_service.py

from config.settings import TAOBAO_URL, XIANYU_URL, WAJUEJI_URL

class LoginService:
    def __init__(self, context):
        self.context = context

    # ===============================
    # 🔍 登录状态判断
    # ===============================
    def is_logged_in(self, page, name: str) -> bool:
        def _debug_page(message: str):
            print(f"[DEBUG] {message}")
            print(f"[DEBUG] url={page.url}")
            try:
                print(page.content()[:2000])
            except Exception as e:
                print(f"[DEBUG] 获取 page.content 失败: {e}")

        try:
            page.wait_for_load_state("networkidle")
            # 新增：等待 5 秒再判断，给页面状态稳定和缓存恢复时间
            page.wait_for_timeout(3000)

            if "login" in page.url:
                return False

            name_lower = name.lower()
            name_contains = lambda token: token in name_lower or token in name

            # =======================
            # 🟠 淘宝
            # =======================
            if name_contains("taobao") or name_contains("淘宝"):
                login_btn = page.locator("button:has-text('登录')")

                if login_btn.count() > 0:
                    return False

                return True

            # =======================
            # 🟠 闲鱼
            # =======================
            elif name_contains("xianyu") or name_contains("闲鱼"):
                nick = page.locator('[class^="nick"]')

                if nick.count() > 0:
                    try:
                        text = nick.first.inner_text().strip()
                        if text and text not in ["登录", "请登录"]:
                            return True
                    except Exception as e:
                        _debug_page(f"闲鱼获取昵称失败: {e}")
                        return False

                return False

            # =======================
            # 🟢 挖煤姬
            # =======================
            elif name_contains("meruki") or name_contains("挖煤姬"):
                login_link = page.locator("a.login:has-text('登录')")
                if login_link.count() > 0:
                    return False
                return True

            return False

        except Exception as e:
            print(f"检测登录状态出错: {e}")
            return False

    # ===============================
    # 🚀 登录流程（核心）
    # ===============================
    def login(self, url: str, name: str):
        page = self.context.new_page()
        print(f"\n🚀 打开{name}...")

        page.goto(url)

        # ✅ Step 1：当前是否已登录
        if self.is_logged_in(page, name):
            print(f"✅ {name} 已登录（自动恢复）")
            return page

        print(f"❌ 当前未登录，尝试使用本地数据恢复...")

        # ✅ Step 2：尝试用本地数据（关键）
        page.reload()
        page.wait_for_load_state("networkidle")

        if self.is_logged_in(page, name):
            print(f"✅ {name} 本地数据恢复成功")
            return page

        # ❗ Step 3：手动登录
        print(f"🔐 {name} 需要手动登录")
        input("👉 登录完成后按 Enter...")

        page.wait_for_load_state("networkidle")

        if self.is_logged_in(page, name):
            print(f"✅ {name} 登录成功（已保存）")
        else:
            print(f"❌ {name} 登录失败，请检查")

        return page

    # ===============================
    # 🌐 多站点
    # ===============================
    def login_all(self):
        from config.context import BrowserManager

        browser_manager = BrowserManager()

        sites = {
            "taobao": (browser_manager.launch_taobao, TAOBAO_URL, "淘宝"),
            "xianyu": (browser_manager.launch_xianyu, XIANYU_URL, "闲鱼"),
            "wajueji": (browser_manager.launch_wajueji, WAJUEJI_URL, "挖煤姬"),
        }

        result = {"contexts": {}}

        for key, (launcher, url, name) in sites.items():
            context = launcher()

            service = LoginService(context)
            page = service.login(url, name)

            result[key] = page
            result["contexts"][key] = context

        print("\n🎉 所有网站登录完成！")
        return result