FROM python:3.11-slim

WORKDIR /app

# Copy requirements first to leverage cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set default command - override CMD in compose if needed, but this is good default
CMD ["python", "simulation.py"]
