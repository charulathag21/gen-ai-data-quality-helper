# Use official Python image
FROM python:3.10

# Install system deps (safe, minimal)
RUN apt-get update && apt-get install -y build-essential libffi-dev && apt-get clean

# Set work directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt /app/

# Install required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend code
COPY . /app/

# FastAPI runs on port 7860 in HF Spaces
EXPOSE 7860

# Run FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
