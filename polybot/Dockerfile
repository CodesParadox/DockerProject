FROM python:3.10-slim
WORKDIR /usr/src/app
RUN apt-get update && apt-get install -y gcc
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]




#Build the Docker image
#docker build -t polybot .

#Run the Docker container
#docker run -it --rm polybot

