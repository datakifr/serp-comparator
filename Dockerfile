# Use a base image with Python 3.10
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file into the working directory
COPY requirements.txt .

# Install the dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application into the working directory
COPY . .

# Expose port 10000 (for Render.com)
EXPOSE 10000

# Set the command to run the application on port 10000
CMD ["streamlit", "run", "app.py", "--server.port", "10000"]
