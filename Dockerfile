FROM python:3.8-slim

WORKDIR /app
ENV LANG C.UTF-8
RUN apt-get update
RUN apt-get install 'ffmpeg'\
    'libsm6'\ 
    'libxext6'  -y

COPY requirements1.txt ./
RUN pip install --no-cache-dir -r requirements1.txt

COPY '.env' WORKDIR
COPY . .

# Make sure the environment is activated:
RUN echo "Make sure Torch and flask are installed:"
RUN python -c "import flask"
RUN python -c "import torch"
RUN python -c "import wikipedia"
RUN python -c "import googlemaps"

CMD gunicorn line-yolo-api:app --bind 0.0.0.0:${PORT:-8000}