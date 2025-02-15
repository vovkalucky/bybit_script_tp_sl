import random
import pytest
from classes.tech_analysis.TechAnalysis import TechAnalysis

COINS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT",
         "ADAUSDT", "AVAXUSDT", "DOTUSDT", "LTCUSDT", "ATOMUSDT", "APEUSDT",
         "LINKUSDT", "NEARUSDT", "PEPEUSDT", "SHIBUSDT", "IMXUSDT", "TONUSDT",
         "SANDUSDT", "XLMUSDT", "HBARUSDT", "MNTUSDT", "SWEATUSDT", "TRXUSDT", "DOGSUSDT"]

TIMEFRAMES = ["1", "3", "5", "15", "30", "60", "120", "240", "360", "720", "D", "M", "W"]

class TestTechAnalysis:
    @pytest.mark.parametrize('timeframe', TIMEFRAMES)
    def test_check_volumes(self, timeframe):
        rand_coin = COINS[random.randint(0, len(COINS) - 1)]
        #rand_interval = TIMEFRAMES[random.randint(0, len(TIMEFRAMES) - 1)]
        rand_count = random.randint(1, 1001)
        actual_result = TechAnalysis.check_volumes(rand_coin, timeframe, rand_count)
        print(actual_result)
        assert isinstance(actual_result, bool), "Тест на проверку объемов не выполнен"

    @pytest.mark.parametrize('volumes', [
        pytest.param([100.2, 200.12, 300.12], id="volumes_high"),
        pytest.param([40.0, 50.0, 60.0, 70.0], id="volumes_low")
    ])
    def test_avg_volume(self, volumes):
        actual_result = TechAnalysis.avg_volume(volumes)
        expected_result = round(sum(volumes)/len(volumes), 3)
        assert type(expected_result) == float
        assert actual_result == expected_result