# Use a base image with Python and Flask installed
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install dependencies, including Gunicorn
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Flask application code into the container
COPY app.py .

# Expose the port your Flask app runs on
EXPOSE 5895

# Run the Flask app using Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5895", "app:app"]
