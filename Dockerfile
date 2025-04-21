# Build phase: Install all build dependencies
FROM python:3.12-slim AS compile-image

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the requirements.txt and install the dependencies
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Final stage: lightweight image for app execution
FROM python:3.12-slim AS build-image

# Install only the necessary runtime libraries
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the packages installed from the previous step
COPY --from=compile-image /root/.local /root/.local

# Copy the rest of the application
COPY . .

# Set the PATH to run installed packages
ENV PATH=/root/.local/bin:$PATH

# Start command
CMD ["python", "main.py"]
