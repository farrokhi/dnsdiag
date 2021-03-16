FROM python:3.8.2

WORKDIR /dnsdiag

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

