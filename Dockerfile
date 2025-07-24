# Use official Python image
FROM python:3.12

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY AstroMind.py ./AstroMind.py
COPY src/ ./src/
COPY dataset/ ./dataset/

# Expose Streamlit port
EXPOSE 8501

# Run the app
CMD ["streamlit", "run", "AstroMind.py", "--server.port=8501", "--server.address=0.0.0.0"]
