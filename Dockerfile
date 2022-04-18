#FROM i386/python:3.8.12-buster
FROM python:3.8.12-buster
MAINTAINER leichgardt

# copy project files and install environment
COPY . /app
RUN apt-get update &&  \
    apt-get install -y bash git build-essential nano tzdata
RUN pip install -U pip setuptools wheel &&  \
    pip install -r /app/requirements.txt

# service parameters
ENV TZ Asia/Irkutsk
ENV PYTHONPATH "/app:/app/src:${PYTHONPATH}"
EXPOSE 5421 8000
WORKDIR /app

# execution
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["bot"]
