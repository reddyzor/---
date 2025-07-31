import requests
import json
from datetime import datetime
import os
from docx import Document
import pandas as pd


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

    def _load_triggers_courses(self, triggers_file_path):
        """Загружает курсы из файла триггеров"""
        try:
            df = pd.read_excel(triggers_file_path)
            df = df.fillna('')
            
            courses_dict = {}
            for _, row in df.iterrows():
                comp = row.get('компетенция', '').strip()
                indicator = row.get('Поведенческие проявления (индикаторы)', '').strip()
                courses = row.get('курсы', '').strip()
                
                if comp and courses:
                    key = f"{comp} - {indicator}" if indicator else comp
                    course_list = [c.strip() for c in courses.split(',') if c.strip()]
                    if course_list:
                        courses_dict[key] = course_list
            
            return courses_dict
        except Exception as e:
            print(f"Ошибка загрузки курсов из триггеров: {e}")
            return {}

    def _extract_competencies_from_report(self, report_text):
        """Извлекает компетенции с низкими баллами из отчета"""
        low_score_competencies = []
        lines = report_text.split('\n')
        
        for line in lines:
            # Ищем строки с компетенциями (с эмодзи или без)
            if ('🔴' in line or '🟡' in line or '🟢' in line) and '**' in line:
                # Извлекаем название компетенции
                comp_name = line.split('**')[1].split('**')[0]
                low_score_competencies.append(comp_name)
            # Также ищем строки с "🏆" (заголовки компетенций)
            elif '🏆' in line and ' - средний балл' in line:
                comp_name = line.split('🏆')[1].split(' - средний балл')[0].strip()
                low_score_competencies.append(comp_name)
        
        return low_score_competencies

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
            "max_tokens": 1500,
            "repetition_penalty": 1.0
        }

        response = requests.post(self.api_chat_url, headers=headers, json=payload, verify=False)
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            return f"Ошибка анализа встречи: {response.status_code} - {response.text}"

    def analyze_meeting_with_file(self, file_path=None, user_id=None):
        """Анализ встречи с уже загруженным файлом пользователя (без повторной загрузки)"""
        # Если file_path не передан — ищем trans.docx в temp_files/{user_id}/trans.docx
        if file_path is None:
            if user_id is None:
                return "❌ Ошибка: Не указан путь к файлу и user_id."
            file_path = f"temp_files/{user_id}/trans.docx"
        if not self.is_token_valid() and not self.get_access_token():
            return "Ошибка: не удалось получить токен доступа"

        # Чтение текста встречи из файла
        try:
            trans = self.read_docx(file_path)
        except Exception as e:
            return f"Ошибка чтения файла: {str(e)}"

        # Ограничиваем размер текста встречи (максимум 6000 символов)
        if len(trans) > 6000:
            trans = trans[:6000] + "\n\n[Текст обрезан для экономии места]"

        # Читаем отчет по компетенциям (обязательно)
        competency_report = ""
        try:
            if os.path.exists('REPORT.txt'):
                with open('REPORT.txt', 'r', encoding='utf-8') as f:
                    full_report = f.read()
                    # Ограничиваем размер отчета (максимум 3000 символов)
                    if len(full_report) > 3000:
                        competency_report = full_report[:3000] + "\n\n[Отчет обрезан для экономии места]"
                    else:
                        competency_report = full_report
            else:
                return "❌ Ошибка: Файл REPORT.txt не найден. Сначала выполните анализ компетенций."
        except Exception as e:
            return f"❌ Ошибка чтения отчета компетенций: {str(e)}"

        # Загружаем курсы из файла триггеров
        triggers_file_path = 'triggers.xlsx'
        if not os.path.exists(triggers_file_path):
            return "❌ Ошибка: Файл triggers.xlsx не найден."
        
        courses_dict = self._load_triggers_courses(triggers_file_path)
        
        # Извлекаем компетенции с проблемами из отчета
        problem_competencies = self._extract_competencies_from_report(competency_report)
        
        # Формируем строку с актуальными курсами
        courses_text = ""
        if courses_dict and problem_competencies:
            courses_text = "\n\n📚 ДОСТУПНЫЕ КУРСЫ ДЛЯ РЕКОМЕНДАЦИЙ:\n"
            for comp in problem_competencies:
                # Ищем курсы для этой компетенции
                for key, courses in courses_dict.items():
                    if comp.lower() in key.lower():
                        courses_text += f"- {comp}:\n"
                        for course in courses:
                            courses_text += f"  • {course}\n"
                        break

        prompt = f"""Проанализируй текст встречи и отчет по компетенциям, затем сформируй детальные рекомендации:

# ДЕТАЛЬНЫЕ РЕКОМЕНДАЦИИ ПО РАЗВИТИЮ

## Анализ встречи и компетенций

[Проанализируй стиль общения, структуру встречи, вовлеченность участников]

## РЕКОМЕНДАЦИИ ПО КОМПЕТЕНЦИЯМ

### Приоритетные компетенции для развития:

{courses_text}

КРИТИЧЕСКИ ВАЖНО: Используй ТОЛЬКО курсы из списка выше для рекомендаций. НЕ придумывай новые курсы. Если для компетенции нет курсов в списке, не указывай курсы вообще.

1. **[Название компетенции]** - [Балл/10]
   - 📊 **Текущий уровень:** [Описание текущего состояния]
   - 📚 **Курсы для изучения:**
     - [Используй ТОЛЬКО курсы из списка выше, если они есть]
   - 💡 **Практические рекомендации:**
     - [Конкретная рекомендация 1]
     - [Конкретная рекомендация 2]
   - 🎯 **Ожидаемый результат:** [Что изменится после развития]

2. **[Название компетенции]** - [Балл/10]
   - 📊 **Текущий уровень:** [Описание текущего состояния]
   - 📚 **Курсы для изучения:**
     - [Используй ТОЛЬКО курсы из списка выше, если они есть]
   - 💡 **Практические рекомендации:**
     - [Конкретная рекомендация 1]
     - [Конкретная рекомендация 2]
   - 🎯 **Ожидаемый результат:** [Что изменится после развития]

## ОБЩИЕ РЕКОМЕНДАЦИИ ПО ВСТРЕЧЕ

### Что улучшить в проведении встреч:

1. [Рекомендация по структуре встречи]
2. [Рекомендация по коммуникации]
3. [Рекомендация по вовлечению участников]

## ПЛАН РАЗВИТИЯ НА БЛИЖАЙШИЙ МЕСЯЦ

### Неделя 1: [Фокус на конкретную компетенцию]
- [Конкретные действия]
- [Практические задания]

### Неделя 2: [Фокус на конкретную компетенцию]
- [Конкретные действия]
- [Практические задания]

---

Текст встречи:
{trans}

Краткий отчет по компетенциям:
{competency_report}
"""

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