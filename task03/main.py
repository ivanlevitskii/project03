from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from models import HuggingFaceClassifier

app = FastAPI(
    title="Единое окно",
    description="API для обработки обращений граждан и их направления в соответствующие департаменты",
    version="1.0.0"
)

# Модель для входящего обращения
class Appeal(BaseModel):
    text: str = Field(..., min_length=10, description="Текст обращения гражданина")
    contact_info: str = Field(..., description="Контактная информация заявителя")

# Список департаментов
DEPARTMENTS = [
    "Департамент транспорта",
    "Департамент культуры",
    "Департамент здравоохранения",
    "Департамент образования",
    "Департамент экологии",
    "Департамент физической культуры и спорта"
]

# Инициализация классификатора
classifier = HuggingFaceClassifier()

@app.post("/process_appeal", 
    response_model=dict,
    summary="Обработать обращение гражданина",
    description="Принимает текст обращения и контактную информацию, определяет соответствующий департамент")
async def process_appeal(appeal: Appeal):
    try:
        # Определение департамента
        department = classifier.classify(appeal.text, DEPARTMENTS)
        if not department:
            raise HTTPException(
                status_code=400,
                detail="Не удалось определить подходящий департамент. Попробуйте переформулировать обращение."
            )
        
        return {
            "status": "success",
            "department": department,
            "message": f"Обращение направлено в {department}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )

@app.get("/departments",
    response_model=dict,
    summary="Получить список департаментов",
    description="Возвращает список всех доступных департаментов")
async def get_departments():
    return {"departments": DEPARTMENTS}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 