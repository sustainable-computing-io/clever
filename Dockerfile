FROM python:3.13.5

WORKDIR /root/src/clever

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./main.py" ]