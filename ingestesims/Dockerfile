FROM public.ecr.aws/lambda/python:3.8 as refresh-dropbox

# Copy Resources to image
RUN mkdir ${LAMBDA_TASK_ROOT}/lib
ADD ./ingestesims ${LAMBDA_TASK_ROOT}/ingestesims
COPY ./lib ${LAMBDA_TASK_ROOT}/lib

# Set Working Directory
WORKDIR ${LAMBDA_TASK_ROOT}/ingestesims

# Install requirements
RUN python3 -m pip install --upgrade pip
RUN python3 -m ensurepip
RUN pip install -r requirements.txt --no-deps

# Set Python Path
ENV PYTHONPATH "${PYTHONPATH}:${LAMBDA_TASK_ROOT}/ingestesims"

# Run lambda
CMD ["ingest_esims.main.handler"]
