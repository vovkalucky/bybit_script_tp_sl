from db.queries.orm import BaseOrm, CoinsOrm, DealsOrm

#BaseOrm.create_tables()

#CoinsOrm.select_coins()
print(DealsOrm.select_open_deals())

# query = insert(Deals).values(coin=symbol, order_id_buy=order_id_buy, order_id_sell=order_id_sell,
#                              money_buy=round(float(money_buy), 3), tax_buy=round(float(tax_buy), 3),
#                              money_sell=round(float(money_sell), 3), tax_sell=round(float(tax_sell), 3),
#                              status=status, time_open=time_sell, time_close=0, time_in_deal=0)

# DealsOrm.append_deal(coin="LTCUSDT", order_id_buy="1234567890", order_id_sell="0987654321",
#                      money_buy="214.323", tax_buy="0.002344", money_sell="0.0", tax_sell="0.0", status="Filled")
# DealsOrm.append_deal(coin="ETHUSDT", order_id_buy="1234567", order_id_sell="09876543",
#                      money_buy="214.323", tax_buy="0.002344", money_sell="0.0", tax_sell="0.0", status="Untrigerred")

#DealsOrm.find_deal_for_update("LTCUSDT", "Filled")

#DealsOrm.update_deal("LTCUSDT", "End", "1442.24", "325.34")
