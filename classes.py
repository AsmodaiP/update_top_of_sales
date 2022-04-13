from typing import TypedDict, List

class ArticleInfo(TypedDict):
    revenue: str
    client_price: int
    name: str
    id: int
    color: str
    category: str
    brand: str
    seller: str
    balance: int
    comments: int
    raiting: int
    final_price: int
    final_price_min: int
    final_price_max: int
    final_price_average: int
    start_price: int
    basic_sale: int
    basic_price: int
    promo_sale: int
    client_sale: int
    client_price: int
    revenue_potential: int
    lost_profit: int
    days_in_stock: int
    sales: int
    revenue: int
    graph: List[int]

class ShortArticleInfo(TypedDict):
    id: int
    revenue: int
    price: int
    orders_count: int