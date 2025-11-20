import os
import sys
from datetime import datetime

# 添加项目根目录到 path，以便导入 src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scraper import DouyinScraper
from src.utils import save_to_csv, save_to_json

def main():
    KEYWORDS = ["复刻台球杆"]
    INTENT_KEYWORDS = ["怎么买", "价格", "多少钱", "求购", "带价"]
    OUTPUT_CSV = os.path.join("data", "douyin_comments.csv")
    OUTPUT_JSON = os.path.join("data", "douyin_comments.json")
    
    print("=== 抖音评论采集器启动 ===")
    print(f"目标话题: {KEYWORDS}")
    print(f"意向关键词: {INTENT_KEYWORDS}")
    
    scraper = DouyinScraper(headless=False) # 首次运行建议 False 以便观察和登录
    
    try:
        scraper.start()
        
        # 检查是否需要登录
        # 如果没有 auth.json 或者用户主动要求登录，可以在这里处理
        # 这里做一个简单的逻辑：如果 auth.json 不存在，提示登录
        if not os.path.exists(scraper.auth_file):
            print("检测到未登录状态。")
            choice = input("是否现在进行手动登录？(y/n): ").strip().lower()
            if choice == 'y':
                scraper.manual_login()
            else:
                print("将尝试以未登录访客模式继续（可能会受限）...")

        # 1. 搜索与筛选
        scraper.search_and_filter(KEYWORDS[0])
        
        # 2. 获取视频列表
        video_links = scraper.get_video_links(max_count=10) # 测试阶段限制数量
        print(f"获取到 {len(video_links)} 个视频链接")
        
        all_data = []
        
        # 3. 遍历视频采集评论
        for link in video_links:
            comments = scraper.parse_video_comments(link, INTENT_KEYWORDS)
            if comments:
                all_data.extend(comments)
                # 实时保存，防止崩溃丢失
                save_to_csv(comments, OUTPUT_CSV)
                save_to_json(comments, OUTPUT_JSON)
        
        print(f"采集完成，共获取 {len(all_data)} 条有效评论。")
        print(f"结果已保存至: {OUTPUT_CSV} 和 {OUTPUT_JSON}")
        
    except Exception as e:
        print(f"发生未捕获异常: {e}")
    finally:
        print("正在关闭浏览器...")
        scraper.stop()
        print("程序结束。")

if __name__ == "__main__":
    main()
