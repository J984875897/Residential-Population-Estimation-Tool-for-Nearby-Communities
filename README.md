# 周边小区居住人口估算工具

# Residential Population Estimation Tool for Nearby Communities

## 一、项目简介 / Overview

本项目是一个基于 Python 的周边小区居住人口估算工具。程序以指定目标地点为中心，按城市、行政区和搜索半径采集贝壳找房小区公开页面中的基础信息，并结合空间距离筛选与人口估算模型，生成结构化 Excel 结果，便于开展周边居住人口规模分析。

This project is a Python-based tool for estimating the residential population around a target location. It collects publicly available community-level information from Beike, filters communities by geographic distance, applies a configurable population estimation model, and exports structured results to Excel for further analysis.

## 二、功能概述 / Features

- 支持图形界面和命令行两种运行方式。  
  Supports both graphical user interface and command-line execution.
- 支持按城市代码、行政区和目标半径配置抓取范围。  
  Allows users to configure the search scope by city code, districts, and radius.
- 支持从列表页坐标进行预筛选，减少详情页访问次数。  
  Uses list-page coordinates for preliminary filtering to reduce detail-page requests.
- 支持断点续跑，运行中断后可继续执行已保存进度。  
  Supports checkpoint-based resume after interruptions.
- 支持单独重算结果，便于修改半径、坐标或估算参数后快速生成新表。  
  Allows recalculation without re-crawling when radius, coordinates, or model parameters change.
- 支持导出 Excel，包含小区名称、距离、户数、平均室数、估算人口和数据来源链接。  
  Exports results to Excel, including community name, distance, household count, average room count, estimated population, and source link.

## 三、项目结构 / Project Structure

```text
├── main.py              # 主流程入口 / Main workflow and Excel output
├── gui.py               # 图形界面 / Tkinter GUI
├── scraper.py           # 爬取逻辑 / Selenium scraping logic
├── calculator.py        # 估算公式 / Average room and population calculation
├── distance.py          # 距离计算 / Haversine distance calculation
├── config.example.py    # 示例配置 / Example configuration
├── requirements.txt     # Python 依赖 / Python dependencies
└── README.md
```

## 四、环境安装 / Installation

建议使用虚拟环境：

It is recommended to use a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

首次运行 Selenium 时，`webdriver-manager` 会自动下载匹配的 ChromeDriver。请确保本机已安装 Chrome。

When Selenium runs for the first time, `webdriver-manager` will automatically download the matching ChromeDriver. Please make sure Google Chrome is installed locally.

## 五、参数配置 / Configuration

复制示例配置：

Copy the example configuration file:

```bash
cp config.example.py config.py
```

然后编辑 `config.py`：

Then edit `config.py`:

- `CITY_CODE`：贝壳城市代码，例如兰州为 `lz`。  
  Beike city code, for example `lz` for Lanzhou.
- `CITY_NAME`：城市中文名，用于日志和输出文件。  
  City name used in logs and output files.
- `TARGET_LNG` / `TARGET_LAT`：目标地点经纬度。  
  Longitude and latitude of the target location.
- `TARGET_NAME`：目标地点名称。  
  Name of the target location.
- `RADIUS_KM`：搜索半径，单位为公里。  
  Search radius in kilometers.
- `SEARCH_DISTRICTS`：行政区拼音列表。  
  List of district slugs used by Beike URLs.
- `DEFAULT_B`：缺少户型分布时使用的默认平均室数。  
  Default average room count when room distribution data is unavailable.
- `PEOPLE_PER_ROOM`：每室平均居住人数。  
  Average number of residents per room.
- `OCCUPANCY_RATE`：入住率修正系数。  
  Occupancy-rate adjustment factor.

GUI 和 CLI 会把上次输入保存到本地 `last_run_config.json`，下次启动时自动带出；这个文件不会替代 `config.py`，只是作为本机运行记录使用。

The GUI and CLI save the last inputs to local `last_run_config.json` and load them on the next run. This file does not replace `config.py`; it is only local runtime state.

## 六、运行方式 / Usage

图形界面模式：

