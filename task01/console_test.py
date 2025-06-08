import requests
import json
from typing import Optional, Dict, Any
import sys

class ConsoleTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def get_departments(self) -> Optional[list]:
        """Получение списка департаментов"""
        try:
            response = requests.get(f"{self.base_url}/departments")
            response.raise_for_status()
            return response.json()["departments"]
        except Exception as e:
            print(f"❌ Ошибка при получении списка департаментов: {str(e)}")
            return None

    def process_appeal(self, text: str, contact_info: str) -> Optional[Dict[str, Any]]:
        """Отправка обращения на обработку"""
        try:
            response = requests.post(
                f"{self.base_url}/process_appeal",
                json={"text": text, "contact_info": contact_info}
            )
            
            if response.status_code == 400:
                print(f"⚠️ {response.json().get('detail', 'Не удалось определить департамент')}")
                return None
                
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Ошибка при обработке обращения: {str(e)}")
            return None

    def print_menu(self):
        """Вывод меню"""
        print("\n=== Тестирование API Единого окна ===")
        print("1. Отправить обращение")
        print("2. Показать список департаментов")
        print("3. Выход")
        print("===================================")

    def run(self):
        """Запуск тестирования"""
        while True:
            self.print_menu()
            choice = input("\nВыберите действие (1-3): ").strip()

            if choice == "1":
                print("\n=== Отправка обращения ===")
                text = input("Введите текст обращения (минимум 10 символов): ").strip()
                
                if len(text) < 10:
                    print("❌ Текст обращения должен содержать минимум 10 символов")
                    continue
                    
                contact_info = input("Введите контактную информацию (email или телефон): ").strip()
                
                if not contact_info:
                    print("❌ Пожалуйста, укажите контактную информацию")
                    continue

                print("\nОтправка обращения...")
                result = self.process_appeal(text, contact_info)
                
                if result:
                    print("\n✅ Обращение успешно обработано!")
                    print(json.dumps(result, indent=2, ensure_ascii=False))

            elif choice == "2":
                print("\n=== Список департаментов ===")
                departments = self.get_departments()
                
                if departments:
                    for i, dept in enumerate(departments, 1):
                        print(f"{i}. {dept}")
                else:
                    print("❌ Не удалось получить список департаментов")
                    print("Убедитесь, что основное приложение запущено")

            elif choice == "3":
                print("\nДо свидания!")
                sys.exit(0)

            else:
                print("\n❌ Неверный выбор. Пожалуйста, выберите 1, 2 или 3")

            input("\nНажмите Enter для продолжения...")

if __name__ == "__main__":
    tester = ConsoleTester()
    try:
        tester.run()
    except KeyboardInterrupt:
        print("\n\nПрограмма завершена пользователем")
        sys.exit(0) 