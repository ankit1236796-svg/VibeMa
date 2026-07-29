FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    xvfb \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium

# Copy code
COPY . .

# Start script (cleans up Xvfb before starting)
CMD ["sh", "-c", "rm -f /tmp/.X99-lock && pkill Xvfb || true && Xvfb :99 -screen 0 1024x768x24 & python bot.py"]
