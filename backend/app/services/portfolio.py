import json
from pathlib import Path

from app.models.schemas import Portfolio


def load_portfolio(file_path: str = "data/portfolio.json") -> Portfolio:

    path = Path(file_path).resolve()

    print("Reading file:", path)
    print("File exists:", path.exists())

    with open(path, "rb") as file:
        raw_data = file.read()

    print("First bytes:", raw_data[:30])

    text = raw_data.decode("utf-8")

    data = json.loads(text)

    return Portfolio(**data)