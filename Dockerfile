FROM python
RUN mkdir /usr/src/app
COPY ./urlcloud /usr/src/app/urlcloud
WORKDIR /usr/src/app
COPY requirements.txt .
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["uvicorn", "urlcloud.main:app","--host", "0.0.0.0", "--reload", "--proxy-headers"]