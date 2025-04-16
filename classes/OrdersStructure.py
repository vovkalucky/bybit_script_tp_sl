#from dataclasses import dataclass
from pydantic import BaseModel
from typing import Optional

class Order(BaseModel):
    order_id: Optional[str] = None
    symbol: Optional[str] = None
    take_profit: Optional[str] = None
    stop_loss: Optional[str] = None
    qty_open: Optional[str] = None
    side_open: Optional[str] = None
    money_open: Optional[str] = None
    tax_open: Optional[str] = None
    time_open: Optional[str] = None
    qty_close: Optional[str] = None
    side_close: Optional[str] = None
    money_close: Optional[str] = None
    tax_close: Optional[str] = None
    price: Optional[str] = None
    avgPrice: Optional[str] = None
    status: Optional[str] = None
    order_id_close: Optional[str] = None
    basePrice: Optional[str] = None
    triggerPrice: Optional[str] = None


# @dataclass
# class Order:
#     order_id: Optional[str] = None
#     symbol: Optional[str] = None
#     qty: Optional[str] = None
#     side: Optional[str] = None
#     status: Optional[str] = None
#     close_price: Optional[str] = None
#     money_open: Optional[str] = None
#     tax_open: Optional[str] = None
#     time_open: Optional[str] = None
#     price: Optional[str] = None
#
# @dataclass
# class Order:
#     order_id: Optional[str] = None
#     symbol: Optional[str] = None
#     qty: Optional[str] = None
#     side: Optional[str] = None
#     status: Optional[str] = None
#     close_price: Optional[str] = None
#     money_open: Optional[str] = None
#     tax_open: Optional[str] = None
#     time_open: Optional[str] = None
#
#
# @dataclass
# class Order:
#     order_id: Optional[str] = None
#     symbol: Optional[str] = None
#     take_profit: Optional[str] = None
#     stop_loss: Optional[str] = None
#     qty: Optional[str] = None
#     side: Optional[str] = None
#     status: Optional[str] = None
#     close_price: Optional[str] = None
#     money_open: Optional[str] = None
#     tax_open: Optional[str] = None
#     time_open: Optional[str] = None
#     money_close: Optional[str] = None
#     tax_close: Optional[str] = None
#     #time_close: Optional[str] = None
#     price: Optional[str] = None
#     order_id_close: Optional[str] = None
#     basePrice: Optional[str] = None
#     triggerPrice: Optional[str] = None