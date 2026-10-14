# Python fixado na imagem, e não no menu do buildpack: o builder do Cloud Run só
# oferece 3.13 e 3.14, e o psycopg2-binary nem sempre tem pacote pronto para a
# versão mais nova — foi assim que o build do vzp-produtividade falhou três vezes
# antes de virar Dockerfile.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependências antes do código: mexer no código não reinstala tudo de novo.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# O mesmo comando do Procfile, que o Render usa. --preload carrega o app antes
# de abrir as conexões, então erro de import aparece no arranque e não na
# primeira visita.
ENV PORT=8080
# --timeout 0: o Cloud Run já corta requisições pelo próprio limite; threads
# aproveitam a CPU da instância sem multiplicar conexões ao banco.
CMD ["sh", "-c", "exec gunicorn --preload app:app --bind 0.0.0.0:${PORT:-8080} --workers 1 --threads 8 --timeout 0"]
