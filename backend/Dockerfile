# Use the official lightweight Python 3.11 image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Prevent Python from writing .pyc files and force stdout/stderr to stream directly to the terminal
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install essential system dependencies required for building psycopg2 (PostgreSQL driver)
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file first to leverage Docker cache layers
COPY requirements.txt .

# Upgrade pip and install all Python dependencies from requirements.txt
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the rest of your backend source code into the container
COPY . .

# Expose port 8000 so the React frontend and Nginx can communicate with it
EXPOSE 8000

# Default command to run the application 
# (Note: Your docker-compose.yml overrides this with --reload for development)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
