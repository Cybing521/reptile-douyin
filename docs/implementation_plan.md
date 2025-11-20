# 实施计划 - 抖音评论采集器

## 目标描述
开发一个基于 Python 和 Playwright 的自动化脚本，用于采集抖音网页版上关于“复刻台球杆”视频的评论。脚本将筛选过去3天内发布的视频，并提取包含购买意向关键词（如“怎么买”、“价格”）的评论。

## 用户审查要求
> [!IMPORTANT]
> **合规性声明**: 本项目严格遵守法律法规。仅采集公开数据，不使用任何黑客手段。
> **反爬虫风险**: 抖音的反爬虫机制非常严格。脚本将使用浏览器自动化来模拟真实用户，但仍存在 IP 被封禁或需要人工介入验证码的风险。建议不要长时间高频运行。

## 拟议变更

### 目录结构
严格遵循以下结构：
- `.agent/`: 规则与任务
- `docs/`: 文档
- `src/`: 源代码
- `data/`: 数据输出

### 新建文件

#### [NEW] [src/main.py](file:///g:/reptile/src/main.py)
- 程序的入口点。
- 负责编排整个采集流程：初始化 -> 搜索 -> 遍历视频 -> 提取评论 -> 保存数据。

#### [NEW] [src/scraper.py](file:///g:/reptile/src/scraper.py)
- 包含 `DouyinScraper` 类。
- 封装 Playwright 的操作：
    - `start_browser()`: 启动浏览器。
    - `search_keyword(keyword)`: 执行搜索。
    - `filter_time_range()`: 应用时间筛选。
    - `get_video_links()`: 获取视频列表。
    - `parse_comments(video_url)`: 进入视频页并提取评论。

#### [NEW] [src/utils.py](file:///g:/reptile/src/utils.py)
- 工具函数：
    - `parse_timestamp(time_str)`: 解析抖音的时间格式（如 "2天前", "刚刚"）。
    - `is_target_comment(text)`: 检查是否包含关键词。
    - `save_to_csv(data)`: 数据持久化。

#### [NEW] [requirements.txt](file:///g:/reptile/requirements.txt)
- 依赖列表：
    - `playwright`
    - `pandas`

## 验证计划

### 自动化测试
1.  **工具函数测试**:
    - 运行 `python -m unittest src/tests/test_utils.py` (可选) 来验证时间解析和关键词匹配逻辑。

### 手动验证
1.  **启动测试**: 运行 `python src/main.py`。
2.  **观察浏览器**:
    - 确认浏览器是否成功启动并加载抖音首页。
    - 确认是否自动输入了“复刻台球杆”并点击搜索。
    - 确认是否点击了“发布时间”筛选。
3.  **数据检查**:
    - 脚本运行结束后，检查 `data/douyin_comments.csv`。
    - 确认 CSV 中是否有数据。
    - 确认数据中的评论是否确实包含关键词。
    - 确认视频发布时间是否在最近3天内。
