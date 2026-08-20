FROM mcr.microsoft.com/azure-functions/python:4-python3.11

ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true \
    PYTHONPATH=/home/site/wwwroot

COPY processor/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the processor code as the root function app so function_app.py is found directly at /home/site/wwwroot
COPY processor/ /home/site/wwwroot/

# Also create a processor symlink/directory so imports like 'from processor.services...' continue to work
RUN ln -s /home/site/wwwroot /home/site/wwwroot/processor
