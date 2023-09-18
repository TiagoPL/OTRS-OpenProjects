FROM python:3.10
WORKDIR /app
COPY ./app.py /app
COPY ./work_package_payload.py /app

RUN pip install --upgrade pip && pip install flask pyotrs pyopenproject

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0"]

# docker build -t nome-da-imagem .
# docker container run -dit -p 5000:5000 --name=nome-do-container -v /db:/db nome-da-imagem
