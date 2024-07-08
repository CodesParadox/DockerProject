FROM python:3.8-slim
WORKDIR /usr/src/app
RUN apt-get update
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python3", "app.py"]




#Build the Docker image
#docker build -t polybot .

#Run the Docker container
#docker run -it --rm polybot

