FROM python:3.6.8

WORKDIR /root/src/clever

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./main.py" ]