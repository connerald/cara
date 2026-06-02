from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class StockPrice:
    """股票价格数据"""
    symbol: str              # 股票代码 (如: sh000001)
    name: str                # 股票名称
    price: float             # 当前价格
    timestamp: str           # 时间戳
    change: float | None = None         # 涨跌幅 (%), 可选
    change_amount: float | None = None  # 涨跌金额, 可选
    high: float | None = None           # 最高价, 可选
    low: float | None = None            # 最低价, 可选
    volume: int | None = None           # 成交量, 可选

    def has_field(self, field_name: str) -> bool:
        """判断某个字段是否已获取到有效值"""
        return getattr(self, field_name, None) is not None


class PriceProvider(ABC):
    """股票价格提供者基类"""
    
    @abstractmethod
    def get_stock_price(
        self,
        symbol: str,
        fields: set[str] | None = None,
    ) -> Optional[StockPrice]:
        """
        获取单只股票的价格信息。
        支持按需字段请求，减少不必要的数据抓取和解析开销。
        
        参数:
            symbol: 股票代码 (如: sh000001 表示上海证券交易所的代码)
            fields: 期望返回的字段集合；None 表示使用提供者默认字段策略
        
        返回:
            获取成功时返回 StockPrice，失败时返回 None
        """
        pass
