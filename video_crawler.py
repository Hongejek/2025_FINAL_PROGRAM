import re
import requests
import time
import random
import json
import csv
import os
from bs4 import BeautifulSoup

# ============================================================================
# Headers管理类 - 模拟真实浏览器行为，避免风控
# ============================================================================
class HeadersManager:
    """Headers管理类，模拟真实浏览器行为"""
    
    # 预定义的User-Agent列表
    USER_AGENTS = [
        # Chrome Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        
        # Chrome macOS
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        
        # Firefox
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0',
        
        # Safari
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    ]
    
    # 接受语言列表
    ACCEPT_LANGUAGES = [
        'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'zh-CN,zh;q=0.9',
        'zh-CN,zh;q=0.9,en;q=0.8',
        'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
    ]
    
    def __init__(self):
        self.session_headers = self._generate_base_headers()
        self.last_ua_change = time.time()
        self.ua_change_interval = 3600  # 每小时更换一次UA
        
    def _generate_base_headers(self):
        """生成基础Headers"""
        return {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': random.choice(self.ACCEPT_LANGUAGES),
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'DNT': '1',
            'Priority': 'u=0, i',
        }
    
    def get_headers(self, referer=None):
        """获取完整的Headers"""
        headers = self.session_headers.copy()
        
        # 定期更换User-Agent
        if time.time() - self.last_ua_change > self.ua_change_interval:
            headers['User-Agent'] = random.choice(self.USER_AGENTS)
            self.last_ua_change = time.time()
        else:
            headers['User-Agent'] = self.session_headers.get('User-Agent', 
                random.choice(self.USER_AGENTS))
        
        # 设置Referer
        if referer:
            headers['Referer'] = referer
        else:
            headers['Referer'] = 'https://www.bilibili.com/'
        
        # 添加Host头
        headers['Host'] = 'www.bilibili.com'
        
        return headers
    
    def update_for_video(self, video_url):
        """为视频请求更新Headers"""
        headers = self.get_headers()
        headers['Referer'] = video_url
        
        # 视频页面可能有特定的Accept头
        headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        
        return headers

# ============================================================================
# 配置和全局变量
# ============================================================================
# 初始化Headers管理器
headers_manager = HeadersManager()

# 配置常量
CONFIG = {
    'REQUEST_DELAY': 2.0,           # 基础请求延迟（秒）
    'TIMEOUT': 20,                  # 请求超时时间（秒）
    'MAX_RETRIES': 3,               # 最大重试次数
    'MIN_CONTENT_LENGTH': 15000,    # 最小响应内容长度
}

# ============================================================================
# 工具函数
# ============================================================================
def write_error_log(message):
    """写入错误日志"""
    with open("video_errorlist.txt", "a", encoding='utf-8') as file:
        file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

def is_url(video_id_or_url):
    """判断是否为URL"""
    return video_id_or_url.startswith(("http://", "https://"))

def get_video_url(video_id_or_url):
    """获取完整的视频URL"""
    if is_url(video_id_or_url):
        return video_id_or_url
    else:
        # 清理可能的空格和换行符
        video_id = video_id_or_url.strip()
        return f"https://www.bilibili.com/video/{video_id}"

def format_timestamp(timestamp):
    """格式化时间戳为可读日期"""
    if timestamp and timestamp > 0:
        try:
            return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
        except:
            return str(timestamp)
    return ''

def check_anti_scraping(response):
    """检查是否触发反爬机制"""
    indicators = {
        '验证页面': ['验证', '安全验证', '人机验证', 'recaptcha'],
        '访问限制': ['访问受限', '频率过高', '请稍后再试'],
        '异常响应': ['异常访问', '非法请求'],
    }
    
    text = response.text.lower()
    
    for indicator, keywords in indicators.items():
        for keyword in keywords:
            if keyword.lower() in text:
                print(f"  检测到{indicator}: {keyword}")
                return True
    
    # 检查响应码
    if response.status_code in [403, 429, 503]:
        print(f"  异常状态码: {response.status_code}")
        return True
    
    return False

def handle_anti_scraping(url):
    """处理反爬机制"""
    print("检测到反爬机制，尝试以下方法：")
    
    # 1. 更换User-Agent
    print("  1. 更换User-Agent...")
    headers_manager.session_headers['User-Agent'] = random.choice(HeadersManager.USER_AGENTS)
    
    # 2. 增加延迟
    print("  2. 增加请求间隔...")
    time.sleep(random.uniform(10, 30))
    
    return False  # 返回是否成功绕过

