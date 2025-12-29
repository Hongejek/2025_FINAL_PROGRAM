import re
import os
import time
import csv
import logging
from curl_cffi import requests
import sys

# =========================
# logging 配置
# =========================
LOG_LEVEL = logging.INFO

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

# =========================
# HTTP 请求封装
# =========================
def bili_get(url, headers, params=None, timeout=10):
    return requests.get(
        url,
        headers=headers,
        params=params,
        timeout=timeout,
        impersonate="chrome120"
    )

def get_Header(bv_id=None):
    with open("bili_cookie.txt", "r", encoding="utf-8") as f:
        cookie = f.read().strip()

    referer = (
        f"https://www.bilibili.com/video/{bv_id}/"
        if bv_id else
        "https://www.bilibili.com/"
    )

    return {
        "Cookie": cookie,
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"
        ),
        "Referer": referer,
        "Origin": "https://www.bilibili.com",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
    }

# =========================
# BV → aid / title
# =========================
def get_information(bv):
    try:
        url = f"https://www.bilibili.com/video/{bv}/"
        logger.info(f"获取视频信息: {bv}")

        resp = bili_get(url, get_Header(bv))
        resp.raise_for_status()
        html_content = resp.text

        # 方法1：从页面中提取视频aid
        aid_match = re.search(r'"aid":(?P<id>\d+),"bvid":"%s"' % bv, html_content)
        if not aid_match:
            # 尝试其他可能的模式
            aid_match = re.search(r'"aid":(\d+)', html_content)
            if not aid_match:
                raise ValueError(f"无法提取 aid，BV 可能无效: {bv}")
        
        aid = aid_match.group(1) if aid_match.groupdict().get('id') else aid_match.group(1)

        # 方法1：尝试从HTML中提取标题（多个匹配模式）
        title = "未识别"
        
        # 尝试从<title>标签中提取
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.DOTALL)
        if title_match:
            raw_title = title_match.group(1).strip()
            # 清理标题，移除" - 哔哩哔哩"等后缀
            if ' - 哔哩哔哩' in raw_title:
                title = raw_title.split(' - 哔哩哔哩')[0]
            elif ' - bilibili' in raw_title:
                title = raw_title.split(' - bilibili')[0]
            else:
                title = raw_title
        else:
            # 尝试从JSON-LD数据中提取
            jsonld_match = re.search(r'"name":"(.*?)"', html_content)
            if jsonld_match:
                title = jsonld_match.group(1)
        
        # 如果以上方法都失败，使用API获取标题
        if title == "未识别":
            try:
                api_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bv}"
                api_resp = bili_get(api_url, get_Header())
                api_data = api_resp.json()
                if api_data.get("code") == 0:
                    title = api_data.get("data", {}).get("title", "未识别")
            except:
                pass

        return aid, title

    except Exception as e:
        logger.error(f"获取视频信息失败: {e}")
        # 返回默认值
        return "0", "未识别"

# =========================
# 文件名清理
# =========================
def sanitize_title_for_filename(title):
    short = (title or "未识别").strip()[:12]
    return re.sub(r'[\\/:*?"<>|]', "_", short)

