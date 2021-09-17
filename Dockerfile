FROM i386/python:3.8.12-buster
MAINTAINER leichgardt
# copy project files and install environment
COPY . /app
RUN chown -R www-data:www-data /app &&  \
    chmod 777 /var/log &&  \
    touch /var/log/irobot.log &&  \
    touch /var/log/irobot-web.log  && \
    chown www-data:www-data /var/log/irobot*
RUN apt-get update &&  \
    apt-get install -y bash git build-essential nano
RUN pip install -U pip setuptools wheel &&  \
    pip install -r /app/requirements.txt &&  \
    git clone https://github.com/carpedm20/emoji.git /tmp/emoji &&  \
    cd /tmp/emoji &&  \
    python setup.py install &&  \
    rm -rf /tmp/emoji
# service parameters
ENV PYTHONPATH "/app:/app/src:${PYTHONPATH}"
EXPOSE 5421 8000
WORKDIR /app
USER www-data
# execution
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["bot"]
# to start the bot run in shell:
#   $ docker run <image> bot
# to start the web-app in shell:
#   $ docker run <image> web