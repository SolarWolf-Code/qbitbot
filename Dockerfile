FROM python:3.11-slim-bullseye

# Path: /app
WORKDIR /app

# Copy over requirements.txt and qbitbot.py
COPY requirements.txt qbitbot.py ./

# Install dependencies
RUN pip install -r requirements.txt

# Run qbitbot.py
CMD ["python", "qbitbot.py"]