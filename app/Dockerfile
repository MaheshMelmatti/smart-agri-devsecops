FROM python:3.11

WORKDIR /app

COPY . .

RUN pip install --timeout=120 --retries=5 -r requirements.txt

EXPOSE 5000

CMD ["gunicorn", "dashboard:app", "--bind", "0.0.0.0:5000"]