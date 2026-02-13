# Deployment Guide for Slack Bot on EC2

This guide details the steps to deploy the Slack Bot to an Amazon EC2 instance.

## Prerequisites

- An active AWS EC2 instance (Amazon Linux 2023 or Ubuntu).
- SSH access to the instance.
- The Git repository URL.
- Your Slack Bot tokens/environment variables.

## Cleaning up the Instance

### Option A: Cleaning up Docker (if you used Docker before)

If your instance already has files or running containers and you want a fresh start:

1.  **Stop and remove all containers:**

    ```bash
    docker stop $(docker ps -aq)
    docker rm $(docker ps -aq)
    ```

2.  **Clean up Docker system (images, networks, build cache):**

    ```bash
    docker system prune -a -f --volumes
    ```

### Option B: Cleaning up Legacy (Non-Docker) Version

If you were running the bot directly (without Docker), follow these steps to kill the processes and remove files.

1.  **Stop the running application:**

    ```bash
    # CAUTION: This commands kill all python and gunicorn processes.
    pkill -f python
    pkill -f gunicorn
    ```
    *If `pkill` is not found, you can find the Process ID (PID) with `ps aux | grep python` and use `kill -9 <PID>`.*

3.  **Remove the application files:**

    ```bash
    cd ~
    # WARNING: Verify the folder name before running rm -rf
    rm -rf slack_bot_le_v
    ```

## Step 1: Connect to your EC2 Instance

Open your terminal and SSH into your instance:

```bash
ssh -i /path/to/your-key.pem ec2-user@your-ec2-public-ip
```

*(Note: User might be `ubuntu` instead of `ec2-user` depending on your AMI.)*

## Step 2: Install Git and Docker

Since you are running **Ubuntu 24.04**, use `apt` to install packages.

**1. Update and Install Prerequisites:**

```bash
sudo apt-get update
sudo apt-get install -y git docker.io curl
```

**2. Configure Docker Permissions:**

```bash
sudo usermod -aG docker $USER
# You must log out and log back in for this to take effect!
exit
```

**3. Reconnect to your instance.**

**4. Install Docker Compose:**

```bash
mkdir -p ~/.docker/cli-plugins/
curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 -o ~/.docker/cli-plugins/docker-compose
chmod +x ~/.docker/cli-plugins/docker-compose
```

---

*(Reference for Amazon Linux users only: `sudo dnf update -y && sudo dnf install -y git docker`)*

## Step 3: Clone the Repository

Navigate to your desired directory and clone the repo:

```bash
cd ~
git clone https://github.com/Lalanne0/slack_bot_le_v.git
cd slack_bot_le_v
```

*(Note: creating a personal access token (PAT) might be required if the repo is private.)*

## Step 4: Configure Environment Variables

Create a `.env` file to store your secrets securely.

```bash
nano .env
```

Paste your environment variables into the editor:

```
SLACK_CHANNEL=your_slack_channel_id
SLACK_TOKEN=xoxb-your-slack-bot-token
```

Save and exit (`Ctrl+O`, `Enter`, `Ctrl+X`).

## Step 5: Build and Run

Start the application using Docker Compose. This will build the image and start the container in detached mode.

```bash
docker compose up -d --build
```

Check the status of your container:

```bash
docker compose ps
```

View logs if needed:

```bash
docker compose logs -f
```

## Step 6: Updating the Application

To update the bot with the latest code from GitHub:

1.  Pull the changes:

    ```bash
    git pull origin main
    ```

2.  Rebuild and restart the container:

    ```bash
    docker compose up -d --build
    ```

    This ensures the new code is packaged into the container and the service is restarted with minimal downtime.

## Troubleshooting

- **Permission Denied**: Ensure you added your user to the `docker` group and re-logged in.
- **Port Issues**: Ensure the Security Group for your EC2 instance allows Inbound traffic on Port 80 (since we mapped port 80 to 5000 in `docker-compose.yml`).

### "Address already in use" Error

If you see `failed to bind host port ... 0.0.0.0:80 ... address already in use`, it means another program is using port 80 (e.g., Nginx, Apache, or an old version of your bot).

**1. Find what is using port 80:**

```bash
sudo lsof -i :80
# OR
sudo netstat -lpnt | grep :80
```

**2. Stop the process:**

- If it's **Nginx**: `sudo systemctl stop nginx`
- If it's **Apache**: `sudo systemctl stop apache2`
- If it's a **Python/Gunicorn** process: `sudo kill <PID>` (replace `<PID>` with the process ID found in step 1).

**3. Retry starting Docker:**

```bash
docker compose up -d --build
```
