import ccxt
import pandas as pd
import numpy as np
import ta  # Technical Analysis library

# Suppress warnings for cleaner output
import warnings

warnings.filterwarnings('ignore')


class AnalysisCoin:
    """
    Класс для анализа одной монеты и генерации сигнала на покупку.
    В данном случае адаптирован для использования в бэктестинге,
    принимая исторические данные как срез.
    """

    def __init__(self, pair):
        self.pair = pair

    def _calculate_indicators_for_backtest(self, df):
        """
        Вычисляет необходимые технические индикаторы на подмножестве данных.
        """
        if df.empty:
            return pd.DataFrame()

        df_copy = df.copy()

        # Экспоненциальные скользящие средние (EMA)
        df_copy['EMA_9'] = ta.trend.ema_indicator(df_copy['close'], window=9)
        df_copy['EMA_20'] = ta.trend.ema_indicator(df_copy['close'], window=20)

        # Индекс относительной силы (RSI)
        df_copy['RSI'] = ta.momentum.rsi(df_copy['close'], window=14)

        # Средний объем (используем SMA из ta.trend)
        df_copy['Volume_MA_20'] = ta.trend.sma_indicator(df_copy['volume'], window=20)

        # Удаляем строки с NaN значениями
        return df_copy.dropna()

    def analyze_coin(self, historical_data_slice: pd.DataFrame) -> str:
        """
        Анализирует последнюю свечу в переданном срезе исторических данных
        на предмет сигнала на покупку по скальпинг-стратегии.

        Args:
            historical_data_slice (pd.DataFrame): Срез исторических данных (OHLCV)
                                                 до текущей свечи включительно.

        Returns:
            str: "Buy", если найден сигнал на покупку, иначе пустая строка.
        """
        processed_klines = self._calculate_indicators_for_backtest(historical_data_slice)

        # Для корректного расчета всех индикаторов и сравнения с предыдущими значениями
        # требуется достаточное количество свечей (минимум 23: для EMA_20, RSI_14 и previous-bar сравнений)
        if processed_klines.empty or len(processed_klines) < 23:
            return ""

        latest = processed_klines.iloc[-1]  # Текущий (самый последний) бар
        previous = processed_klines.iloc[-2]  # Предыдущий бар (для наклона EMA и роста RSI/Close)

        # --- Условия для сигнала "Buy" (Обновленные) ---

        # 1. Сильный и устойчивый восходящий тренд (EMAs)
        condition1_1 = latest['EMA_9'] > latest['EMA_20']
        condition1_2 = latest['close'] > latest['EMA_9'] and latest['close'] > latest['EMA_20']

        ema9_sloping_up = latest['EMA_9'] > previous['EMA_9']
        ema20_sloping_up = latest['EMA_20'] > previous['EMA_20']

        # 2. Мощный бычий импульс
        condition2_1 = latest['close'] > latest['open']  # Текущая свеча бычья
        condition2_2 = latest['close'] > previous['close']  # Цена закрытия продолжает расти (импульс)

        condition2_3 = latest['RSI'] >= 55 and latest['RSI'] < 70  # RSI в зоне сильной покупки, но не перегрет
        condition2_4 = latest['RSI'] > previous['RSI']  # RSI должен показывать рост

        # 3. Подтверждение объемом
        condition3 = latest['volume'] > latest['Volume_MA_20']

        # Объединяем все условия для сигнала на покупку
        if (condition1_1 and condition1_2 and ema9_sloping_up and ema20_sloping_up and
                condition2_1 and condition2_2 and condition2_3 and condition2_4 and
                condition3):
            return "Buy"
        else:
            return ""


# --- Фреймворк для бэктестирования ---

