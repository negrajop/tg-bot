import requests
import matplotlib.pyplot as plt
from datetime import datetime

from config import API_URL

response = requests.get(f"{API_URL}/moods", timeout=10)
response.raise_for_status()
data = response.json()

dates = [datetime.fromisoformat(item["date"]) for item in data]
values = [item["value"] for item in data]

plt.plot(dates, values)
plt.title("График самочувствия")
plt.xlabel("Дата")
plt.ylabel("Оценка")
plt.grid(True)
plt.tight_layout()
plt.savefig("mood_chart.png")
plt.show()