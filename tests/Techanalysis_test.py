import random
import pytest
from classes.tech_analysis.TechAnalysis import TechAnalysis
import allure
from tests.conftest import RANDOM_COIN, TIMEFRAMES_BYBIT, RANDOM_TIMEFRAME, RANDOM_TIMEFRAME_BYBIT


class TestTechAnalysis:
    @allure.title("test_check_volumes")
    @allure.description("Тест функции проверки объемов check_volumes")
    def test_check_volumes(self):
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

    @allure.title("test_detect_trend")
    @allure.description("Тест функции для определения тренда на разных таймфреймах")
    def test_detect_trend(self):
        expected_result = ["Bull", "Bear", "Flat"]
        actual_result = TechAnalysis.detect_trend(RANDOM_COIN, RANDOM_TIMEFRAME)
        print(f"[test_detect_trend] {RANDOM_COIN} {RANDOM_TIMEFRAME} {actual_result}")
        assert actual_result in expected_result

    @pytest.mark.parametrize('side', ("bear", "bull"))
    @allure.title("test_find_imbalance")
    @allure.description("Тест функции для определения имбаланса на разных таймфреймах")
    def test_find_imbalance(self, side):
        expected_result = [True, False]
        actual_result = TechAnalysis.find_imbalance(RANDOM_COIN, RANDOM_TIMEFRAME_BYBIT, side, 10, 0.8, 1)
        print(f"[test_find_imbalance] {RANDOM_COIN} {RANDOM_TIMEFRAME_BYBIT} {side} {actual_result}")
        assert actual_result in expected_result