Run with GUI:

```bash
python main.py
```

命令行模式：

Run in command-line mode:

```bash
python main.py --cli
```

测试模式，仅抓取一个小区并打印结果：

Test mode, which crawls one community and prints the result:

```bash
python main.py --test
```

清除断点：

Clear checkpoints:

```bash
python main.py --reset
```

## 七、输出结果 / Output

程序会生成一个 Excel 文件，文件名格式如下：

The program generates an Excel file with the following naming format:

```text
目标地点_人口估算结果.xlsx
```

输出表包含小区名称、距离、是否在搜索半径内、楼栋数、总户数、平均室数、估算人口和贝壳链接。范围外的小区会在表格中保留并灰显，便于核查筛选边界。

The output table includes community name, distance, whether it is within the configured radius, building count, household count, average room count, estimated population, and Beike source link. Communities outside the radius are retained and greyed out for boundary review.

## 八、估算方法 / Estimation Method

人口估算公式如下：

The population estimation formula is:

```text
P = a * b * PEOPLE_PER_ROOM * OCCUPANCY_RATE
```

其中：

Where:

- `P`：估算居住人口。  
  Estimated residential population.
- `a`：小区总户数。  
  Total household count of the community.
- `b`：加权平均室数；若页面无户型分布，则使用 `DEFAULT_B`。  
  Weighted average room count; `DEFAULT_B` is used when room distribution data is unavailable.
- `PEOPLE_PER_ROOM`：每室平均居住人数。  
  Average number of residents per room.
- `OCCUPANCY_RATE`：入住率修正系数。  
  Occupancy-rate adjustment factor.

小区与目标地点之间的距离采用 Haversine 公式计算。程序会根据配置半径筛选参与汇总的小区，并在 Excel 中保留完整计算结果。

The distance between each community and the target location is calculated using the Haversine formula. The program filters communities according to the configured radius and keeps the full calculation results in the Excel output.

坐标说明：小区坐标来自贝壳页面字段，目标坐标由用户提供。程序不判断坐标系，也不做百度 / 高德 / WGS84 / GCJ-02 等坐标转换；建议目标坐标尽量与贝壳坐标保持同一体系，尤其是 1km 这类较小半径的边界判断。

Coordinate note: community coordinates are extracted from Beike page fields, while the target coordinate is user-provided. The program does not detect or convert between coordinate systems such as Baidu, Amap, WGS84, or GCJ-02. Use a target coordinate that is as consistent with Beike's coordinates as possible, especially for small-radius boundary decisions such as 1 km.

## 九、流程说明 / Workflow

程序主流程分为三个阶段：

The main workflow consists of three steps:

```text
Step 1：按行政区抓取小区列表，并使用列表页坐标进行初步筛选
        Crawl community lists by district and apply preliminary filtering using list-page coordinates

Step 2：访问小区详情页，提取楼栋数、总户数、坐标和户型分布
        Visit detail pages and extract building count, household count, coordinates, and room distribution

Step 3：计算距离和估算人口，生成 Excel 汇总结果
        Calculate distances, estimate population, and generate the Excel summary
```

断点文件默认保存在 `checkpoints/` 目录中，也可以在 GUI 或 CLI 启动时选择其他数据保存文件夹。程序只检查当前选择文件夹里的 `step1_urls.json` 和 `step2_details.json`；如果有断点，会提示继续或重跑，如果没有断点，会提示并从 Step 1 开始。

Checkpoint files are stored in `checkpoints/` by default, and another data folder can be selected in the GUI or CLI. The program only checks `step1_urls.json` and `step2_details.json` in the selected folder. If checkpoints exist, it offers resume/restart choices; otherwise it starts from Step 1.

## 十、使用说明 / Notes

本项目适用于学习、研究和内部分析场景。使用时应合理设置请求间隔，遵守目标网站的服务条款和 robots 规则，避免高频访问或对目标网站造成额外负担。

This project is intended for learning, research, and internal analysis. Please use reasonable request intervals, comply with the target website's terms of service and robots rules, and avoid high-frequency access that may cause unnecessary load.
