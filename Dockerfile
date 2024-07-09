FROM python:3.12
RUN mkdir /code
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./urlcloud /code/urlcloud
EXPOSE 8000
CMD ["uvicorn", "urlcloud.main:app", "--host", "0.0.0.0", "--reload"]