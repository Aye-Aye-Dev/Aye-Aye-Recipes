FROM python:3.10-alpine
WORKDIR /app
COPY ./requirements.txt /app
RUN pip install -r requirements.txt
COPY . .
EXPOSE 2345
CMD ["python", "fossa_node.py"]
