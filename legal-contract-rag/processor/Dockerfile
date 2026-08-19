FROM mcr.microsoft.com/azure-functions/python:4-python3.14

ENV AzureWebJobsScriptRoot=/home/site/wwwroot/processor \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true \
    PYTHONPATH=/home/site/wwwroot

COPY processor/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY processor/ /home/site/wwwroot/processor/