# ============================================================================
# 请求处理函数
# ============================================================================
def make_request(url, retry_count=0):
    """发送请求，带有完整的Headers和重试机制"""
    try:
        # 获取动态Headers
        headers = headers_manager.update_for_video(url)
        
        # 随机延迟
        delay = CONFIG['REQUEST_DELAY'] + random.uniform(0, 1.0)
        time.sleep(delay)
        
        # 发送请求
        response = requests.get(
            url, 
            headers=headers,
            timeout=CONFIG['TIMEOUT'],
            allow_redirects=True,
            verify=True  # SSL验证
        )
        
        # 检查响应
        response.raise_for_status()
        
        # 检查是否触发反爬
        if check_anti_scraping(response):
            if retry_count < CONFIG['MAX_RETRIES'] - 1:
                handle_anti_scraping(url)
                return make_request(url, retry_count + 1)
            return None
        
        # 检查内容类型
        content_type = response.headers.get('Content-Type', '')
        if 'text/html' not in content_type:
            print(f"  警告: 非HTML响应: {content_type}")
            if retry_count < CONFIG['MAX_RETRIES'] - 1:
                return make_request(url, retry_count + 1)
            return None
        
        # 检查内容长度
        if len(response.text) < CONFIG['MIN_CONTENT_LENGTH']:
            print(f"  警告: 响应过短 ({len(response.text)} 字符)")
            if retry_count < CONFIG['MAX_RETRIES'] - 1:
                return make_request(url, retry_count + 1)
            return None
        
        return response
        
    except requests.exceptions.SSLError as e:
        print(f"  SSL错误: {e}")
        if retry_count < CONFIG['MAX_RETRIES'] - 1:
            return make_request(url, retry_count + 1)
        return None
        
    except requests.exceptions.Timeout as e:
        print(f"  请求超时: {e}")
        if retry_count < CONFIG['MAX_RETRIES'] - 1:
            # 超时后增加延迟
            time.sleep(5)
            return make_request(url, retry_count + 1)
        return None
        
    except requests.exceptions.TooManyRedirects as e:
        print(f"  重定向过多: {e}")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"  请求异常: {e}")
        if retry_count < CONFIG['MAX_RETRIES'] - 1:
            return make_request(url, retry_count + 1)
        return None

# ============================================================================
# 数据提取函数
# ============================================================================
def extract_video_data_from_script(initial_state_text):
    try:
        json_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', initial_state_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            data = json.loads(json_str)
            
            video_data = data.get('videoData', {})
            stat_data = video_data.get('stat', {})
            
            return {
                'title': video_data.get('title', ''),
                'bvid': video_data.get('bvid', ''),
                'aid': video_data.get('aid', ''),
                'author': video_data.get('owner', {}).get('name', ''),
                'author_id': video_data.get('owner', {}).get('mid', ''),
                'views': stat_data.get('view', 0),
                'danmaku': stat_data.get('danmaku', 0),
                'likes': stat_data.get('like', 0),
                'coins': stat_data.get('coin', 0),
                'favorites': stat_data.get('favorite', 0),
                'shares': stat_data.get('share', 0),
                'comments': stat_data.get('reply', 0),  # 新增：评论总数
                'duration': video_data.get('duration', 0),
                'pubdate': video_data.get('pubdate', 0),
                'desc': video_data.get('desc', ''),
                'tags': [tag.get('tag_name', '') for tag in video_data.get('tags', [])]
            }
    except json.JSONDecodeError as e:
        print(f"  JSON解析错误: {e}")
    except Exception as e:
        print(f"  数据提取错误: {e}")
    return None

