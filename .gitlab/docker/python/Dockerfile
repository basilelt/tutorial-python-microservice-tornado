FROM python:3.8-alpine

# Set the working directory to /app
WORKDIR /app

# Copy the project directory contents into the container at /app
COPY src /app

# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip && \
    pip install -r requirements.txt --no-cache-dir