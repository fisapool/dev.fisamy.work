FROM gitpod/openvscode-server:latest

# Switch to root temporarily for package installation
USER root

# Install additional tools and dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    python3 \
    python3-pip \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install Coder CLI (fix the installation command)
RUN curl -fsSL https://coder.com/install.sh | sh -s -- --method=standalone

# Create workspace directory and set permissions
RUN mkdir -p /home/workspace && chown -R 1000:1000 /home/workspace

# Switch back to non-root user
USER 1000

# Set working directory
WORKDIR /home/workspace

# Expose port 3000
EXPOSE 3000

# Default command (will be overridden by Terraform)
CMD ["/openvscode-server/bin/openvscode-server", "--host", "0.0.0.0", "--port", "3000"]
