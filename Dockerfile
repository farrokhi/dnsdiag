FROM python:3.13-alpine

WORKDIR /dnsdiag

ENV PATH "$PATH:/dnsdiag"

COPY . .

RUN pip install --no-cache-dir -r requirements.txt