# =========================
# 评论抓取主逻辑
# =========================
def start(bv, oid, page_num, count, csv_writer, is_second):
    params = {
        "oid": oid,
        "type": 1,
        "mode": 3,
        "pn": page_num,
        "ps": 20,
        "plat": 1,
        "web_location": 1315875,
    }

    try:
        response = bili_get(
            "https://api.bilibili.com/x/v2/reply/main",
            headers=get_Header(bv),
            params=params
        )
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logger.error(f"评论请求失败: {e}")
        return bv, oid, page_num, count, csv_writer, is_second

    if data.get("code") != 0:
        logger.warning(f"接口返回异常: {data.get('message')}")
        return bv, oid, page_num, count, csv_writer, is_second

    replies = data.get("data", {}).get("replies")
    if not replies:
        logger.info("没有更多评论，爬取完成")
        return bv, oid, 0, count, csv_writer, is_second

    for reply in replies:
        count += 1

        # 每100条评论输出一次进度
        if count % 100 == 0:
            logger.info(f"已爬取 {count} 条评论")

        member = reply.get("member", {})
        content = reply.get("content", {})
        
        # IP属地处理
        location = reply.get("reply_control", {}).get("location", "")
        if location and len(location) > 5:
            IP = location[5:]
        else:
            IP = "未知"
            
        # 大会员状态
        vip_status = member.get("vip", {}).get("status", 0)
        vip = "是" if vip_status == 1 else "否"

        csv_writer.writerow([
            count,
            "",
            reply.get("rpid"),
            member.get("mid"),
            member.get("uname"),
            member.get("level_info", {}).get("current_level"),
            member.get("sex"),
            content.get("message"),
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(reply.get("ctime"))),
            reply.get("rcount"),
            reply.get("like"),
            member.get("sign"),
            IP,
            vip,
            member.get("avatar"),
        ])

        # 二级评论
        if is_second and reply.get("rcount", 0) > 0:
            root = reply.get("rpid")
            total_pages = (reply.get("rcount", 0) + 9) // 10

            for pn in range(1, total_pages + 1):
                sub_params = {
                    "oid": oid,
                    "type": 1,
                    "root": root,
                    "pn": pn,
                    "ps": 10,
                    "web_location": 333.788,
                }

                try:
                    sub_resp = bili_get(
                        "https://api.bilibili.com/x/v2/reply/reply",
                        headers=get_Header(bv),
                        params=sub_params
                    )
                    sub_resp.raise_for_status()
                    sub_data = sub_resp.json()
                except Exception as e:
                    break

                if sub_data.get("code") != 0:
                    break

                sub_replies = sub_data.get("data", {}).get("replies")
                if not sub_replies:
                    break

                for sub in sub_replies:
                    count += 1
                    
                    # 每100条评论输出一次进度
                    if count % 100 == 0:
                        logger.info(f"已爬取 {count} 条评论")
                    
                    sub_member = sub.get("member", {})
                    sub_content = sub.get("content", {})
                    
                    sub_location = sub.get("reply_control", {}).get("location", "")
                    if sub_location and len(sub_location) > 5:
                        sub_IP = sub_location[5:]
                    else:
                        sub_IP = "未知"
                        
                    sub_vip_status = sub_member.get("vip", {}).get("status", 0)
                    sub_vip = "是" if sub_vip_status == 1 else "否"

                    csv_writer.writerow([
                        count,
                        root,
                        sub.get("rpid"),
                        sub_member.get("mid"),
                        sub_member.get("uname"),
                        sub_member.get("level_info", {}).get("current_level"),
                        sub_member.get("sex"),
                        sub_content.get("message"),
                        time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(sub.get("ctime"))),
                        "",
                        sub.get("like"),
                        sub_member.get("sign"),
                        sub_IP,
                        sub_vip,
                        sub_member.get("avatar"),
                    ])

                time.sleep(0.3)

    # 检查是否还有下一页
    cursor = data.get("data", {}).get("cursor", {})
    is_end = cursor.get("is_end", False)
    
    if is_end:
        logger.info(f"评论爬取完成！总共爬取{count}条。")
        return bv, oid, 0, count, csv_writer, is_second
    else:
        time.sleep(0.8)
        return bv, oid, page_num + 1, count, csv_writer, is_second

# =========================
# 程序入口&终止信号处理
# =========================
if __name__ == "__main__":

    # 从bv_list.txt中读取视频bv（取第一行非空BV）
    bv_list_file = "bv_list.txt"
    try:
        with open(bv_list_file, "r", encoding="utf-8") as f:
            bvs = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"错误: 找不到BV列表文件 {bv_list_file}")
        sys.exit(1)

    if not bvs:
        print("错误: BV列表文件为空")
        sys.exit(1)

    bv = bvs[0]
    print(f"使用BV: {bv}")

    # 获取视频oid和标题
    oid, title = get_information(bv)
    # 评论起始页（默认为空）
    next_pageID = ''
    # 初始化评论数量
    count = 0

    # 是否开启二级评论爬取，默认开启
    is_second = True

    # 创建输出目录
    output_dir = os.path.join("data", "comment")
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{sanitize_title_for_filename(title)}_评论.csv"
    filepath = os.path.join(output_dir, filename)

    try:
        # 创建CSV文件并写入表头
        with open(filepath, mode='w', newline='', encoding='utf-8-sig') as file:
            csv_writer = csv.writer(file)
            csv_writer.writerow(['序号', '上级评论ID','评论ID', '用户ID', '用户名', '用户等级', '性别', '评论内容', '评论时间', '回复数', '点赞数', '个性签名', 'IP属地', '是否是大会员', '头像'])

            # 开始爬取
            while next_pageID != 0:
                bv, oid, next_pageID, count, csv_writer, is_second = start(bv, oid, next_pageID, count, csv_writer, is_second)
    
    except KeyboardInterrupt:
    # 通过读取文件行数计算实际爬取的评论数量
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                lines = sum(1 for _ in f)
                actual_count = max(0, lines - 1) 
        except:
            actual_count = count
        print(f"\n程序被用户中断，已爬取 {actual_count} 条评论")
        print(f"数据已保存到: {filepath}")
        
    except Exception as e:
        print(f"程序异常: {e}")