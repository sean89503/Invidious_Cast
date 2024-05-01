# Stage 1: Build environment (same as before)

# Stage 2: Production environment (slim image)
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy all application code
COPY app.py /app
COPY main.py /app

# Health Check Module
COPY health_check.py /app

RUN pip install waitress
RUN pip install flask
RUN pip install yt_dlp

# Expose port (same as before)
EXPOSE 5895

# Command to run your script
CMD ["python", "main.py"]

# Health Check Configuration
HEALTHCHECK CMD ["python", "-c", "import health_check; health_check.update_health_status()"]
