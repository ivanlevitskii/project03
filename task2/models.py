from abc import ABC, abstractmethod
import os
import requests
import json
from typing import List
from fastapi import HTTPException
from transformers import pipeline, AutoTokenizer, AutoModel
import logging
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import torch
# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseModel(ABC):
    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    def classify(self, text: str, departments: List[str]) -> str:
        pass

class DeepSeekClassifier:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = "https://api.deepseek.com/v1/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def classify(self, text: str, departments: List[str]) -> str:
        """
        Классифицирует обращение гражданина и определяет соответствующий департамент
        """
        prompt = f"""
        Проанализируй следующее обращение гражданина и определи, в какой департамент его нужно направить.
        Доступные департаменты: {', '.join(departments)}
        
        Обращение: {text}
        
        Ответь только названием департамента из списка.
        """
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "Ты - помощник по классификации обращений граждан. Твоя задача - определить, в какой департамент нужно направить обращение. Отвечай только названием департамента из предложенного списка."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,
            "max_tokens": 100
        }
        
        try:
            response = requests.post(self.url, headers=self.headers, json=data)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        except requests.exceptions.RequestException as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при обращении к DeepSeek API: {str(e)}"
            )
        except (KeyError, IndexError) as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при обработке ответа от DeepSeek: {str(e)}"
            )

class QwenModel(BaseModel):
    def classify(self, text: str, departments: List[str]) -> str:
        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        prompt = f"""
        Проанализируй следующее обращение гражданина и определи, в какой департамент его нужно направить.
        Доступные департаменты: {', '.join(departments)}
        
        Обращение: {text}
        
        Ответь только названием департамента из списка.
        """
        
        data = {
            "model": "qwen-turbo",
            "input": {
                "messages": [
                    {"role": "system", "content": "Ты - помощник по классификации обращений граждан."},
                    {"role": "user", "content": prompt}
                ]
            },
            "parameters": {
                "temperature": 0.1,
                "max_tokens": 100
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            return result["output"]["text"].strip()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка Qwen: {str(e)}")

class YandexGPTModel(BaseModel):
    def classify(self, text: str, departments: List[str]) -> str:
        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {self.api_key}"
        }
        
        prompt = f"""
        Проанализируй следующее обращение гражданина и определи, в какой департамент его нужно направить.
        Доступные департаменты: {', '.join(departments)}
        
        Обращение: {text}
        
        Ответь только названием департамента из списка.
        """
        
        data = {
            "modelUri": "gpt://b1gqs0e2qom8vq2a5q6s/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": 0.1,
                "maxTokens": "2000"
            },
            "messages": [
                {
                    "role": "system",
                    "text": "Ты - помощник по классификации обращений граждан."
                },
                {
                    "role": "user",
                    "text": prompt
                }
            ]
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            return result["result"]["alternatives"][0]["message"]["text"].strip()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка YandexGPT: {str(e)}")

class HuggingFaceClassifier:
    def __init__(self):
        self.model_name = "sberbank-ai/sbert_large_nlu_ru"
        try:
            logger.info(f"Инициализация модели {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
            logger.info("Модель успешно инициализирована")
        except Exception as e:
            logger.error(f"Ошибка при инициализации модели: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при инициализации модели: {str(e)}"
            )

    def get_embedding(self, text: str) -> np.ndarray:
        """Получение эмбеддинга текста"""
        inputs = self.tokenizer(text, padding=True, truncation=True, max_length=512, return_tensors="pt")
        with torch.no_grad():
            outputs = self.model(**inputs)
        return outputs.last_hidden_state.mean(dim=1).numpy()

    def classify(self, text: str, departments: List[str]) -> str:
        """
        Классифицирует обращение гражданина и определяет соответствующий департамент
        
        Args:
            text (str): Текст обращения
            departments (List[str]): Список доступных департаментов
            
        Returns:
            str: Название выбранного департамента или None, если не удалось определить
        """
        logger.info(f"Начало классификации текста: {text[:100]}...")

        # Описания департаментов
        department_descriptions = {
            "Департамент транспорта": """
                Отвечает за транспортную инфраструктуру, дороги, общественный транспорт, 
                парковки, светофоры, дорожные знаки, ремонт дорог, транспортные развязки, 
                мосты, туннели, велодорожки, остановки, автобусы, трамваи, метро, такси.
            """,
            "Департамент культуры": """
                Отвечает за музеи, театры, библиотеки, культурные центры, выставки, 
                концерты, фестивали, парки культуры, художественные студии, творческие 
                кружки, культурные мероприятия, памятники, исторические здания, 
                культурное наследие, искусство, музыку, литературу.
            """,
            "Департамент здравоохранения": """
                Отвечает за больницы, поликлиники, медицинские центры, аптеки, 
                медицинское обслуживание, здоровье населения, профилактику заболеваний, 
                медицинские услуги, врачей, медсестер, медицинское оборудование, 
                вакцинацию, диспансеризацию.
            """,
            "Департамент образования": """
                Отвечает за школы, детские сады, университеты, колледжи, образовательные 
                программы, учебные заведения, образование детей и взрослых, курсы, 
                обучение, преподавателей, учебные материалы, образовательные стандарты.
            """,
            "Департамент экологии": """
                Отвечает за охрану окружающей среды, уборку мусора, озеленение, 
                экологические программы, чистоту города, переработку отходов, 
                экологическое образование, защиту природы, экологические нормы, 
                мониторинг окружающей среды.
            """,
            "Департамент физической культуры и спорта": """
                Отвечает за спортивные объекты, стадионы, спортивные площадки, 
                бассейны, спортивные секции, физкультуру, спортивные мероприятия, 
                соревнования, тренировки, развитие спорта, спортивные программы.
            """
        }

        try:
            # Получаем эмбеддинг входного текста
            text_embedding = self.get_embedding(text)
            
            # Получаем эмбеддинги описаний департаментов
            department_embeddings = {
                dept: self.get_embedding(desc)
                for dept, desc in department_descriptions.items()
            }

            # Вычисляем косинусное сходство между текстом и описаниями департаментов
            similarities = {
                dept: cosine_similarity(text_embedding, dept_embedding)[0][0]
                for dept, dept_embedding in department_embeddings.items()
            }
            
            for dept, similarity in similarities.items():
                logger.info(f"Сходство с {dept}: {similarity:.4f}")

            # Выбираем департамент с наибольшим сходством
            max_similarity = max(similarities.values())
            if max_similarity < 0.3:  # Пороговое значение для уверенности в классификации
                logger.warning(f"Недостаточное сходство с любым департаментом (max: {max_similarity:.4f})")
                return None

            best_department = max(similarities.items(), key=lambda x: x[1])[0]
            logger.info(f"Выбран департамент: {best_department} (сходство: {max_similarity:.4f})")
            return best_department

        except Exception as e:
            logger.error(f"Ошибка при классификации: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при классификации обращения: {str(e)}"
            )

def get_model(model_name: str, api_key: str) -> BaseModel:
    """
    Фабрика для создания экземпляров моделей
    """
    models = {
        "deepseek": DeepSeekClassifier,
        "qwen": QwenModel,
        "yandexgpt": YandexGPTModel
    }
    
    if model_name not in models:
        raise ValueError(f"Неподдерживаемая модель: {model_name}")
    
    return models[model_name](api_key) 