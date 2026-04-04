# Use an official Python image
FROM python:3.11.1

# Set the working directory inside the container
WORKDIR /app

# Copy requirements files
COPY requirements.txt .
COPY requirements-flask.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-flask.txt

# Copy the rest of the application
COPY . .

# Expose the correct port
EXPOSE 8000

# Start the application with 4 workers
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"] 