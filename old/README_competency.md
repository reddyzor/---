# Анализатор компетенций с использованием GigaChat

Этот проект предназначен для анализа компетенций на основе семантического сравнения фраз из транскрипта с триггерами из Excel файла через API GigaChat.

## Возможности

- 📊 Загрузка триггеров из Excel файла
- 📝 Извлечение фраз из DOCX транскрипта
- 🤖 Семантическое сравнение через GigaChat API
- 💾 Кэширование результатов для оптимизации
- 📈 Детальная статистика и отчеты
- 🎯 Настраиваемый порог сходства
- 📋 Экспорт результатов в CSV и JSON

## Установка

1. Установите зависимости:
```bash
pip install -r requirements_competency.txt
```

2. Настройте конфигурацию в `config.py`:
```python
GIGACHAT_API_KEY = "ваш_api_ключ_здесь"
```

## Структура файлов

### Входные файлы

- `triggers.xlsx` - Excel файл с триггерами
  - Колонка `trigger_text` - текст триггера
  - Колонка `competency` - название компетенции
  - Колонка `score` - балл за триггер

- `trans.docx` - DOCX файл с транскриптом

### Выходные файлы

Результаты сохраняются в папку `results/`:
- `matches_YYYYMMDD_HHMMSS.csv` - детальные совпадения
- `summary_YYYYMMDD_HHMMSS.csv` - сводная таблица
- `summary_YYYYMMDD_HHMMSS.json` - JSON отчет
- `stats_YYYYMMDD_HHMMSS.json` - статистика работы

## Использование

### Базовый анализ

```python
import asyncio
from competency_analyzer_advanced import AdvancedCompetencyAnalyzer

async def main():
    async with AdvancedCompetencyAnalyzer() as analyzer:
        # Загрузка данных
        triggers = analyzer.load_triggers("triggers.xlsx")
        phrases = analyzer.load_phrases("trans.docx")
        
        # Анализ
        matches = await analyzer.analyze_competencies(phrases, triggers)
        
        # Создание отчета
        summary = analyzer.create_summary(matches)
        analyzer.save_results(matches, summary)

asyncio.run(main())
```

### Запуск из командной строки

```bash
python competency_analyzer_advanced.py
```

## Конфигурация

Основные параметры в `config.py`:

```python
# API настройки
GIGACHAT_API_KEY = "ваш_ключ"
GIGACHAT_API_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

# Файлы
TRIGGERS_FILE = "triggers.xlsx"
TRANSCRIPT_FILE = "trans.docx"

# Порог сходства (0-100)
SIMILARITY_THRESHOLD = 85

# Папка для результатов
OUTPUT_DIR = "results"
```

## Алгоритм работы

1. **Загрузка данных**
   - Извлечение триггеров из Excel
   - Извлечение фраз из DOCX

2. **Семантическое сравнение**
   - Формирование промпта для каждой пары (фраза, триггер)
   - Отправка в GigaChat API
   - Получение оценки сходства (0-100)

3. **Фильтрация**
   - Отбор совпадений с score >= порог

4. **Агрегация**
   - Суммирование баллов по компетенциям
   - Расчет статистик

5. **Экспорт**
   - Сохранение детальных совпадений
   - Создание сводной таблицы

## Оптимизации

- **Кэширование**: Результаты сравнений сохраняются в памяти
- **Прогресс-бар**: Отображение прогресса обработки
- **Обработка ошибок**: Устойчивость к сбоям API
- **Статистика**: Детальная информация о работе

## Примеры отчетов

### Сводная таблица
```
competency          total_score  avg_score  avg_similarity  max_similarity  matches_count  percentage
Коммуникация        45.0         15.0       87.5           95              3              60.0
Лидерство           30.0         15.0       88.0           92              2              40.0
```

### Детальные совпадения
```
phrase                    trigger                    competency    score  similarity
"Я всегда слушаю..."     "Активное слушание"        Коммуникация  15     95
"В команде я..."         "Командная работа"          Лидерство     15     88
```

## Требования

- Python 3.7+
- pandas
- aiohttp
- python-docx
- openpyxl

## Поддержка

При возникновении проблем:
1. Проверьте правильность API ключа
2. Убедитесь в наличии входных файлов
3. Проверьте формат Excel файла (нужные колонки)
4. Посмотрите логи для диагностики ошибок 