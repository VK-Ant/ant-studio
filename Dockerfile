FROM python:3.12-slim

LABEL maintainer="Venkatkumar Rajan <venkatkumarr.vk99@gmail.com>"
LABEL description="Ant Studio - Local-first responsible AI pipeline tool"

WORKDIR /app

# System deps for PyMuPDF and matplotlib
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md LICENSE ./
COPY antstudio/ ./antstudio/
COPY data/ ./data/

RUN pip install --no-cache-dir -e ".[docker]"

# Default working directory for user data
RUN mkdir -p /data /output

ENTRYPOINT ["antstudio"]
CMD ["status"]
