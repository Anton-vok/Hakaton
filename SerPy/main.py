import sys
import os
sys.path.append(r"C:\Users\Nimbl\source\repos\Hakaton project")

import json
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Настройка CORS, чтобы фронтендер мог подключиться со своего компьютера
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Функция загрузки данных из файла
def load_data():
    path_to_json = r"C:\Users\Nimbl\source\repos\Hakaton project\data.json"
    with open(path_to_json, "r", encoding="utf-8") as f:
        return json.load(f)

# Хелпер для разбора строки ЕГЭ: "rus:85,cs:90" -> {"rus": 85, "cs": 90}
def parse_subjects(subjects_str: str) -> dict:
    if not subjects_str:
        return {}
    result = {}
    pairs = subjects_str.split(",")
    for pair in pairs:
        if ":" in pair:
            subject, score = pair.split(":")
            result[subject.strip()] = int(score.strip())
    return result


# 1. Эндпоинт фильтров
@app.get("/api/filters-data")
def get_filters():
    return {
        "interests": [
            { "id": "cs", "label": "Компьютерные науки" },
            { "id": "dev", "label": "Разработка" },
            { "id": "other", "label": "Что то не крутое" }
        ],
        "specializations": [
            { "id": "spec1", "label": "Искусственный интеллект" },
            { "id": "spec2", "label": "Веб-разработка" },
            { "id": "spec3", "label": "Информационная безопасность" }
        ]
    }


# 2. Эндпоинт списка программ с фильтрацией и проверкой баллов ЕГЭ
@app.get("/api/programs")
def get_programs(
    filter: str = "relevance",
    interests: str = None,
    specs: str = None,
    subjects: str = None
):
    programs = load_data()
    user_scores = parse_subjects(subjects)
    
    selected_interests = interests.split(",") if interests else []
    selected_specs = specs.split(",") if specs else []
    
    filtered_programs = []
    
    for prog in programs:
        # Фильтрация по интересам
        if selected_interests:
            prog_int_ids = [i["id"] for i in prog.get("interests", [])]
            if not any(idx in prog_int_ids for idx in selected_interests):
                continue
                
        # Фильтрация по специализациям
        if selected_specs:
            prog_spec_ids = [s["id"] for s in prog.get("specializations", [])]
            if not any(idx in prog_spec_ids for idx in selected_specs):
                continue

        # Подсчет баллов ЕГЭ
        user_total = 0
        has_all_subjects = True
        
        for sub in prog.get("requiredSubjects", []):
            if sub in user_scores:
                user_total += user_scores[sub]
            else:
                has_all_subjects = False
        
        if not has_all_subjects:
            prog["isPassingBudget"] = False
            prog["isPassingPaid"] = False
        else:
            prog["isPassingBudget"] = user_total >= prog["budgetPoints"]
            prog["isPassingPaid"] = user_total >= prog["paidPoints"]
            
        filtered_programs.append(prog)
        
    # Сортировка
    if filter == "only-budget":
        filtered_programs = [p for p in filtered_programs if p.get("isPassingBudget")]
    elif filter == "first-budget":
        filtered_programs.sort(key=lambda x: x.get("isPassingBudget", False), reverse=True)

    return filtered_programs


# 3. Эндпоинт конкретной программы по ID
@app.get("/api/programs/{program_id}")
def get_program_by_id(program_id: int):
    programs = load_data()
    for prog in programs:
        if prog["id"] == program_id:
            return prog
    return {"error": "Program not found"}


# Автозапуск сервера
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
