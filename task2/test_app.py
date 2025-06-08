import streamlit as st
import requests
from typing import List, Optional, Dict, Any
from datetime import datetime

# Конфигурация страницы
st.set_page_config(
    page_title="Тестирование API Единого окна",
    page_icon="🏢",
    layout="wide"
)

# Заголовок
st.title("🏢 Тестирование API Единого окна")
st.markdown("---")

# Боковая панель с информацией
with st.sidebar:
    st.header("Информация")
    st.markdown("""
    Это тестовое приложение для проверки работы API Единого окна.
    
    ### Доступные департаменты:
    - Департамент транспорта
    - Департамент культуры
    - Департамент здравоохранения
    - Департамент образования
    - Департамент экологии
    - Департамент физической культуры и спорта
    """)

def get_departments() -> List[str]:
    """Получение списка департаментов"""
    try:
        response = requests.get("http://localhost:8000/departments")
        response.raise_for_status()
        return response.json()["departments"]
    except Exception as e:
        st.error(f"Ошибка при получении списка департаментов: {str(e)}")
        return []

def process_appeal(text: str, contact_info: str, theme: str) -> Optional[Dict[str, Any]]:
    """Отправка обращения на обработку"""
    try:
        response = requests.post(
            "http://localhost:8000/process_appeal",
            json={"text": text, "contact_info": contact_info}
        )
        if response.status_code == 400:
            st.warning(response.json().get("detail", "Не удалось определить департамент. Попробуйте переформулировать обращение."))
            return None
        response.raise_for_status()
        result = response.json()
        
        # Добавляем дополнительные поля
        result.update({
            "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "theme": theme,
            "department": result.get("department", "Не определен")
        })
        
        return result
    except Exception as e:
        st.error(f"Ошибка при обработке обращения: {str(e)}")
        return None

# Основной интерфейс
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Отправка обращения")
    
    # Поле для ввода темы обращения
    theme = st.text_input(
        "Тема обращения",
        placeholder="Введите тему обращения..."
    )
    
    # Поле для ввода текста обращения
    appeal_text = st.text_area(
        "Текст обращения",
        height=200,
        placeholder="Введите текст обращения (минимум 10 символов)..."
    )
    
    # Поле для контактной информации
    contact_info = st.text_input(
        "Контактная информация",
        placeholder="Email или телефон..."
    )
    
    # Кнопка отправки
    if st.button("Отправить обращение", type="primary"):
        if not theme:
            st.warning("Пожалуйста, укажите тему обращения")
        elif not appeal_text or len(appeal_text) < 10:
            st.warning("Текст обращения должен содержать минимум 10 символов")
        elif not contact_info:
            st.warning("Пожалуйста, укажите контактную информацию")
        else:
            with st.spinner("Обрабатываем обращение..."):
                result = process_appeal(appeal_text, contact_info, theme)
                if result:
                    st.success("✅ Обращение успешно обработано!")
                    
                    # Отображаем основные данные
                    st.markdown("### Данные обращения:")
                    st.markdown(f"**Дата:** {result['date']}")
                    st.markdown(f"**Тема:** {result['theme']}")
                    st.markdown(f"**Департамент:** {result['department']}")
                    
                    # Отображаем полные данные в раскрывающемся блоке
                    with st.expander("Показать полные данные"):
                        st.json(result)

with col2:
    st.subheader("Статус API")
    
    # Проверка доступности API
    try:
        departments = get_departments()
        if departments:
            st.success("✅ API доступен")
            st.markdown("### Доступные департаменты:")
            for dept in departments:
                st.markdown(f"- {dept}")
        else:
            st.error("❌ Не удалось получить список департаментов")
    except Exception as e:
        st.error(f"❌ API недоступен: {str(e)}")
        st.info("Убедитесь, что основное приложение запущено на http://localhost:8000") 