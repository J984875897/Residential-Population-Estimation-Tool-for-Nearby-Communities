from typing import Optional


def calc_avg_rooms(room_dist: dict) -> Optional[float]:
    """
    计算加权平均卧室数 b
    room_dist: {卧室数: 套数}，例如 {1: 20, 2: 50, 3: 30}
    注意：从 JSON 断点恢复后，卧室数 key 会变成字符串，例如 {"1": 20}
    返回 None 如果没有有效数据
    """
    if not room_dist:
        return None

    weighted_rooms = 0.0
    total_units = 0
    for rooms, count in room_dist.items():
        try:
            rooms_num = float(rooms)
            count_num = int(count)
        except (TypeError, ValueError):
            continue

        if rooms_num <= 0 or count_num <= 0:
            continue

        weighted_rooms += rooms_num * count_num
        total_units += count_num

    if total_units == 0:
        return None
    return weighted_rooms / total_units


def calc_population(b: float, a: int) -> float:
    """
    估算小区居住人口
    P = a × b × 1.5 × 0.6
    a = 总户数（贝壳页面已是全小区合计），b = 平均每户室数
    1.5 = 每室平均人数，0.6 = 入住率修正
    """
    from config import PEOPLE_PER_ROOM, OCCUPANCY_RATE
    return a * b * PEOPLE_PER_ROOM * OCCUPANCY_RATE