def extract_data_with_regex(soup, url, index):
    """使用正则表达式提取数据（备用方法）"""
    try:
        # 查找脚本
        initial_state_script = soup.find("script", string=re.compile("window.__INITIAL_STATE__"))
        
        if not initial_state_script:
            print(f"  错误: 找不到包含 window.__INITIAL_STATE__ 的脚本")
            write_error_log(f"第{index}行视频找不到INITIAL_STATE脚本: {url}")
            return None
            
        initial_state_text = initial_state_script.string
        
        # 提取基本信息
        author_id_pattern = re.compile(r'"mid":(\d+)')
        video_aid_pattern = re.compile(r'"aid":(\d+)')
        video_duration_pattern = re.compile(r'"duration":(\d+)')
        
        author_id_match = author_id_pattern.search(initial_state_text)
        video_aid_match = video_aid_pattern.search(initial_state_text)
        video_duration_match = video_duration_pattern.search(initial_state_text)
        
        if not author_id_match:
            print(f"  错误: 无法提取作者ID")
            return None
        if not video_aid_match:
            print(f"  错误: 无法提取视频AID")
            return None
        if not video_duration_match:
            print(f"  错误: 无法提取视频时长")
            return None
            
        author_id = author_id_match.group(1)
        video_aid = video_aid_match.group(1)
        video_duration_raw = int(video_duration_match.group(1))
        video_duration = video_duration_raw - 2

        # 提取标题
        title_tag = soup.find("title")
        if title_tag:
            title_raw = title_tag.text
            title = re.sub(r"_哔哩哔哩_bilibili", "", title_raw).strip()
        else:
            title = "未找到标题"

        # 提取标签
        keywords_meta = soup.find("meta", itemprop="keywords")
        if keywords_meta and "content" in keywords_meta.attrs:
            keywords_content = keywords_meta["content"]
            content_without_title = keywords_content.replace(title + ',', '')
            keywords_list = content_without_title.split(',')
            tags = ",".join(keywords_list[:-4]) if len(keywords_list) > 4 else ""
        else:
            tags = ""

        # 提取描述信息
        desc_meta = soup.find("meta", itemprop="description")
        if not desc_meta or "content" not in desc_meta.attrs:
            print(f"  错误: 找不到描述信息")
            return None
            
        meta_description = desc_meta["content"]
        numbers = re.findall(
            r'[\s\S]*?视频播放量 (\d+)、弹幕量 (\d+)、点赞数 (\d+)、投硬币枚数 (\d+)、收藏人数 (\d+)、转发人数 (\d+)',
            meta_description)

        # 提取作者
        author_search = re.search(r"视频作者\s*([^,]+)", meta_description)
        if author_search:
            author = author_search.group(1).strip()
        else:
            author = "未找到作者"

        # 提取作者简介
        author_desc_pattern = re.compile(r'作者简介 (.+?),')
        author_desc_match = author_desc_pattern.search(meta_description)
        if author_desc_match:
            author_desc = author_desc_match.group(1)
        else:
            author_desc = "未找到作者简介"

        # 提取视频简介
        meta_parts = re.split(r',\s*', meta_description)
        if meta_parts:
            video_desc = meta_parts[0].strip()
        else:
            video_desc = "未找到视频简介"

        # 提取发布时间
        publish_date_meta = soup.find("meta", itemprop="uploadDate")
        publish_date = publish_date_meta["content"] if publish_date_meta and "content" in publish_date_meta.attrs else ""

        if numbers:
            views, danmaku, likes, coins, favorites, shares = [int(n) for n in numbers[0]]
            
            return {
                'title': title,
                'bvid': '',
                'aid': video_aid,
                'author': author,
                'author_id': author_id,
                'views': views,
                'danmaku': danmaku,
                'likes': likes,
                'coins': coins,
                'favorites': favorites,
                'shares': shares,
                'duration': video_duration,
                'pubdate': publish_date,
                'desc': video_desc,
                'tags': tags
            }
        else:
            print(f"  警告: 未找到统计数据")
            write_error_log(f"第{index}行视频未找到统计数据: {url}")
            return None
            
    except AttributeError as e:
        error_msg = f"第{index}行视频解析错误: {e}"
        print(f"  {error_msg}")
        write_error_log(error_msg)
        return None
    except Exception as e:
        error_msg = f"第{index}行视频发生错误: {e}"
        print(f"  {error_msg}")
        write_error_log(error_msg)
        return None

def sanitize_title_for_filename(title_raw):
    """将标题裁剪为3字并移除文件名非法字符"""
    title = (title_raw or "").strip() or "未命名"
    short = title[:3]  # 超过3个字只取前三个
    return re.sub(r'[\\\\/:*?"<>|]', "_", short)

def format_data_for_csv(data, url):
    """格式化数据为CSV行，返回(行数据, 标题)"""
    row = [
        data.get('title', ''),
        url,
        data.get('author', ''),
        data.get('author_id', ''),
        data.get('views', 0),
        data.get('danmaku', 0),
        data.get('likes', 0),
        data.get('coins', 0),
        data.get('favorites', 0),
        data.get('shares', 0),
        data.get('comments', 0),  # 新增：评论总数
        format_timestamp(data.get('pubdate', 0)),
        data.get('duration', 0),
        (data.get('desc', '')[:200] if data.get('desc') else ''),  # 截断描述
        '',
        ','.join(data.get('tags', [])[:5]) if isinstance(data.get('tags'), list) else data.get('tags', ''),
        data.get('aid', '')
    ]
    return row, data.get('title', '')

