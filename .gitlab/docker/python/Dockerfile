FROM python:3.8-alpine

# Set the working directory to /app
WORKDIR /app

# Copy the project directory contents into the container at /app
COPY src /app

# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip==25.0.1 --no-cache-dir && \
    pip install setuptools==75.3.0 wheel==0.45.1 --no-cache-dir && \
    pip install -r requirements.txt --no-cache-dir --no-build-isolation