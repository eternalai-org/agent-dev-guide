# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the requirements file into the container at /usr/src/app
COPY requirements.txt ./

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /usr/src/app
COPY . .

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable
ENV OPENAI_API_KEY YOUR_API_KEY_HERE
# Users should replace YOUR_API_KEY_HERE with their actual key or set it during runtime

# Run server.py when the container launches
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
