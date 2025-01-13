# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set environment variables to prevent Python from writing .pyc files and to buffer output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt file to the container
COPY requirements.txt /app/

# Install system dependencies (optional, depending on your app's needs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the container
COPY . /app/

# Expose the port the application listens on
EXPOSE 8080

# Define the entrypoint 
ENTRYPOINT ["python", "app.py"]

# Define the default command to run the application
CMD ["python", "app.py"]
