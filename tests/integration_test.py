import pytest
from classes.SpotOrders import SpotOrders


@pytest.mark.parametrize('side', ('Buy', 'Sell'))
def test_open_and_cancel_tp_sl_order(spot: SpotOrders, side):
    order = spot.tp_sl_order(side=side, money_for_one_order=6,take_profit=10, stop_loss=10)
    order = spot.get_info_about_tp_sl_order(order)
    response = spot.cancel_order(order.order_id_close)
    assert response == True