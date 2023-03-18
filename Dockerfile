FROM python:3.10

WORKDIR /usr/src/app

COPY . .

RUN pip install git+https://github.com/weatherapicom/python.git
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "./bot.py"]