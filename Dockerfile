# Use the official Python image as a base image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Update the apt package index and install dependencies
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian bullseye main contrib non-free" > /etc/apt/sources.list \
    && echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian bullseye-updates main contrib non-free" >> /etc/apt/sources.list \
    && echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security bullseye-security main contrib non-free" >> /etc/apt/sources.list \
    && apt-get update && apt-get install -y \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Configure pip to use Tsinghua source
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# Install required Python packages
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python program into the container
COPY . /app

# Add a cron job to execute the script every hour and log to stdout
RUN echo "0 * * * *  /usr/local/bin/python /app/main.py --conf=/config/config.yaml >> /proc/1/fd/1 2>&1" > /etc/cron.d/mycron

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/mycron

# Apply the cron job
RUN crontab /etc/cron.d/mycron

# Start cron service in foreground and redirect logs
CMD ["cron", "-f"]
