from fastapi import FastAPI
from db import get_moods

app = FastAPI()


@app.get("/moods")
def read_moods(start: str = None, end: str = None):
    data = get_moods(start, end)

    return [
        {"value": value, "date": date}
        for value, date in data
    ]