FROM mcr.microsoft.com/playwright/python:v1.55.0-jammy
WORKDIR /app
COPY . /app
RUN pip install playwright==1.55.0 requests
RUN playwright install