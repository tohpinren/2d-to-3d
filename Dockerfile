# ---- Base image with CUDA 12.3 runtime ----
FROM nvidia/cuda:12.9.1-cudnn-runtime-ubuntu22.04

# 1.  Essentials
RUN apt-get update && \
    apt-get install -y git curl python3.11 python3.11-distutils python3.11-venv \
    python3.11-dev build-essential cmake ninja-build && \
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    ln -sf /usr/local/bin/pip3.11 /usr/bin/pip3 && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# 2.  Copy code
COPY wonder3d   /app/wonder3d
COPY dreamgaussian /app/dreamgaussian
COPY make_mesh.py requirements.txt /app/

# 3.  Python deps
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install torch==2.3.0+cu123 torchvision==0.18.0+cu123 --index-url https://download.pytorch.org/whl/cu123

# 4.  Paths for weights (bind mount later)
ENV WGHT_DIR=/weights

# 5.  Entrypoint
ENTRYPOINT ["python","make_mesh.py"]
