FROM python:3.12.3

WORKDIR /app

COPY requirement.txt .

RUN pip install --no-cache-dir --upgrade -r requirement.txt

COPY ./app /app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]