def run_backtest(coins: list, start_date: str, end_date: str, initial_deposit: float = 10000):
    """
    Выполняет бэктестирование скальпинг-стратегии для списка монет.

    Args:
        coins (list): Список торговых пар (например, ["BTCUSDT", "ETHUSDT"]).
        start_date (str): Начальная дата бэктеста в формате 'YYYY-MM-DD HH:MM:SS'.
        end_date (str): Конечная дата бэктеста в формате 'YYYY-MM-DD HH:MM:SS'.
        initial_deposit (float): Начальный размер депозита в USD.

    Returns:
        str: "Passed_Backtest" если цели достигнуты, иначе "Failed_Backtest".
    """
    total_deposit = initial_deposit
    total_trades = 0
    winning_trades = 0
    losing_trades = 0
    total_profit_loss_usd = 0
    trade_logs = []

    # --- ВАЖНЕЙШЕЕ ПРЕДУПРЕЖДЕНИЕ ---
    print(f"\n{"!" * 80}")
    print("ВНИМАНИЕ: В этой версии стратегии ОТСУТСТВУЮТ STOP-LOSS И ВРЕМЕННОЙ STOP-LOSS.")
    print("Сделки закрываются ТОЛЬКО по Take Profit. Если TP не достигается, позиция УДЕРЖИВАЕТСЯ")
    print("БЕСКОНЕЧНО ДОЛГО В УБЫТКЕ, пока цена не вернется к точке входа + TP,")
    print("либо пока депозит не будет обнулен из-за блокировки капитала в убыточных позициях.")
    print("ЭТО КАТАСТРОФИЧЕСКИ РИСКОВАННАЯ СТРАТЕГИЯ, КОТОРУЮ НЕ СЛЕДУЕТ ИСПОЛЬЗОВАТЬ В РЕАЛЬНОЙ ТОРГОВЛЕ.")
    print("Она может привести к ПОЛНОЙ потере капитала.")
    print(f"{"!" * 80}\n")
    # --- КОНЕЦ ПРЕДУПРЕЖДЕНИЯ ---

    TAKER_FEE_RATE = 0.0005  # 0.05%
    SLIPPAGE_RATE = 0.0001  # 0.01%

    # Параметры стратегии выхода (обновленные)
    TAKE_PROFIT_PERCENT = 0.010  # 1.0% (по вашему запросу)
    # ЗДЕСЬ НЕТ STOP-LOSS И MAX_HOLD_CANDLES!

    print(f"Запуск бэктеста с {start_date} по {end_date} для {len(coins)} монет.")
    print(f"Начальный депозит: ${initial_deposit:.2f}")

    exchange = ccxt.bybit({'enableRateLimit': True, 'options': {'defaultType': 'spot'}})

    # --- Шаг 1: Загрузка всех исторических данных ---
    all_data = {}
    print("Загрузка исторических данных для всех монет...")
    for pair in coins:
        try:
            since_ms = exchange.parse8601(start_date)
            end_ms = exchange.parse8601(end_date)
            all_ohlcv = []

            while True:
                ohlcv_chunk = exchange.fetch_ohlcv(pair, '5m', since=since_ms, limit=1000)
                if not ohlcv_chunk:
                    break
                all_ohlcv.extend(ohlcv_chunk)
                last_timestamp_in_chunk = ohlcv_chunk[-1][0]
                since_ms = last_timestamp_in_chunk + 5 * 60 * 1000

                if last_timestamp_in_chunk >= end_ms:
                    break

            df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            all_data[pair] = df[
                (df['timestamp'] >= pd.to_datetime(start_date)) & (df['timestamp'] <= pd.to_datetime(end_date))]
            all_data[pair].set_index('timestamp', inplace=True)
            print(f"Загружено {len(all_data[pair])} свечей для {pair}.")
        except Exception as e:
            print(f"Не удалось загрузить данные для {pair}: {e}")
            all_data[pair] = pd.DataFrame()

            # --- Шаг 2: Итерация по свечам и симуляция торгов ---

    all_timestamps = pd.DatetimeIndex([])
    for pair_data in all_data.values():
        if not pair_data.empty:
            all_timestamps = all_timestamps.union(pair_data.index)
    all_timestamps = all_timestamps.sort_values()

    all_timestamps = all_timestamps[
        (all_timestamps >= pd.to_datetime(start_date)) & (all_timestamps <= pd.to_datetime(end_date))]

    coin_analyzers = {pair: AnalysisCoin(pair) for pair in coins}

    active_trades = []  # Список активных сделок, теперь без SL и MAX_HOLD

    for i, current_timestamp in enumerate(all_timestamps):
        if i % 1000 == 0:
            print(f"Обрабатывается временная метка: {current_timestamp} ({i}/{len(all_timestamps)})")

        current_deposit_at_step = total_deposit

        trades_to_remove = []
        for trade in active_trades:
            pair = trade['pair']

            if pair not in all_data or all_data[pair].empty or current_timestamp not in all_data[pair].index:
                continue

            current_candle = all_data[pair].loc[current_timestamp]
            # current_low = current_candle['low'] # Не используется без SL
            current_high = current_candle['high']
            # current_close = current_candle['close'] # Не используется без MAX_HOLD

            exit_reason = None
            exit_price = 0

            # Проверяем Take Profit (TP срабатывает, если HIGH >= TP)
            # Это единственный механизм выхода
            if current_high >= trade['take_profit']:
                exit_price = trade['take_profit']
                exit_reason = "TP"

            if exit_reason:
                trades_to_remove.append(trade)

                raw_profit_loss_percent = (exit_price - trade['entry_price']) / trade['entry_price']

                # Комиссии за вход и выход
                fees = (trade['entry_price'] * TAKER_FEE_RATE) + (exit_price * TAKER_FEE_RATE)
                fees_percent = fees / trade['entry_price']

                actual_profit_loss_percent = raw_profit_loss_percent - fees_percent
                profit_loss_usd = trade['trade_size_usd'] * actual_profit_loss_percent

                total_deposit += profit_loss_usd
                total_profit_loss_usd += profit_loss_usd

                if profit_loss_usd > 0:
                    winning_trades += 1
                else:
                    losing_trades += 1
                total_trades += 1

                trade_logs.append({
                    'timestamp': current_timestamp,
                    'pair': pair,
                    'action': 'SELL',
                    'entry_price': trade['entry_price'],
                    'exit_price': exit_price,
                    'profit_loss_percent': actual_profit_loss_percent * 100,
                    'profit_loss_usd': profit_loss_usd,
                    'exit_reason': exit_reason,
                    'trade_size_usd': trade['trade_size_usd'],
                    'remaining_deposit': total_deposit
                })

        for trade in trades_to_remove:
            active_trades.remove(trade)

        for pair in coins:
            if pair not in all_data or all_data[pair].empty:
                continue

            lookback_offset_seconds = 250 * 5 * 60
            data_start_time_for_slice = current_timestamp - pd.Timedelta(seconds=lookback_offset_seconds)

            current_historical_slice = all_data[pair].loc[data_start_time_for_slice:current_timestamp]

            if current_historical_slice.empty or len(current_historical_slice) < 60:
                continue

            current_candle_for_pair = None
            if current_timestamp in all_data[pair].index:
                current_candle_for_pair = all_data[pair].loc[current_timestamp]
            else:
                continue

            signal = coin_analyzers[pair].analyze_coin(current_historical_slice)

            if signal == "Buy":
                if any(t['pair'] == pair for t in active_trades):
                    continue

                entry_price_raw = current_candle_for_pair['close']
                entry_price = entry_price_raw * (1 + SLIPPAGE_RATE)

                trade_size_usd = current_deposit_at_step * 0.05  # Аллокация 5%

                if trade_size_usd < 10:
                    continue

                # Если нет свободного кэша для новой позиции, не открываем
                if total_deposit - sum(t['trade_size_usd'] for t in active_trades) <= 0:
                    continue

                take_profit = entry_price * (1 + TAKE_PROFIT_PERCENT)
                # БЕЗ СТОП-ЛОССА

                active_trades.append({
                    'pair': pair,
                    'entry_time': current_timestamp,
                    'entry_price': entry_price,
                    'take_profit': take_profit,
                    'trade_size_usd': trade_size_usd  # Размер позиции (не стоимость физ.монет)
                })
                trade_logs.append({
                    'timestamp': current_timestamp,
                    'pair': pair,
                    'action': 'BUY',
                    'entry_price': entry_price,
                    'profit_loss_percent': 0,
                    'profit_loss_usd': 0,
                    'exit_reason': 'N/A',
                    'trade_size_usd': trade_size_usd,
                    'remaining_deposit': total_deposit
                })

    # --- Учет оставшихся активных сделок в конце бэктеста ---
    # В этой стратегии они считаются "открытыми и удерживаемыми в убытке/прибыли"
    # Для целей отчетности бэктеста мы их "виртуально" закрываем по последней цене,
    # но это не является реальным закрытием по стратегии.
    total_unrealized_profit_loss = 0
    open_positions_value = 0
    unclosed_trades_count = len(active_trades)

    for trade in active_trades:
        pair = trade['pair']
        if pair in all_data and not all_data[pair].empty:
            last_price = all_data[pair]['close'].iloc[-1]

            # Это стоимость активов, которые мы все еще держим
            amount_of_coin = trade['trade_size_usd'] / trade['entry_price']
            current_value_of_position = amount_of_coin * last_price
            open_positions_value += current_value_of_position

            raw_profit_loss_usd = current_value_of_position - trade['trade_size_usd']
            # Здесь мы не вычитаем комиссии на "гипотетический" выход, т.к. сделка не закрыта
            total_unrealized_profit_loss += raw_profit_loss_usd

            # Не будем добавлять их в total_trades, winning_trades, losing_trades
            # поскольку они не закрыты по правилам стратегии (нет TP)

            # Добавим в лог, но с пометкой "Unrealized"
            trade_logs.append({
                'timestamp': all_timestamps[-1],
                'pair': pair,
                'action': 'UNREALIZED (Still Open)',
                'entry_price': trade['entry_price'],
                'exit_price': last_price,
                'profit_loss_percent': (raw_profit_loss_usd / trade['trade_size_usd']) * 100,
                'profit_loss_usd': raw_profit_loss_usd,
                'exit_reason': 'Still Open at End of Backtest',
                'trade_size_usd': trade['trade_size_usd'],
                'remaining_deposit': total_deposit  # Свободный депозит
            })

    # Итоговый депозит должен включать свободный кэш и стоимость открытых позиций
    final_equity = total_deposit + total_unrealized_profit_loss

    # --- Сводка результатов бэктеста ---
    print("\n--- Результаты Бэктеста ---")
    print(f"Период: {start_date} по {end_date}")
    print(f"Начальный депозит: ${initial_deposit:.2f}")
    print(f"Свободный депозит (кэш от закрытых сделок): ${total_deposit:.2f}")
    print(f"Количество незакрытых сделок на конец бэктеста: {unclosed_trades_count}")
    print(f"Виртуальная стоимость незакрытых позиций (на последнюю цену): ${open_positions_value:.2f}")
    print(f"Итоговая чистая стоимость капитала (Equity): ${final_equity:.2f}")

    net_profit_loss_usd = final_equity - initial_deposit
    print(f"Общая прибыль/убыток (Equity): ${net_profit_loss_usd:.2f}")

    duration_days = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days
    if duration_days > 0:
        if initial_deposit > 0:
            monthly_return_rate = (final_equity / initial_deposit - 1) * (30 / duration_days) * 100
        else:
            monthly_return_rate = 0
        print(f"Примерная месячная доходность (на основе Equity): {monthly_return_rate:.2f}%")
        goal_achieved_return = monthly_return_rate >= 5
    else:
        monthly_return_rate = 0
        print("Период слишком короткий для оценки месячной доходности.")
        goal_achieved_return = False

    print(f"\nВсего фактически закрытых сделок (по TP): {total_trades}")
    if total_trades > 0:
        print(f"Выигрышных сделок: {winning_trades}")
        # Проигрышных сделок (по стандартному SL) нет в этой стратегии
        # losing_trades_by_time = total_trades - winning_trades
        # print(f"Проигрышных сделок (по временному SL): {losing_trades_by_time}")
        win_rate = (winning_trades / total_trades) * 100
        print(f"Процент выигрышных сделок: {win_rate:.2f}%")

        avg_trades_per_day = total_trades / duration_days if duration_days > 0 else 0
        print(f"Среднее количество закрытых сделок в день: {avg_trades_per_day:.2f}")
        goal_achieved_frequency = avg_trades_per_day >= 5 and avg_trades_per_day <= 10
    else:
        print("Сделки не закрывались по TP.")
        win_rate = 0
        avg_trades_per_day = 0
        goal_achieved_frequency = False

    print(f"\nЦель в 5% месячной доходности: {'Достигнута' if goal_achieved_return else 'НЕ достигнута'}")
    print(
        f"Цель в 5-10 сделок/день: {'Достигнута' if goal_achieved_frequency and total_trades > 0 else 'НЕ достигнута'}")  # Учитываем, что сделки могут не закрываться

    if goal_achieved_return and goal_achieved_frequency:
        print("!!!!!! СТРАТЕГИЯ ПОКАЗАЛА РЕЗУЛЬТАТЫ, СООТВЕТСТВУЮЩИЕ ЦЕЛЯМ. !!!!!!")
        print("ОДНАКО ЕЩЕ РАЗ НАПОМИНАЮ О КАТАСТРОФИЧЕСКОМ РИСКЕ ТАКОЙ СТРАТЕГИИ В РЕАЛЬНОЙ ТОРГОВЛЕ.")
        return "Passed_Backtest (with extreme risk)"
    else:
        print("Стратегия НЕ соответствует заданным целям.")
        return "Failed_Backtest"


# --- Конфигурация для запуска ---
if __name__ == "__main__":
    # Список основных монет Bybit
    MAIN_BYBIT_COINS = [
        "BTCUSDT"
    ]

    # Период бэктеста: последние 30 дней для хорошей выборки
    end_date = pd.Timestamp.now(tz='UTC').strftime('%Y-%m-%d %H:%M:%S')
    start_date = (pd.Timestamp.now(tz='UTC') - pd.DateOffset(days=30)).strftime('%Y-%m-%d %H:%M:%S')

    print(f"Запуск бэктеста для {len(MAIN_BYBIT_COINS)} монет.")
    backtest_result = run_backtest(MAIN_BYBIT_COINS, start_date, end_date, initial_deposit=10000)

    print(f"\nИтоговый результат бэктеста: {backtest_result}")