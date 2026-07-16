FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 openjdk-17-jre-headless \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt constraints.txt ./
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt -c constraints.txt

COPY . .
RUN python -m pip install -e ".[dev]" -c constraints.txt

CMD ["python", "scripts/validate_skill_package.py", "--skill-root", "."]
