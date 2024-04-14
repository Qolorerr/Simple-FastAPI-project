FROM python:3.10.13-slim

RUN apt-get update && apt-get install -y iproute2 systemd

WORKDIR /banner_api

COPY requirements.txt .
RUN python3.10 -m venv venv
RUN . venv/bin/activate
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]