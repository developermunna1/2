FROM python:3.11-slim

# Install system dependencies and Chrome
RUN apt-get update && apt-get install -y \
    wget \
    gnupg2 \
    unzip \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirement file first to leverage cache
COPY requirements.txt .

# Install python dependencies
# Note: customtkinter might fail if checks for tk, but usually it installs fine as a library
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Command to run the bot web server
CMD ["gunicorn", "-b", "0.0.0.0:10000", "app:app"]
