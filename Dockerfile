FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements_web.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements_web.txt

# Copy application files
COPY . .

# Expose port
EXPOSE 8501

# Run streamlit
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]