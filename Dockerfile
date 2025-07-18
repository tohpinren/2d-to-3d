# Stage 1: Builder
FROM nvidia/cuda:12.9.1-cudnn-runtime-ubuntu22.04 AS builder

RUN apt-get update && \
    apt-get install -y git curl python3.11 python3.11-distutils python3.11-venv \
    python3.11-dev build-essential cmake ninja-build && \
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    ln -sf /usr/local/bin/pip3.11 /usr/bin/pip3 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY wonder3d   /app/wonder3d
COPY dreamgaussian /app/dreamgaussian
COPY make_mesh.py requirements.txt /app/

# install all python deps (compile here)
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install torch==2.3.0+cu121 torchvision==0.18.0+cu121 --index-url https://download.pytorch.org/whl/cu121


# Stage 2: Runtime container (slim)
FROM nvidia/cuda:12.9.1-cudnn-runtime-ubuntu22.04

RUN apt-get update && \
    apt-get install -y python3.11 python3.11-distutils python3.11-venv curl && \
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    ln -sf /usr/local/bin/pip3.11 /usr/bin/pip3 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# copy installed deps from builder
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

ENV PYTHONUNBUFFERED=1
ENV WGHT_DIR=/weights

ENTRYPOINT ["python", "make_mesh.py"]
