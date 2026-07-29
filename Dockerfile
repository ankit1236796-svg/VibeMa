# Use official Python image
FROM python:3.11-slim

# Install ALL dependencies for Playwright + Xvfb
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Xvfb
    xvfb \
    # Playwright dependencies
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    # Clean up
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium --with-deps

# Copy the rest of the code
COPY . .

# Create a startup script
RUN echo '#!/bin/bash\n\
# Clean up any existing Xvfb processes\npkill Xvfb 2>/dev/null || true\nrm -f /tmp/.X99-lock\n\
# Start Xvfb with a unique display\nXvfb :99 -screen 0 1024x768x24 -ac & \n\
# Wait for Xvfb to start\nsleep 2\n\
# Start the bot\nexec python bot.py' > start.sh && chmod +x start.sh

# Use the startup script
CMD ["./start.sh"]
