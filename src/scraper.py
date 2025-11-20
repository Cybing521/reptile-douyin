import time
import random
import os
from datetime import datetime
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from src.utils import parse_douyin_time, is_target_comment

class DouyinScraper:
    def __init__(self, headless: bool = False, auth_file: str = "auth.json"):
        self.headless = headless
        self.auth_file = auth_file
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start(self):
        """启动浏览器"""
        self.playwright = sync_playwright().start()
        # 尝试使用本地 Chrome 浏览器，以规避"浏览器版本过低"的检测
        # 如果没有安装 Chrome，可以尝试改为 'msedge' 或删除 channel 参数(但可能回到版本过低问题)
        try:
            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                channel="chrome", 
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-infobars',
                ]
            )
        except Exception as e:
            print(f"启动本地 Chrome 失败，尝试使用默认 Chromium (可能仍会被检测): {e}")
            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                args=['--disable-blink-features=AutomationControlled']
            )

        # 加载状态（如果有）
        # 不再硬编码 User-Agent，让浏览器使用默认值，或者仅在必要时伪装
        context_args = {
            "viewport": {"width": 1280, "height": 720},
            # 移除硬编码的 User-Agent，使用浏览器默认的，通常更真实
        }
        
        if os.path.exists(self.auth_file):
            print(f"加载登录状态: {self.auth_file}")
            context_args["storage_state"] = self.auth_file
            
        self.context = self.browser.new_context(**context_args)
        
        self.page = self.context.new_page()
        
        # 注入更强的反检测脚本
        js_script = """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            window.chrome = { runtime: {} };
        """
        self.page.add_init_script(js_script)
        
        # 预加载首页
        print("正在加载抖音首页...")
        try:
            self.page.goto("https://www.douyin.com/")
        except Exception as e:
            print(f"首页加载异常 (可忽略): {e}")

    def manual_login(self):
        """手动登录并保存状态"""
        print("正在打开登录页...")
        # 如果当前已经在首页，刷新一下或者直接使用
        if "douyin.com" not in self.page.url:
            self.page.goto("https://www.douyin.com/")
            
        print("请在浏览器中手动完成登录（推荐扫码）。")
        print("登录完成后，请按回车键继续...")
        input()
        
        # 保存状态
        self.context.storage_state(path=self.auth_file)
        print(f"登录状态已保存至: {self.auth_file}")

    def stop(self):
        """关闭浏览器"""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def random_sleep(self, min_s: float = 1.5, max_s: float = 4.0):
        """随机延迟"""
        time.sleep(random.uniform(min_s, max_s))

    def search_and_filter(self, keyword: str):
        """搜索并应用时间筛选"""
        # 直接使用 URL 参数进行筛选，比点击 UI 更稳定
        # publish_time=7 表示一周内
        target_url = f"https://www.douyin.com/search/{keyword}?publish_time=7"
        
        print(f"正在搜索并筛选(一周内): {target_url}")
        
        try:
            self.page.goto(target_url)
            # 等待搜索结果加载（主要等待视频列表容器）
            # 这里的 selector 可能需要根据实际页面调整，先等待通用的视频链接
            # self.page.wait_for_selector('a[href*="/video/"]', timeout=15000) # 移除严格等待，防止超时
            self.random_sleep(3.0, 5.0) # 给足加载时间
            
        except Exception as e:
            print(f"搜索页面加载可能超时，尝试继续: {e}")

        # 旧的点击筛选逻辑已移除，改用 URL 参数更高效
        self.random_sleep()

    def get_video_links(self, max_count: int = 20) -> List[str]:
        """滚动并获取视频链接"""
        links = set()
        scroll_attempts = 0
        
        while len(links) < max_count and scroll_attempts < 10:
            # 尝试多种选择器来定位视频链接
            # 1. 通用规则: 包含 /video/ 的链接
            elements = self.page.locator('a[href*="/video/"]').all()
            
            # 2. 如果上面没找到，尝试找包含 modal_id 的链接 (搜索页常见结构)
            if not elements:
                 elements = self.page.locator('a[href*="modal_id="]').all()

            for el in elements:
                try:
                    href = el.get_attribute("href")
                    if href:
                        # 处理相对路径
                        if href.startswith("/"):
                            href = "https://www.douyin.com" + href
                        # 简单去重
                        if "/video/" in href or "modal_id=" in href:
                             # 对于 modal_id 链接，通常已经是完整的或需要进一步处理
                             # 这里先统一收集
                            links.add(href)
                except:
                    pass
            
            print(f"当前已发现 {len(links)} 个视频...")
            
            if len(links) >= max_count:
                break

            # 滚动
            self.page.mouse.wheel(0, 3000) # 加大滚动距离
            self.random_sleep(1.5, 3.0)
            scroll_attempts += 1
            
        return list(links)[:max_count]

    def parse_video_comments(self, video_url: str, keywords: List[str]) -> List[Dict[str, Any]]:
        """进入视频页采集评论"""
        results = []
        try:
            print(f"正在处理视频: {video_url}")
            # 新开页面处理，防止干扰搜索列表
            new_page = self.context.new_page()
            new_page.goto(video_url)
            new_page.wait_for_load_state("domcontentloaded")
            self.random_sleep(2.0, 3.0)

            # 滚动以加载评论
            new_page.mouse.wheel(0, 2000)
            self.random_sleep(1.0, 2.0)
            
            # 尝试点击 "暂无评论" 或 "全部评论" 来展开（如果有折叠）
            try:
                # 这是一个常见模式，但不一定存在
                new_page.get_by_text("全部评论").click(timeout=2000)
            except:
                pass

            # 提取评论
            # 策略：获取所有可见的文本块，然后过滤
            # 在没有确切 Selector 的情况下，我们遍历页面上的文本元素
            
            # 优化: 直接使用 locator 过滤包含关键词的元素
            for kw in keywords:
                try:
                    # 查找包含关键词的元素
                    found_elements = new_page.get_by_text(kw).all()
                    for el in found_elements:
                        try:
                            if not el.is_visible():
                                continue
                                
                            text = el.inner_text()
                            if len(text) > 100: # 忽略过长的文本块（可能是整个区域）
                                continue
                                
                            # 去重
                            if any(r['content'] == text for r in results):
                                continue

                            results.append({
                                "video_url": video_url,
                                "title": new_page.title(),
                                "content": text.strip(),
                                "matched_keyword": kw,
                                "author": "Unknown", # 难以在无 Selector 下获取
                                "publish_time": "Unknown", # 难以在无 Selector 下获取
                                "scrape_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            })
                        except:
                            continue
                except:
                    pass
            
            if not results:
                 print(f"  - 未在视频 {video_url} 中找到包含关键词的评论。")
            else:
                 print(f"  - 找到 {len(results)} 条潜在意向评论！")

            new_page.close()
            
        except Exception as e:
            print(f"处理视频出错: {e}")
            try:
                new_page.close()
            except:
                pass
        
        return results
