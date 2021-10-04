FROM python:3.8-alpine

WORKDIR /dnsdiag

ENV PATH "$PATH:/dnsdiag"

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

