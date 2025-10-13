import time
from functools import wraps
from pybit.exceptions import InvalidRequestError, FailedRequestError
from typing import Callable, Any


class TradeHelpsFunc:
    @staticmethod
    def count_digits_after_decimal(str_number: str) -> int:
        # Проверяем, есть ли точка в числе
        if '.' in str_number:
            # Разделяем строку на целую и дробную части
            integer_part, decimal_part = str_number.split('.')
            return len(decimal_part)  # Возвращаем длину дробной части
        else:
            return 0  # Если точки нет, то цифр после запятой нет

    @staticmethod
    def float_trunc(f: float, prec: int) -> str:
        """Отбросить от float лишние знаки без округлений, включая числа в научной нотации"""
        float_value = float(f)
        # Преобразуем число в строку в стандартной десятичной записи
        l, r = f"{float_value:.{prec + 12}f}".split('.')  # Увеличиваем точность для предотвращения потерь
        return f'{l}.{r[:prec]}'  # Возвращаем строку для точного результата

    @staticmethod
    def retry(max_retries: int = 3, delay: int = 5):
        """Декоратор для повторного вызова функции с заданным количеством попыток и задержкой."""

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs): #self,
                for attempt in range(1, max_retries + 1):
                    try:
                        return func(*args, **kwargs)  # Выполняем оригинальную функцию
                    except (InvalidRequestError, FailedRequestError) as e:
                        print(f"[{func.__name__}] API Error: {e.status_code} | {e.message}")
                    except Exception as e:
                        print(f"[{func.__name__}] Unexpected error: {e}")

                    if attempt < max_retries:
                        print(f"[{func.__name__}] Attempt {attempt} failed. Retrying in {delay} seconds...")
                        time.sleep(delay)
                print(f"[{func.__name__}] Failed after {max_retries} attempts.")
                return None
            return wrapper
        return decorator

    @staticmethod
    def retry_until_true(n: int, delay: float) -> Callable:
        """
        Декоратор, который повторяет вызов функции до тех пор,
        пока она не вернет True или не исчерпает попытки.

        Args:
            n: Максимальное количество попыток
            delay: Интервал между попытками (в секундах)
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> bool:
                for attempt in range(1, n + 1):
                    result = func(*args, **kwargs)
                    if result is True:
                        return True
                    if attempt < n:
                        print(f"[{func.__name__}] 🛑 Попытка {attempt} не удалась. Повторный запрос через {delay} секунд...")
                        time.sleep(delay)
                return False
            return wrapper
        return decorator

