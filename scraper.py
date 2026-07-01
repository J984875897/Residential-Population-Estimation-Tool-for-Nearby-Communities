import re
import time
import random
import logging
from typing import Optional

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

import config

logger = logging.getLogger(__name__)

_driver: Optional[webdriver.Chrome] = None
_request_count = 0
_log_fn = print
_verify_fn = None  # GUI 模式注入，CLI 模式回落到 input()


def set_callbacks(log_fn=print, verify_fn=None):
    """由 GUI / main 在启动前注入，使 scraper 内部交互走弹窗而非终端。"""
    global _log_fn, _verify_fn
    _log_fn = log_fn
    if verify_fn is not None:
        _verify_fn = verify_fn

def _init_driver() -> webdriver.Chrome:
    """启动 Chrome 浏览器（仅初始化一次）"""
    global _driver
    if _driver is not None:
        return _driver

    options = Options()
    options.add_argument("--lang=zh-CN")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--start-maximized")
    options.add_argument("--disable-infobars")

    print("  正在启动 Chrome 浏览器（首次启动需下载驱动，约30秒）...")
    service = Service(ChromeDriverManager().install())
    _driver = webdriver.Chrome(service=service, options=options)

    # 移除 Selenium 标志，避免被检测
    _driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

    return _driver


def close_driver() -> None:
    """关闭 Selenium Chrome，避免流程结束后浏览器残留。"""
    global _driver
    if _driver is None:
        return
    try:
        _driver.quit()
    except Exception as exc:
        logger.warning("关闭 Chrome 浏览器失败: %s", exc)
    finally:
        _driver = None


def sync_browser_cookies() -> int:
    """
    将 Chrome 中 ke.com 的登录 Cookie 注入到 Selenium 驱动。
    调用前需先启动驱动并导航到 ke.com。
    返回注入的 Cookie 数量。
    """
    driver = _init_driver()

    # 导航到目标域（必须先在该域下才能设置 cookies）
    driver.get(f"{config.BASE_URL}/xiaoqu/")
    time.sleep(2)

    try:
        import browser_cookie3
        jar = list(browser_cookie3.chrome(domain_name=".ke.com"))
        if not jar:
            logger.warning("Chrome 中没有 ke.com cookies，请先在 Chrome 登录贝壳")
            return 0

        count = 0
        for ck in jar:
            try:
                driver.add_cookie({
                    "name": ck.name,
                    "value": ck.value,
                    "domain": ck.domain,
                    "path": ck.path or "/",
                })
                count += 1
            except Exception:
                pass

        # 刷新页面使 cookies 生效
        driver.refresh()
        time.sleep(2)
        logger.info("已注入 %d 个 ke.com cookies 到浏览器", count)
        return count

    except ImportError:
        logger.warning("browser-cookie3 未安装: pip3 install browser-cookie3")
        return 0
    except Exception as exc:
        logger.warning("Cookie 注入失败: %s", exc)
        return 0


def get_district_links() -> list:
    """抓取城市首页，返回可用行政区列表 [{"name": "七里河区", "slug": "qilihequ"}, ...]"""
    soup = _make_request(f"{config.BASE_URL}/xiaoqu/")
    if soup is None:
        return []
    results, seen = [], set()
    for a in soup.find_all("a", href=True):
        m = re.match(r"^/xiaoqu/([a-z]+)/$", a["href"])
        if m:
            slug = m.group(1)
            name = a.get_text(strip=True)
            if slug and name and slug not in seen:
                seen.add(slug)
                results.append({"name": name, "slug": slug})
    return results


def _make_request(url: str, retries: int = 3) -> Optional[BeautifulSoup]:
    """使用 Selenium Chrome 获取页面，自动处理验证码（浏览器可见）"""
    global _request_count
    _request_count += 1
    if _request_count > 1 and _request_count % 10 == 0:
        pause = random.uniform(15, 25)
        logger.info("已完成 %d 次请求，主动暂停 %.0f 秒...", _request_count, pause)
        time.sleep(pause)

    driver = _init_driver()

    for attempt in range(retries):
        try:
            driver.get(url)
            time.sleep(random.uniform(config.DELAY_MIN, config.DELAY_MAX))

            current_url = driver.current_url
            is_blocked = any(x in current_url for x in
                             ["captcha", "clogin", "hip.ke.com", "verify"])

            if is_blocked:
                _log_fn("\n⚠️  浏览器需要验证（已自动跳转到验证页面）")
                _log_fn("   请在弹出的 Chrome 窗口中完成验证后点击「继续运行」")
                if _verify_fn is not None:
                    _verify_fn()
                else:
                    input("   完成后回到这里按 Enter 继续...")
                time.sleep(2)
                driver.get(url)
                time.sleep(4)
                if any(x in driver.current_url for x in ["captcha", "clogin", "hip.ke.com"]):
                    logger.warning("验证后仍被拦截，重试 %d/%d...", attempt + 1, retries)
                    continue

            html = driver.page_source
            if len(html) < 3000:
                logger.warning("页面内容过短（%d字节），可能未加载完成，重试...", len(html))
                time.sleep(5)
                continue

            return BeautifulSoup(html, "html.parser")

        except Exception as exc:
            logger.warning("请求失败（第%d次）: %s", attempt + 1, exc)
            if attempt < retries - 1:
                time.sleep(5)

    logger.error("❌ 无法访问: %s", url)
    return None


