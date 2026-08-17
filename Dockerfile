FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.12-slim

RUN groupadd -r bastion && useradd -r -g bastion bastion

WORKDIR /app

COPY --from=builder /root/.local /home/bastion/.local
COPY . .

RUN chown -R bastion:bastion /app /home/bastion

ENV PATH=/home/bastion/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

USER bastion

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]