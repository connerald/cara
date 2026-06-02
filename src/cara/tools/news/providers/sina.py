"""
新浪财经行情中心搜索工具
"""

import requests
from typing import Optional

class SinaFinanceSearcher:
    """新浪财经行情中心搜索工具"""
    
    BASE_URL = "https://finance.sina.com.cn/"
    SEARCH_URL = "https://vip.stock.finance.sina.com.cn/mkt"
    SUGGEST_URL = "http://biz.finance.sina.com.cn/suggest/lookup.php"
    
    def __init__(self, timeout: int = 10):
        """
        初始化搜索工具
        
        参数:
            timeout: 请求超时时间（秒），默认10秒
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search(self, query: str) -> str:
        """
        搜索新浪财经
        
        参数:
            query: 搜索内容（简称/代码/拼音）
            
        返回:
            搜索结果页面的HTML代码文本
            
        异常:
            requests.RequestException: 网络请求出错
            ValueError: 搜索内容为空
        """
        if not query or not query.strip():
            raise ValueError("搜索内容不能为空")
        
        query = query.strip()
        
        try:
            # 构建搜索参数
            params = {
                'q': query,
                'bdate': '',
                'edate': '',
                'type': '0',
                'dpc': '1',
                'sdate': '',
                'symbol': '',
            }
            
            # 发送搜索请求
            response = self.session.get(
                self.SEARCH_URL,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # 设置正确的编码
            if response.encoding.lower() in ['gb2312', 'gbk']:
                response.encoding = 'gbk'
            
            return response.text
            
        except requests.RequestException as e:
            raise requests.RequestException(f"搜索请求失败: {str(e)}")
    
    def search_with_headers(self, query: str, referer: Optional[str] = None) -> str:
        """
        使用自定义请求头搜索
        
        参数:
            query: 搜索内容
            referer: 请求来源（可选）
            
        返回:
            搜索结果页面的HTML代码文本
        """
        if not query or not query.strip():
            raise ValueError("搜索内容不能为空")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': referer or self.BASE_URL,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
        }
        
        try:
            params = {'q': query.strip()}
            response = self.session.get(
                self.SEARCH_URL,
                params=params,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            if response.encoding.lower() in ['gb2312', 'gbk']:
                response.encoding = 'gbk'
            
            return response.text
            
        except requests.RequestException as e:
            raise requests.RequestException(f"搜索请求失败: {str(e)}")
    
    def get_search_suggestions(self, query: str, type_: str = "0") -> dict:
        """
        获取搜索建议/自动补全（通过lookup.php接口）
        
        参数:
            query: 搜索内容（股票简称/代码/拼音）
            type_: 搜索类型，默认为'0'（全部）
            
        返回:
            搜索结果字典，包含HTML内容或解析后的结果
            
        异常:
            requests.RequestException: 网络请求出错
            ValueError: 搜索内容为空
            
        说明:
            这个接口返回HTML页面而不是JSON，包含搜索结果的完整页面
        """
        if not query or not query.strip():
            raise ValueError("搜索内容不能为空")
        
        try:
            params = {
                'q': query.strip(),
                'type': type_,
            }
            
            response = self.session.get(
                self.SUGGEST_URL,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # 设置正确的编码
            if response.encoding.lower() in ['gb2312', 'gbk']:
                response.encoding = 'gbk'
            
            # 返回包含响应信息的字典
            return {
                'status': response.status_code,
                'content': response.text,
                'url': response.url,
                'content_type': response.headers.get('content-type', ''),
            }
                
        except requests.RequestException as e:
            raise requests.RequestException(f"获取搜索建议失败: {str(e)}")
    
    def close(self):
        """关闭会话连接"""
        self.session.close()


# 便捷函数
def search_sina_finance(query: str, timeout: int = 10) -> str:
    """
    快速搜索新浪财经的便捷函数
    
    参数:
        query: 搜索内容（简称/代码/拼音）
        timeout: 请求超时时间（秒），默认10秒
        
    返回:
        搜索结果页面的HTML代码文本
        
    示例:
        >>> html = search_sina_finance("中国平安")
        >>> print(len(html))  # 输出HTML长度
    """
    searcher = SinaFinanceSearcher(timeout=timeout)
    try:
        return searcher.search(query)
    finally:
        searcher.close()


def get_search_suggestions(query: str, timeout: int = 10, type_: str = "0") -> dict:
    """
    快速获取搜索建议的便捷函数
    
    参数:
        query: 搜索内容（简称/代码/拼音）
        timeout: 请求超时时间（秒），默认10秒
        type_: 搜索类型，默认为'0'（全部）
        
    返回:
        搜索结果字典
        
    示例:
        >>> result = get_search_suggestions("中国平安")
        >>> print(result['status'])  # 输出HTTP状态码
        >>> print(len(result['content']))  # 输出响应内容长度
    """
    searcher = SinaFinanceSearcher(timeout=timeout)
    try:
        return searcher.get_search_suggestions(query, type_)
    finally:
        searcher.close()


if __name__ == "__main__":
    # 测试示例
    query = "中国平安"
    
    searcher = SinaFinanceSearcher()
    
    try:
        # 获取搜索建议
        print(f"正在获取搜索建议: {query}")
        result = searcher.get_search_suggestions(query)
        print(f"\n搜索结果:")
        print(f"  状态码: {result['status']}")
        print(f"  内容类型: {result['content_type']}")
        print(f"  URL: {result['url']}")
        print(f"  内容长度: {len(result['content'])} 字符")
        print(f"  前200个字符:\n{result['content'][:200]}")
        
        # 同时演示直接搜索功能
        print(f"\n正在搜索: {query}")
        html = searcher.search(query)
        print(f"搜索成功，获取HTML代码长度: {len(html)} 字符")
        
    except Exception as e:
        print(f"出错: {e}")
    finally:
        searcher.close()
