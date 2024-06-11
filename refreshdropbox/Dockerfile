FROM public.ecr.aws/lambda/python:3.8 as refresh-dropbox

# Copy Resources to image
RUN mkdir ${LAMBDA_TASK_ROOT}/lib
ADD ./refreshdropbox ${LAMBDA_TASK_ROOT}/refreshdropbox
COPY ./lib ${LAMBDA_TASK_ROOT}/lib

# Set Working Directory
WORKDIR ${LAMBDA_TASK_ROOT}/refreshdropbox

# Install dependencies
RUN yum -y update \
    && yum -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm \
    && yum makecache \
    && yum -y install zbar \
    && yum -y install tesseract

# Install requirements
RUN python3 -m pip install --upgrade pip
RUN python3 -m ensurepip
RUN pip install -r requirements.txt --no-deps

# Set Python Path
ENV PYTHONPATH "${PYTHONPATH}:${LAMBDA_TASK_ROOT}/refreshdropbox"

# Run lambda
CMD ["refresh_dropbox.main.handler"]

