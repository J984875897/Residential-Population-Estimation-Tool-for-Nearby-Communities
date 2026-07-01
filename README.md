# 贝壳周边小区人口估算爬虫

一个用于估算目标地点周边小区居住人口的 Python 小工具。程序会从贝壳找房小区页面抓取小区 URL、楼栋数、总户数、坐标和户型分布，按目标坐标和搜索半径筛选小区，最后导出 Excel 结果。

## 功能特点

- 支持 GUI 和命令行两种运行方式
- 支持按城市代码和行政区配置抓取范围
- 使用列表页坐标做预筛选，减少详情页请求量
- 支持断点文件，运行中断后可继续
- 支持重新运行 Step 3，便于修改半径、坐标或公式后快速重算
- 自动生成 Excel，并标记范围外小区和默认平均室数

## 项目结构

```text
.
├── main.py              # 主流程入口，包含三步爬取和 Excel 输出
├── gui.py               # tkinter 图形界面
├── scraper.py           # Selenium 抓取逻辑
├── calculator.py        # 平均室数和人口估算公式
├── distance.py          # Haversine 距离计算
├── config.example.py    # 示例配置文件
├── requirements.txt     # Python 依赖
└── README.md
```

## 安装

建议使用虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

首次运行 Selenium 时，`webdriver-manager` 会自动下载匹配的 ChromeDriver。请确保本机已安装 Chrome。

## 配置

复制示例配置：

```bash
cp config.example.py config.py
```

然后编辑 `config.py`：

- `CITY_CODE`：贝壳城市代码，例如兰州为 `lz`
- `CITY_NAME`：城市中文名
- `TARGET_LNG` / `TARGET_LAT`：目标地点经纬度
- `TARGET_NAME`：目标地点名称
- `RADIUS_KM`：搜索半径，单位公里
- `SEARCH_DISTRICTS`：行政区拼音列表

`config.py` 默认不会提交到 GitHub，避免公开真实项目名称、坐标或客户信息。

## 运行

GUI 模式：

```bash
python main.py
```

命令行模式：

```bash
python main.py --cli
```

测试模式，仅抓取一个小区并打印结果：

```bash
python main.py --test
```

清除断点：

```bash
python main.py --reset
```

## 输出

程序会生成一个 Excel 文件，文件名类似：

```text
目标地点_人口估算结果.xlsx
```

输出表包含小区名称、距离、是否在搜索半径内、楼栋数、总户数、平均室数、估算人口和贝壳链接。

## 隐私与上传注意事项

上传到公开 GitHub 前，请不要提交以下内容：

- `config.py`：可能包含真实目标地点、坐标和项目名称
- `checkpoints/`：断点文件，包含已抓取的小区链接和详情数据
- `*.xlsx` / `*.csv`：导出的分析结果
- `.claude/`、`.vscode/`、`__pycache__/`、`.DS_Store` 等本地环境文件
- 调试脚本运行输出，尤其是包含 Cookie 片段、页面内容或本地路径的日志

本项目根目录 `.gitignore` 已默认排除这些文件。提交前仍建议运行：

```bash
git status --short
git diff --cached --name-only
```

确认待提交文件中没有隐私数据后再 push。

## 人口估算公式

```text
P = a * b * PEOPLE_PER_ROOM * OCCUPANCY_RATE
```

- `a`：小区总户数
- `b`：加权平均室数；若页面无户型分布，则使用 `DEFAULT_B`
- `PEOPLE_PER_ROOM`：每室平均居住人数
- `OCCUPANCY_RATE`：入住率修正

## 免责声明

本项目仅用于学习和内部分析。请遵守目标网站的服务条款和 robots 规则，合理设置请求间隔，不要进行高频或商业化爬取。
