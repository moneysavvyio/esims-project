FROM public.ecr.aws/lambda/python:3.8 as esims-router

# Copy Resources to image
RUN mkdir ${LAMBDA_TASK_ROOT}/lib
ADD ./esimsrouter ${LAMBDA_TASK_ROOT}/esimsrouter
COPY ./lib ${LAMBDA_TASK_ROOT}/lib

# Set Working Directory
WORKDIR ${LAMBDA_TASK_ROOT}/esimsrouter

# Install dependencies
RUN yum -y update \
    && yum -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm \
    && yum makecache \
    && yum -y install zbar

# Install requirements
RUN python3 -m pip install --upgrade pip
RUN python3 -m ensurepip
RUN pip install -r requirements.txt --no-deps

# Set Python Path
ENV PYTHONPATH "${PYTHONPATH}:${LAMBDA_TASK_ROOT}/esimsrouter"

# Run lambda
CMD ["esims_router.main.handler"]

