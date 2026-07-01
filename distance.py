import math


def haversine(lng1: float, lat1: float, lng2: float, lat2: float) -> float:
    """
    计算地球上两点间的球面距离（km）
    使用 Haversine 公式，无需任何外部 API
    参数顺序：经度1, 纬度1, 经度2, 纬度2
    """
    R = 6371.0
    dlng = math.radians(lng2 - lng1)
    dlat = math.radians(lat2 - lat1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(dlng / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))
