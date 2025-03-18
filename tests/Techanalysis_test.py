import random
import pytest
from classes.tech_analysis.TechAnalysis import TechAnalysis
import allure

COINS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT",
         "ADAUSDT", "AVAXUSDT", "DOTUSDT", "LTCUSDT", "ATOMUSDT", "APEUSDT",
         "LINKUSDT", "NEARUSDT", "PEPEUSDT", "SHIBUSDT", "IMXUSDT", "TONUSDT",
         "SANDUSDT", "XLMUSDT", "HBARUSDT", "MNTUSDT", "SWEATUSDT", "TRXUSDT", "DOGSUSDT"]

TIMEFRAMES_BYBIT = ["1", "3", "5", "15", "30", "60", "120", "240", "360", "720", "D", "M", "W"]
TIMEFRAMES_TV = ["1m", "5m", "15m", "30m", "1h", "2h", "4h", "1d", "1W", "1M"]
RANDOM_COIN = COINS[random.randint(0, len(COINS) - 1)]
#RANDOM_TIMEFRAME = TIMEFRAMES_TV[random.randint(0, len(TIMEFRAMES_TV) - 1)]
RANDOM_TIMEFRAME = random.choice(TIMEFRAMES_TV)

class TestTechAnalysis:
    @allure.title("test_check_volumes")
    @allure.description("Тест функции проверки объемов check_volumes")
    #@pytest.mark.parametrize('timeframe', TIMEFRAMES_BYBIT)
    def test_check_volumes(self):
        #rand_coin = COINS[random.randint(0, len(COINS) - 1)]
        #rand_interval = TIMEFRAMES[random.randint(0, len(TIMEFRAMES) - 1)]
        rand_count = random.randint(1, 1001)
        actual_result = TechAnalysis.check_volumes(RANDOM_COIN, random.choice(TIMEFRAMES_BYBIT), rand_count)
        print(actual_result)
        assert isinstance(actual_result, bool), "Тест на проверку объемов не выполнен"


    @pytest.mark.parametrize('volumes', [
        pytest.param([100.2, 200.12, 300.12], id="volumes_high"),
        pytest.param([40.0, 50.0, 60.0, 70.0], id="volumes_low")
    ])
    @allure.title("test_avg_volume")
    @allure.description("Тест функции расчета среднего объема avg_volume")
    def test_avg_volume(self, volumes: list[float]):
        actual_result = TechAnalysis.avg_volume(volumes)
        expected_result = round(sum(volumes)/len(volumes), 3)
        assert isinstance(expected_result, float)
        assert actual_result == expected_result

    @allure.title("test_determine_trend")
    @allure.description("Тест функции для определения тренда на разных таймфреймах")
    def test_determine_trend_ema(self):
        expected_result = ["Bull", "Bear", "Flat"]
        actual_result = TechAnalysis.determine_trend_ema(RANDOM_COIN, RANDOM_TIMEFRAME)
        assert actual_result in expected_result

