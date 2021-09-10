FROM python:3.8.12-buster
MAINTAINER leichgardt

COPY . /app
RUN chown -R www-data:www-data /app &&  \
    chmod 777 /var/log
RUN apt-get update &&  \
    apt-get install -y bash git build-essential nano
RUN pip install -U pip setuptools wheel &&  \
    pip install -r /app/requirements.txt &&  \
    git clone https://github.com/carpedm20/emoji.git /tmp/emoji &&  \
    cd /tmp/emoji &&  \
    python setup.py install &&  \
    rm -rf /tmp/emoji

ENV PYTHONPATH "/app:/app/src:${PYTHONPATH}"
EXPOSE 5421 8000
WORKDIR /app
USER www-data

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["bot"]
