FROM python:3.11-slim
WORKDIR /app
COPY web/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:8000", "--workers", "1"]