def save_csv_file(title, row):
    """按要求保存为单个CSV文件"""
    output_dir = os.path.join("data", "video")
    os.makedirs(output_dir, exist_ok=True)
    headers = [
        "标题", "链接", "up主", "up主id", "精确播放数", "历史累计弹幕数",
        "点赞数", "投硬币枚数", "收藏人数", "转发人数", "评论数",  # 新增列
        "发布时间", "视频时长(秒)", "视频简介", "作者简介", "标签", "视频aid"
    ]
    filename = f"{sanitize_title_for_filename(title)}_视频.csv"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerow(row)
    print(f"  已保存: {filepath}")

# ============================================================================
# 主处理函数
# ============================================================================
def process_video(video_id_or_url, index):
    """处理单个视频"""
    url = get_video_url(video_id_or_url)
    print(f"[{index}] 处理: {url}")
    
    # 发送请求
    response = make_request(url)
    if not response:
        write_error_log(f"请求失败: {url}")
        return None
    
    # 解析HTML
    soup = BeautifulSoup(response.text, "html.parser")
    
    # 检查是否被重定向到验证页面
    title = soup.find("title")
    if title and ("验证" in title.text or "安全验证" in title.text):
        print(f"  触发验证页面，需要人工干预")
        write_error_log(f"触发验证: {url}")
        return None
    
    # 方法1: 尝试JSON解析
    initial_state_script = soup.find("script", string=re.compile("window.__INITIAL_STATE__"))
    if initial_state_script:
        json_data = extract_video_data_from_script(initial_state_script.string)
        if json_data:
            print(f"  成功(JSON): {json_data.get('title', '')[:30]}...")
            return format_data_for_csv(json_data, url)
    
    # 方法2: 回退到正则提取
    print(f"  使用正则提取")
    regex_data = extract_data_with_regex(soup, url, index)
    if regex_data:
        print(f"  成功(正则): {regex_data.get('title', '')[:30]}...")
        return format_data_for_csv(regex_data, url)
    
    print(f"  失败: 无法提取数据")
    write_error_log(f"数据提取失败: {url}")
    return None

# ============================================================================
# 主函数
# ============================================================================
def main():
    """主函数"""
    input_file = "bv_list.txt"
    
    # 读取ID列表
    try:
        with open(input_file, "r", encoding='utf-8') as file:
            id_list = [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(f"错误: 找不到输入文件 {input_file}")
        return
    
    if not id_list:
        print("错误: 输入文件为空")
        return
    
    print(f"找到 {len(id_list)} 个视频ID")
    print(f"配置: 延迟={CONFIG['REQUEST_DELAY']}秒, 超时={CONFIG['TIMEOUT']}秒, 重试={CONFIG['MAX_RETRIES']}次")
    print("-" * 50)
    
    # 处理每个视频并单独保存CSV
    success_count = 0
    start_time = time.time()
    
    for idx, video_id in enumerate(id_list, 1):
        result = process_video(video_id, idx)
        if result:
            row_data, title = result
            save_csv_file(title, row_data)
            success_count += 1
        
        # 显示进度
        if idx % 10 == 0 or idx == len(id_list):
            elapsed = time.time() - start_time
            avg_time = elapsed / idx if idx > 0 else 0
            remaining = avg_time * (len(id_list) - idx)
            print(f"进度: {idx}/{len(id_list)} ({idx/len(id_list)*100:.1f}%) | "
                  f"成功: {success_count} | 预计剩余: {remaining/60:.1f}分钟")
    
    # 汇总信息
    print("-" * 50)
    print(f"完成! 成功处理 {success_count}/{len(id_list)} 个视频")
    
    if success_count < len(id_list):
        failed_count = len(id_list) - success_count
        print(f"失败 {failed_count} 个，详见 video_errorlist.txt")
        
    elapsed_total = time.time() - start_time
    print(f"总耗时: {elapsed_total/60:.1f} 分钟")
    print(f"平均每个视频: {elapsed_total/len(id_list):.1f} 秒")

if __name__ == "__main__":
    print("B站视频数据爬虫 v2.0")
    print("=" * 50)
    main()