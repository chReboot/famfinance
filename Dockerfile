FROM python:3.12-slim
WORKDIR /app
COPY app/ .
RUN pip install flask pandas
VOLUME ["/data"]
CMD ["python","app.py"]
