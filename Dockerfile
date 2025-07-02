FROM mcr.microsoft.com/azure-functions/python:4-python3.12

WORKDIR /app

COPY requirements.txt .

# Instala herramientas de compilación
RUN apt-get update && apt-get install -y build-essential python3-dev

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 80

ENV AzureWebJobsScriptRoot=/app \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true

CMD ["func", "start"]