FROM python:3

ARG VERSION=1

COPY ./gcalendar_ruz /gcalendar_ruz
COPY ./requirements.txt /

RUN pip install -r requirements.txt

CMD ["python", "/gcalendar_ruz/main.py"]
