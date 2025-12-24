from pybit import exceptions
from classes.SpotOrders import SpotOrders
from classes.TlgSendMessage import TlgSendMessage
from db.queries.orm import CoinsOrm, DealsOrm
from settings import MONEY_FOR_ONE_ORDER, TAKE_PROFIT, MAX_COUNT_OF_DEALS, STOP_LOSS, COIN_COOLDOWN_HOURS
from classes.strategy.gpt import AnalysisCoin


class TradeManager:
    @staticmethod
    def check_deal_limits() -> bool:
        """Проверяет общий лимит активных сделок"""
        spot_orders = SpotOrders(symbol="DOGEUSDT")
        list_of_deals = DealsOrm.select_open_deals()
        active_deals = spot_orders.check_orders_status(list_of_deals)

        if len(active_deals) >= MAX_COUNT_OF_DEALS:
            print(f"🤖 Бот уже участвует в {len(active_deals)}/{MAX_COUNT_OF_DEALS} сделках(е)!\n"
                  f"⏳ Подождите, пока закроется хотя бы одна из них")
            return False
        return True

    def find_and_execute_trade(self) -> None:
        """Находит и исполняет сделку с учетом всех ограничений"""
        # Проверка общего лимита сделок
        if not TradeManager.check_deal_limits():
            return

        # Получаем свежий список доступных монет
        available_coins = CoinsOrm.select_coins()

        if not available_coins:
            print("⏳ Нет доступных монет для торговли (все в задержке или достигли лимита)")
            return

        print(f"✅ Доступно монет для анализа: {len(available_coins)}")
        print(f"📋 Список: {', '.join(available_coins)}")

        # Анализируем каждую доступную монету
        for pair in available_coins:
            # Дополнительная проверка перед анализом
            if not CoinsOrm.can_trade(pair):
                print(f"⚠️ {pair}: пропущена (не прошла проверку can_trade)")
                continue

            # Анализ монеты
            analysis = AnalysisCoin(pair)
            side = analysis.analyze_coin()

            if side in ["Buy", "Sell"]:
                print(f"🎯 Найден сигнал {side} для {pair}")

                # Попытка исполнить сделку
                if self.execute_trade(pair, side):
                    print(f"✅ Сделка по {pair} успешно открыта и зарегистрирована")
                    return  # Сигнал найден и сделка открыта, прекращаем поиск
                else:
                    print(f"❌ Не удалось открыть сделку по {pair}, продолжаем поиск...")

        print(f"🔴 Сигнал не найден для {len(available_coins)} доступных пар")

    @staticmethod
    def execute_trade(symbol: str, side: str) -> bool:
        """
        Исполняет сделку и регистрирует её в базе данных

        Returns:
            bool: True если сделка успешно открыта и зарегистрирована, False иначе
        """
        try:
            # Финальная проверка перед открытием сделки
            if not CoinsOrm.can_trade(symbol):
                print(f"⚠️ {symbol}: монета недоступна для торговли")
                return False

            # Открытие сделки на бирже
            print(f"📈 Открываем {side} позицию по {symbol}...")
            spot = SpotOrders(symbol=symbol)
            order_open = spot.tp_sl_order(side, MONEY_FOR_ONE_ORDER, TAKE_PROFIT, STOP_LOSS)

            if not order_open.order_id:
                print(f"⚠️ {symbol}: не удалось получить order_id")
                return False

            # Получение информации о заказе
            order = spot.get_info_about_tp_sl_order(order_open)

            if not order:
                print(f"⚠️ {symbol}: не удалось получить информацию о заказе")
                return False

            # Регистрация монеты в базе (с установкой задержки)
            if not CoinsOrm.add_coin(symbol):
                print(f"❌ {symbol}: не удалось зарегистрировать в базе")
                return False

            # Регистрация сделки в базе
            DealsOrm.append_deal(order)

            # Отправка уведомления в Telegram
            TlgSendMessage.send_tlg_message_new_tp_sl_order(order)

            return True

        except exceptions.InvalidRequestError as e:
            print(f"[execute_trade] ByBit API Request Error | {symbol} | {e.status_code} | {e.message}")
            return False

        except exceptions.FailedRequestError as e:
            print(f"[execute_trade] HTTP Request Failed | {symbol} | {e.status_code} | {e.message}")
            return False

        except Exception as e:
            print(f"[execute_trade] ❌ Ошибка при исполнении сделки для {symbol}: {e}")
            import traceback
            traceback.print_exc()
            return False