def _extract_list_page_coords(soup: BeautifulSoup) -> dict:
    """
    从列表页脚本数据提取 {小区ID: (lng, lat)} 映射。
    贝壳列表页通常在 <script> 内嵌 JSON 数据包含坐标，提取成功则 Step 2 可大幅减少请求数。
    """
    coord_map = {}
    for script in soup.find_all("script"):
        text = script.string or ""
        if len(text) < 100:
            continue
        # 格式: "resblockId":"xxx" ... "posX":103.7 ... "posY":36.1
        for m in re.finditer(
            r'"(?:resblockId|houseId|id)"\s*:\s*"?(\d{8,})"?'
            r'.{0,300}?"(?:posX|longitude|lng)"\s*:\s*([\d.]+)'
            r'.{0,200}?"(?:posY|latitude|lat)"\s*:\s*([\d.]+)',
            text, re.S
        ):
            coord_map[m.group(1)] = (float(m.group(2)), float(m.group(3)))
        # 反向格式: posX 在前, id 在后
        for m in re.finditer(
            r'"(?:posX|longitude|lng)"\s*:\s*([\d.]+)'
            r'.{0,200}?"(?:posY|latitude|lat)"\s*:\s*([\d.]+)'
            r'.{0,300}?"(?:resblockId|houseId|id)"\s*:\s*"?(\d{8,})"?',
            text, re.S
        ):
            coord_map[m.group(3)] = (float(m.group(1)), float(m.group(2)))
    return coord_map


def get_community_urls(district: str) -> list:
    """
    翻页爬取某行政区所有小区的详情页 URL，同时尝试从列表页提取坐标。
    返回 list[dict]：[{"url": str, "name": str, "lng": float|None, "lat": float|None}]
    坐标有值时可在 Step 1 预筛选距离，大幅减少 Step 2 的详情页请求数。
    """
    results = []
    seen_urls = set()
    page = 1

    while True:
        list_url = f"{config.BASE_URL}/xiaoqu/{district}/pg{page}/"
        logger.info("  列表页: %s", list_url)

        soup = _make_request(list_url)
        if soup is None:
            break

        coord_map = _extract_list_page_coords(soup)
        found_this_page = []

        for tag in soup.find_all("a", href=re.compile(r"/xiaoqu/\d{4,}/")):
            href = tag["href"]
            url = href if href.startswith("http") else config.BASE_URL + href
            url = url.split("?")[0].rstrip("/") + "/"
            if url in seen_urls:
                continue
            seen_urls.add(url)

            name = tag.get_text(strip=True) or url
            id_match = re.search(r"/xiaoqu/(\d+)/", url)
            comm_id = id_match.group(1) if id_match else None

            lng, lat = None, None
            if comm_id and comm_id in coord_map:
                lng, lat = coord_map[comm_id]
            else:
                # 备用：从父元素向上遍历，在小区卡片范围内找 xiaoqu 属性
                node = tag.parent
                for _ in range(5):
                    if node is None:
                        break
                    val = node.get("xiaoqu", "")
                    if val:
                        m = re.search(r"\[?\s*([\d.]+)\s*,\s*([\d.]+)\s*\]?", val)
                        if m:
                            lng, lat = float(m.group(1)), float(m.group(2))
                            break
                    sub = node.find(attrs={"xiaoqu": True})
                    if sub:
                        m = re.search(r"\[?\s*([\d.]+)\s*,\s*([\d.]+)\s*\]?",
                                      sub.get("xiaoqu", ""))
                        if m:
                            lng, lat = float(m.group(1)), float(m.group(2))
                            break
                    node = node.parent

            found_this_page.append({"url": url, "name": name, "lng": lng, "lat": lat})

        if not found_this_page:
            logger.info("  第%d页无结果，停止翻页", page)
            break

        results.extend(found_this_page)
        coord_count = sum(1 for c in found_this_page if c["lng"] is not None)
        logger.info(
            "  第%d页: 找到 %d 个小区（%d 个已提取坐标）（累计 %d）",
            page, len(found_this_page), coord_count, len(results)
        )

        has_next = bool(soup.select_one("a.next")) or bool(
            soup.find("a", string=re.compile(r"下一页|›|»"))
        )
        if not has_next:
            pager = soup.select_one(".house-lst-page-box, .page-box")
            if pager:
                page_links = [a.get_text(strip=True) for a in pager.find_all("a")]
                if str(page + 1) not in page_links:
                    break
            else:
                break

        page += 1

    return results


