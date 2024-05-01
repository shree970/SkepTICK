FROM python:3.10

WORKDIR /code

COPY ./requirements.txt .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

EXPOSE 80

#COPY . .

#CMD ["gunicorn", "main:app","--timeout","300"]