FROM public.ecr.aws/lambda/python:3.8 as dropbox-connector

# Copy Resources to image
ADD ./dropboxconnector ${LAMBDA_TASK_ROOT}/dropboxconnector

# Set Working Directory
WORKDIR ${LAMBDA_TASK_ROOT}/dropboxconnector

# Install requirements
RUN python3 -m pip install --upgrade pip
RUN python3 -m ensurepip
RUN pip install -r requirements.txt --no-deps

# Set Python Path
ENV PYTHONPATH "${PYTHONPATH}:${LAMBDA_TASK_ROOT}/dropboxconnector"

# Run lambda
CMD ["dropbox_connector.main.handler"]
