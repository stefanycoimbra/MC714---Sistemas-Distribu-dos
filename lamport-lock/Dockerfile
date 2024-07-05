# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY lamport_lock.py .

# Run lamport_lock.py when the container launches
CMD ["python", "lamport_lock.py"]
