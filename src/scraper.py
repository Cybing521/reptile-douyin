import time
import random
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from src.utils import parse_douyin_time, is_target_comment

class DouyinScraper:
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start(self):
        """启动浏览器"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']  # 规避部分检测
        )
        # 加载状态（如果有）
        if False: # TODO: 实现状态加载逻辑
            pass
        else:
            self.context = self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            )
        
        self.page = self.context.new_page()
        # 添加反检测脚本
        self.page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

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
        print(f"正在搜索: {keyword}")
        self.page.goto("https://www.douyin.com/")
        self.page.wait_for_load_state("networkidle")
        
        # 搜索框
        search_input = self.page.locator('input[type="search"]')
        # 如果首页没有搜索框（有时是登录页），尝试直接访问搜索URL
        if not search_input.is_visible():
             self.page.goto(f"https://www.douyin.com/search/{keyword}")
        else:
            search_input.fill(keyword)
            self.random_sleep(0.5, 1.0)
            self.page.keyboard.press("Enter")
        
        self.page.wait_for_load_state("networkidle")
        self.random_sleep()

        # 筛选 - 这是一个假设的交互流程，实际DOM可能不同，需要根据实际情况调整
        # 通常会有 "筛选" 按钮，然后是 "发布时间"
        try:
            # 尝试点击筛选 (假设文本是 "筛选")
            filter_btn = self.page.get_by_text("筛选", exact=True)
            if filter_btn.is_visible():
                filter_btn.click()
                self.random_sleep(0.5, 1.0)
                
                # 点击 "一周内" 或 "一天内"
                # 这里使用 "一周内" 以确保覆盖3天
                time_filter = self.page.get_by_text("一周内")
                if time_filter.is_visible():
                    time_filter.click()
                    print("已应用时间筛选: 一周内")
                    self.random_sleep(2.0, 3.0)
                else:
                    print("未找到时间筛选选项")
            else:
                print("未找到筛选按钮，尝试继续...")
        except Exception as e:
            print(f"筛选操作失败: {e}")

    def get_video_links(self, max_count: int = 20) -> List[str]:
        """滚动并获取视频链接"""
        links = set()
        scroll_attempts = 0
        
        while len(links) < max_count and scroll_attempts < 10:
            # 获取当前可见的视频卡片链接
            # 抖音搜索结果通常是 a 标签，href 包含 /video/
            # 这是一个泛化的选择器
            elements = self.page.locator('a[href*="/video/"]').all()
            
            for el in elements:
                try:
                    href = el.get_attribute("href")
                    if href:
                        # 处理相对路径
                        if href.startswith("/"):
                            href = "https://www.douyin.com" + href
                        # 简单去重
                        if "/video/" in href:
                            links.add(href)
                except:
                    pass
            
            print(f"当前已发现 {len(links)} 个视频...")
            
            if len(links) >= max_count:
                break

            # 滚动
            self.page.mouse.wheel(0, 1000)
            self.random_sleep(1.0, 2.0)
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
            # 评论区通常在右侧或下方，尝试滚动页面
            new_page.mouse.wheel(0, 2000)
            self.random_sleep(1.0, 2.0)

            # 提取评论
            # 假设评论容器类名，实际需调试
            # 这里使用通用策略：查找包含文本的列表项
            
            # 尝试定位评论元素 (Douyin class names are obfuscated usually, e.g. 'comment-item')
            # We try to find elements that look like comments. 
            # Strategy: Find elements with text, filter by length/structure if possible.
            # For now, we will try a generic approach or assume we need to inspect DOM manually later.
            # Using a broad selector for demonstration in this 'blind' coding phase.
            
            # 模拟：获取所有文本内容较长的 div/span，假设是评论
            # 在真实项目中，这里需要具体的 CSS Selector，例如 '.comment-content'
            # 由于无法实时查看 DOM，我将使用一个假设的选择器，并在注释中说明需要替换
            
            # TODO: 替换为真实的评论选择器
            comment_elements = new_page.locator('div[class*="comment-text"]').all() 
            if not comment_elements:
                 # Fallback: try finding elements with text that are likely comments
                 pass

            # 模拟提取 (因为没有真实 DOM，这里写逻辑框架)
            # 实际运行时，如果选择器不对，将采集不到数据
            
            # 获取视频标题作为元数据
            title = new_page.title()

            # 假设我们能获取到评论文本
            # 为了演示，我们假设页面上所有可见文本都可能是评论 (这很粗糙，但符合盲写逻辑)
            # 更好的方式是等待用户反馈选择器
            
            # 这里我们只做逻辑框架：
            # for el in comment_elements:
            #    text = el.inner_text()
            #    ...
            
            print("警告: 由于未提供具体的 CSS 选择器，评论提取逻辑仅为框架。请根据实际 DOM 更新 'src/scraper.py' 中的选择器。")

            new_page.close()
            
        except Exception as e:
            print(f"处理视频出错: {e}")
            try:
                new_page.close()
            except:
                pass
        
        return results
