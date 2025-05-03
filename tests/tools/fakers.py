from datetime import date, timedelta
from faker import Faker
#from data.data import Person
import random
import os

class Fake:
    """
    Класс-обертка над Faker, предоставляющий удобные методы генерации фейковых данных.
    """
    def __init__(self, faker: Faker):
        """
        Инициализирует объект Fake с экземпляром Faker.

        :param faker: Экземпляр Faker для генерации случайных данных.
        """
        self.faker = faker
    def rand_int(self, start: int = 15, end: int = 100):
        """
        Генерирует случайное целое число.

        :param start: Минимальное значение (по умолчанию -100).
        :param end: Максимальное значение (по умолчанию 100).
        :return: Случайное целое число в заданном диапазоне.
        """
        return self.faker.pyint(min_value=start, max_value=end)

    def date(self, start: timedelta = timedelta(days=-30), end: timedelta = timedelta()) -> date:
        """
        Генерирует случайную дату в заданном диапазоне.

        :param start: Начальный диапазон (по умолчанию -30 дней от текущей даты).
        :param end: Конечный диапазон (по умолчанию сегодняшняя дата).
        :return: Случайная дата в заданном диапазоне.
        """
        return self.faker.date_between(start_date=start, end_date=end)

    def money(self, start: float = -100, end: float = 100) -> float:
        """
        Генерирует случайную сумму денег.

        :param start: Минимальное значение (по умолчанию -100).
        :param end: Максимальное значение (по умолчанию 100).
        :return: Случайное число с плавающей запятой в заданном диапазоне.
        """
        return self.faker.pyfloat(min_value=start, max_value=end)

    def category(self) -> str:
        """
        Генерирует случайную категорию расходов.

        :return: Одна из предопределенных категорий ('food', 'taxi', 'fuel' и т.д.).
        """
        return self.faker.random_element(['food', 'taxi', 'fuel', 'beauty', 'restaurants'])

    def sentence(self) -> str:
        """
        Генерирует случайное описание операции.

        :return: Строка с описанием.
        """
        return self.faker.sentence()

    # def person(self) -> Person:
    #     """
    #     Генерирует случайное человека.
    #
    #     :return: Объект Person.
    #     """
    #     subjects = ["Hindi", "English", "Maths", "Physics", "Chemistry", "Biology", "Computer Science", "Commerce",
    #                 "Accounting", "Economics", "Arts", "Social Studies", "History", "Civics"]
    #     return Person(
    #         first_name=self.faker.first_name_male(),
    #         last_name=self.faker.last_name_male(),
    #         middle_name=self.faker.middle_name_male(),
    #         email=self.faker.email(),
    #         mobile=''.join(str(random.randint(0, 9)) for _ in range(10)),
    #         subject=random.sample(subjects, random.randint(0, 3)),
    #         current_address=self.faker.address(),
    #         permanent_address=self.faker.address(),
    #         age=random.randint(18, 80),
    #         salary=random.randint(15000, 250000),
    #         department=self.faker.company(),
    #         date_of_birth= "11 Oct 1990"
    #     )

    def generated_file(self):
        # path = rf'C:\Users\home\PycharmProjects\Page-Object-Model-Pattern\test{random.randint(10,100)}.txt'
        server_folder_path = os.getcwd()
        print(server_folder_path)
        path = os.path.join(server_folder_path, f'test{random.randint(10, 100)}.txt')
        file = open(path, 'w')
        file.write(f'{self.faker.sentence()}')
        file.close()
        return file.name, path

# Создаем глобальный экземпляр `fake`, который будем использовать в других модулях.
#fake = Fake(faker=Faker("ru_Ru"))

#print(fake.rand_int())
#print(fake.person())