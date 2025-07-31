import requests
import json
from datetime import datetime
import os
from docx import Document


class MeetingAnalyzer:
    def __init__(self, auth_key, scope, api_auth_url, api_chat_url):
        self.auth_key = auth_key
        self.scope = scope
        self.api_auth_url = api_auth_url
        self.api_chat_url = api_chat_url
        self.access_token = None
        self.token_expires = 0

    def get_access_token(self):
        headers = {
            'Authorization': f'Bearer {self.auth_key}',
            'RqUID': '6f0b1291-c7f3-43c6-bb2e-9f3efb2dc98e',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {'scope': self.scope}

        response = requests.post(self.api_auth_url, headers=headers, data=data, verify=False)
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data['access_token']
            self.token_expires = datetime.now().timestamp() + int(token_data['expires_at'])
            return True
        else:
            print(f"Ошибка получения токена: {response.status_code} - {response.text}")
            return False

    def is_token_valid(self):
        return self.access_token and datetime.now().timestamp() < self.token_expires

    def read_docx(self, file_path):
        """Чтение текста из файла .docx"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл {file_path} не найден")

        doc = Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return '\n'.join(full_text)

    def analyze_meeting(self):
        if not self.is_token_valid() and not self.get_access_token():
            return "Ошибка: не удалось получить токен доступа"

        # Чтение текста встречи из файла
        try:
            trans = self.read_docx('./trans.docx')
        except Exception as e:
            return f"Ошибка чтения файла: {str(e)}"

        prompt = f"""Проанализируй текст встречи и сформируй рекомендации в следующем формате:

Итоги ММ

Твой голос и речь были [позитивны/нейтральны/негативны], [доброжелательны/формальны/холодны], [располагающие к ОС/нейтральные/отталкивающие]. 
Ты вовлёк в обсуждение [N] из [M] присутствующих ММК. 
Ты [пропустил/не пропустил] важный этап - [не озвучил правила проведения ММ/озвучил правила]/участникам важно помнить формат обучения. 
В момент обсуждения [не озвучивались/озвучивались] персональные данные клиента, это [хорошо/плохо], Кибербезопасность превыше всего. 
[Соблюдён тайминг/Не соблюдён, потренируйся короче формулировать свои мысли]. 
[Один/Несколько/Никто] из [M] участников ММК [ФИО] погрузился в бизнес клиента, его задачи и планы. 
При этом [не погрузился/погрузился] в клиента, не узнал о его интересах и хобби. 
Уточняющие вопросы о клиенте задавали [N] из [M] ММК. 
Ты [не предложил/предложил] команде поиск решения, что [не позволило/позволило] тебе вовлечь всех сотрудников. 
При этом тобой [использовались слова паразиты (более 3 раз)/не использовал слова паразиты (более 3 раз)]. 
Ты [перебивал/не перебивал] речь [ФИО]. 
В итоге [ребята не сформулировали свою идею/предложения/сформулировали свои идеи]. 
[Были/Не было] признаков активного слушания. 
По итогам ММ [N] из [M] ребят не сформулировали ценность встречи. И не поделились своими мыслями.

Рекомендации РМ

Тебе необходимо:

1. [Рекомендация 1]
2. [Рекомендация 2]
3. [Рекомендация 3]
4. [Рекомендация 4]

Текст встречи для анализа:
{trans}"""

        return self._send_request(prompt)

    def _send_request(self, prompt):
        """Отправка запроса к GigaChat API"""
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        payload = {
            "model": "GigaChat",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "top_p": 0.9,
            "n": 1,
            "stream": False,
            "max_tokens": 4000,
            "repetition_penalty": 1.0
        }

        response = requests.post(self.api_chat_url, headers=headers, json=payload, verify=False)
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            return f"Ошибка анализа встречи: {response.status_code} - {response.text}"

    def analyze_meeting_with_file(self, file_path):
        """Анализ встречи с указанным файлом и создание расширенных рекомендаций"""
        if not self.is_token_valid() and not self.get_access_token():
            return "Ошибка: не удалось получить токен доступа"

        # Чтение текста встречи из файла
        try:
            trans = self.read_docx(file_path)
        except Exception as e:
            return f"Ошибка чтения файла: {str(e)}"

        # Читаем отчет по компетенциям (обязательно)
        competency_report = ""
        try:
            # Проверяем все возможные расположения файла отчета
            report_files = ['REPORT.txt', './REPORT.txt', 'REPORT_backup.txt', './REPORT_backup.txt']
            report_found = False
            
            print("🔍 Поиск файла отчета по компетенциям...")
            for report_file in report_files:
                abs_path = os.path.abspath(report_file)
                print(f"   Проверяю: {abs_path}")
                if os.path.exists(report_file):
                    print(f"✅ Найден файл: {report_file}")
                    with open(report_file, 'r', encoding='utf-8') as f:
                        competency_report = f.read()
                    report_found = True
                    break
                else:
                    print(f"❌ Файл не найден: {report_file}")
            
            if not report_found:
                # Показываем содержимое текущей директории
                current_dir = os.getcwd()
                print(f"\n📁 Текущая директория: {current_dir}")
                print("📂 Содержимое директории:")
                try:
                    for item in os.listdir('.'):
                        if os.path.isfile(item):
                            size = os.path.getsize(item)
                            print(f"   📄 {item} ({size} байт)")
                        else:
                            print(f"   📁 {item}/")
                except Exception as list_error:
                    print(f"   ❌ Ошибка чтения директории: {list_error}")
                
                return "❌ ОШИБКА: Файл отчета по компетенциям не найден!\n\n" + \
                       "🔧 РЕШЕНИЯ:\n" + \
                       "1. Сначала запустите анализ компетенций (search_optimized.py)\n" + \
                       "2. Убедитесь, что файл REPORT.txt создается в правильной директории\n" + \
                       "3. Проверьте права доступа к файлам\n" + \
                       f"4. Текущая рабочая директория: {current_dir}"
            
            # Анализируем отчет чтобы подсчитать количество компетенций
            competency_count = competency_report.count("🏆")
            print(f"📊 НАЙДЕНО КОМПЕТЕНЦИЙ В ОТЧЕТЕ: {competency_count}")
            
            # Извлекаем названия компетенций для вывода
            import re
            competencies = re.findall(r'🏆 (.+?) - средний балл', competency_report)
            print("📋 СПИСОК КОМПЕТЕНЦИЙ:")
            for i, comp in enumerate(competencies, 1):
                print(f"   {i}. {comp}")
            print(f"\n🎯 GigaChat должен создать рекомендации для ВСЕХ {competency_count} компетенций!")
                       
        except Exception as e:
            return f"❌ Ошибка чтения отчета компетенций: {str(e)}"

        prompt = f"""Проанализируй текст встречи и отчет по компетенциям, затем сформируй детальные рекомендации:

# ДЕТАЛЬНЫЕ РЕКОМЕНДАЦИИ ПО РАЗВИТИЮ

## Анализ встречи и компетенций

[Проанализируй стиль общения, структуру встречи, вовлеченность участников]

## РЕКОМЕНДАЦИИ ПО КОМПЕТЕНЦИЯМ

### Приоритетные компетенции для развития:

**ВАЖНО:** Проанализируй ВСЕ компетенции из отчета и создай рекомендации для КАЖДОЙ компетенции, найденной в отчете по компетенциям. Используй следующий формат для КАЖДОЙ компетенции:

**[Номер]. [Название компетенции]** - [ТОЧНЫЙ балл из отчета]/10
   - 📊 **Текущий уровень:** [Описание на основе найденных совпадений и балла]
   - 📚 **Курсы для изучения:** (ОБЯЗАТЕЛЬНО используй курсы из раздела "💡 РЕКОМЕНДОВАННЫЕ КУРСЫ (ИЗ EXCEL)" отчета)
     - [ТОЧНОЕ название курса из отчета] - [обоснование из Excel файла]
     - НЕ ДОБАВЛЯЙ курсы от себя - используй ТОЛЬКО из отчета!
   - 💡 **Практические рекомендации:**
     - [Конкретная рекомендация 1]
     - [Конкретная рекомендация 2]
     - [Конкретная рекомендация 3]
   - 🎯 **Ожидаемый результат:** [Что изменится после развития]
   - ❌ **Примеры негативных фраз из встречи:** (используй фразы из раздела "❌ НАЙДЕНО В ТЕКСТЕ (негативное)" в отчете)
     - Цитата: "[точная цитата из отчета]" → Мог бы сказать: "[конкретная альтернативная фраза]"
   - ✅ **Примеры позитивных фраз из встречи:** (используй фразы из раздела "✅ НАЙДЕНО В ТЕКСТЕ (позитивное)" в отчете)
     - Цитата: "[точная цитата из отчета]" - отлично сказано!

ОБЯЗАТЕЛЬНО создай рекомендации для ВСЕХ компетенций из отчета, даже если балл равен 0.

## ОБЩИЕ РЕКОМЕНДАЦИИ ПО ВСТРЕЧЕ

### Что улучшить в проведении встреч:

1. [Рекомендация по структуре встречи]
2. [Рекомендация по коммуникации]
3. [Рекомендация по вовлечению участников]

## ПЛАН РАЗВИТИЯ НА БЛИЖАЙШИЙ МЕСЯЦ

**ИНСТРУКЦИЯ:** Создай план развития, который охватывает ВСЕ компетенции из отчета. Распредели компетенции по неделям в зависимости от их количества и приоритетности:

### Неделя 1: [Название самой проблемной компетенции (с самым низким баллом)]
- [Конкретные действия для развития этой компетенции]
- [Практические задания]
- [Рекомендованные курсы на эту неделю]

### Неделя 2: [Название следующей компетенции по приоритету]
- [Конкретные действия для развития этой компетенции]
- [Практические задания]
- [Рекомендованные курсы на эту неделю]

### Неделя 3: [Название следующей компетенции или продолжение предыдущих]
- [Конкретные действия]
- [Практические задания]
- [Рекомендованные курсы на эту неделю]

### Неделя 4: [Закрепление всех компетенций или оставшиеся компетенции]
- [Интегрированные задания по всем компетенциям]
- [Практические задания]
- [Контрольные мероприятия]

**ПРИМЕЧАНИЕ:** Если компетенций больше 4, распредели их логично по неделям или создай дополнительные недели.

## МЕТРИКИ УСПЕХА

- [Измеримая цель 1]
- [Измеримая цель 2]
- [Измеримая цель 3]

---

**Текст встречи для анализа:**
{trans}

**Отчет по компетенциям:**
{competency_report}

**КРИТИЧЕСКИ ВАЖНО:** 
1. Обработай КАЖДУЮ компетенцию из отчета - НЕ пропускай ни одной!
2. Если видишь 4 компетенции в отчете - создай рекомендации для всех 4!
3. Если компетенций будет больше (5, 6, 7...) - обработай все!
4. ОБЯЗАТЕЛЬНО используй конкретные фразы из разделов "❌ НАЙДЕНО В ТЕКСТЕ (негативное)" и "✅ НАЙДЕНО В ТЕКСТЕ (позитивное)" для создания примеров "мог бы сказать так".
5. Начни ответ сразу с заголовка "# ДЕТАЛЬНЫЕ РЕКОМЕНДАЦИИ ПО РАЗВИТИЮ".

**СТРОГИЕ ПРАВИЛА ДЛЯ БАЛЛОВ И КУРСОВ:**
1. 🎯 БАЛЛЫ: Используй ТОЧНЫЕ баллы из отчета (например, если написано "средний балл 0.0" - пиши 0.0, если "-2.1" - пиши -2.1)
2. 📚 КУРСЫ: Используй ТОЛЬКО курсы из разделов "💡 РЕКОМЕНДОВАННЫЕ КУРСЫ (ИЗ EXCEL)" - НЕ добавляй свои!
3. 🚫 НЕ ПРИДУМЫВАЙ курсы от себя - если в отчете нет курсов для компетенции, напиши "Курсы не указаны в Excel файле"
4. 📊 НЕ ОКРУГЛЯЙ и НЕ ИЗМЕНЯЙ баллы - копируй их точно как в отчете

**ПРОВЕРЬ СЕБЯ:** 
- Количество компетенций = количеству в отчете
- Баллы точно скопированы из отчета  
- Курсы взяты только из отчета"""

        return self._send_request(prompt)


# Пример использования
if __name__ == "__main__":
    AUTH_KEY = 'ZGMzMGJmZjEtODQwYS00ZjAwLWI2NjgtNGIyNGNiY2ViNmE1OjYwNjM3NTU0LWQxMDctNDA5ZS1hZWM3LTAwYjQ5MjZkOGU2OA=='
    SCOPE = 'GIGACHAT_API_PERS'
    API_AUTH_URL = 'https://ngw.devices.sberbank.ru:9443/api/v2/oauth'
    API_CHAT_URL = 'https://gigachat.devices.sberbank.ru/api/v1/chat/completions'

    analyzer = MeetingAnalyzer(AUTH_KEY, SCOPE, API_AUTH_URL, API_CHAT_URL)

    try:
        analysis_result = analyzer.analyze_meeting()
        print("Результат анализа встречи:")
        print(analysis_result)

        # Сохранение результата в файл
        with open('meeting_analysis.txt', 'w', encoding='utf-8') as f:
            f.write(analysis_result)
        print("\nРезультат сохранён в файл meeting_analysis.txt")

    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")