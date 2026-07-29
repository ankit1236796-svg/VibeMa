FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
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

# Copy requirements FIRST
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium --with-deps

# Copy the rest of the code
COPY . .

# Start script
RUN echo '#!/bin/bash\nrm -f /tmp/.X99-lock\npkill Xvfb 2>/dev/null || true\nXvfb :99 -screen 0 1024x768x24 & \nsleep 2\npython bot.py' > start.sh && chmod +x start.sh

CMD ["./start.sh"]