def _extract_coords(soup: BeautifulSoup) -> Optional[tuple]:
    """从页面中提取 [经度, 纬度]"""
    # 方法1: 贝壳在 <span xiaoqu="[lng,lat]"> 属性中内嵌坐标
    for tag in soup.find_all(attrs={"xiaoqu": True}):
        val = tag.get("xiaoqu", "")
        m = re.search(r"\[?\s*([\d.]+)\s*,\s*([\d.]+)\s*\]?", val)
        if m:
            return float(m.group(1)), float(m.group(2))

    # 方法2: 搜索 <script> 中的 JSON 字段 "longitude"/"latitude"
    for script in soup.find_all("script"):
        text = script.string or ""
        m = re.search(
            r'"(?:longitude|lng)"\s*:\s*([\d.]+).*?"(?:latitude|lat)"\s*:\s*([\d.]+)',
            text,
            re.S,
        )
        if m:
            return float(m.group(1)), float(m.group(2))

    return None


def _extract_int(text: str) -> Optional[int]:
    m = re.search(r"[\d,]+", text)
    if m:
        return int(m.group().replace(",", ""))
    return None


def _extract_building_info(soup: BeautifulSoup) -> dict:
    """提取楼栋数(N)和总户数(a)"""
    result = {"N": None, "a": None}

    # 尝试 <dl><dt>标签</dt><dd>值</dd></dl> 结构
    for dl in soup.find_all("dl"):
        dts = dl.find_all("dt")
        dds = dl.find_all("dd")
        for dt, dd in zip(dts, dds):
            label = dt.get_text(strip=True)
            value = dd.get_text(strip=True)
            if re.search(r"楼栋", label):
                result["N"] = _extract_int(value)
            elif re.search(r"总户|房屋总", label):
                result["a"] = _extract_int(value)

    # 备用：直接从纯文本中找 "楼栋数" / "总户数" 后的数字
    if result["N"] is None or result["a"] is None:
        for tag in soup.find_all(string=re.compile(r"楼栋数|楼栋总数")):
            sibling = tag.parent.find_next_sibling()
            if sibling and result["N"] is None:
                result["N"] = _extract_int(sibling.get_text())

        for tag in soup.find_all(string=re.compile(r"总户数|房屋总数")):
            sibling = tag.parent.find_next_sibling()
            if sibling and result["a"] is None:
                result["a"] = _extract_int(sibling.get_text())

    # 备用2：从整段文本中匹配 "X栋" / "X户"
    page_text = soup.get_text()
    if result["N"] is None:
        m = re.search(r"楼栋数[^\d]*(\d+)\s*栋", page_text)
        if m:
            result["N"] = int(m.group(1))
    if result["a"] is None:
        m = re.search(r"总户数[^\d]*(\d+)\s*户", page_text)
        if m:
            result["a"] = int(m.group(1))

    return result


def _extract_room_distribution(soup: BeautifulSoup) -> dict:
    """
    提取户型分布 {卧室数(int): 套数(int)}
    例如：{1: 20, 2: 50, 3: 30}
    若页面无此数据则返回空字典（调用方使用默认值）
    """
    room_dist = {}
    page_text = soup.get_text(" ")

    # 匹配 "X室...数字套" 格式
    for m in re.finditer(r"(\d)\s*室[^套\d]{0,10}([\d,]+)\s*套", page_text):
        rooms = int(m.group(1))
        count = int(m.group(2).replace(",", ""))
        if 1 <= rooms <= 6:
            room_dist[rooms] = room_dist.get(rooms, 0) + count

    # 备用：表格行 <td>X室Y厅</td><td>N套</td>
    if not room_dist:
        for row in soup.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                label = cells[0].get_text(strip=True)
                value = cells[-1].get_text(strip=True)
                m_r = re.match(r"(\d)\s*室", label)
                m_v = re.search(r"([\d,]+)", value)
                if m_r and m_v:
                    rooms = int(m_r.group(1))
                    count = int(m_v.group(1).replace(",", ""))
                    if 1 <= rooms <= 6 and count > 0:
                        room_dist[rooms] = room_dist.get(rooms, 0) + count

    return room_dist


def get_community_detail(url: str) -> Optional[dict]:
    """
    爬取小区详情页，返回数据字典：
    {
        name       : str,
        url        : str,
        lng        : float,
        lat        : float,
        N          : int | None,
        a          : int | None,
        room_dist  : dict,   # {卧室数: 套数}，可能为空
    }
    坐标缺失时返回 None（无法计算距离）
    """
    soup = _make_request(url)
    if soup is None:
        return None

    # 小区名称
    name_tag = soup.select_one(
        "h1.detailTitle, .xiaoquDetailedTitle h1, .content h1, h1"
    )
    name = name_tag.get_text(strip=True) if name_tag else url.rstrip("/").split("/")[-1]

    # 坐标（缺失则放弃该小区）
    coords = _extract_coords(soup)
    if not coords:
        logger.warning("  ⚠️  未找到坐标: %s (%s)", name, url)
        return None
    lng, lat = coords

    building_info = _extract_building_info(soup)
    room_dist = _extract_room_distribution(soup)

    return {
        "name": name,
        "url": url,
        "lng": lng,
        "lat": lat,
        "N": building_info["N"],
        "a": building_info["a"],
        "room_dist": room_dist,
    }
