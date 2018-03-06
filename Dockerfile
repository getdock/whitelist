FROM python:3.6
EXPOSE 80
WORKDIR /app
CMD ["/app/start.sh"]

# Install magicwand
ADD app/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

ADD app /app
