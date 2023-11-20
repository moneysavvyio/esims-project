FROM public.ecr.aws/lambda/python:3.8 as esims-router

# Copy Resources to image
ADD ./esimsrouter ${LAMBDA_TASK_ROOT}/esimsrouter

# Set Working Directory
WORKDIR ${LAMBDA_TASK_ROOT}/esimsrouter

# Install requirements
RUN python3 -m pip install --upgrade pip
RUN python3 -m ensurepip
RUN pip install -r requirements.txt --no-deps

# Set Python Path
ENV PYTHONPATH "${PYTHONPATH}:${LAMBDA_TASK_ROOT}/esimsrouter"

# Run lambda
CMD ["esims_router.main.handler"]

