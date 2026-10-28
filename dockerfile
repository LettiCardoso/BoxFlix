# Imagem base leve com Python
FROM python:3.12-slim

# Diretório de trabalho dentro do container
WORKDIR /app

# Copia só o requirements.txt primeiro (aproveita cache do Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código do projeto
COPY . .

# Porta que o Flask usa
EXPOSE 5000

# Comando que roda quando o container inicia
CMD ["python", "app.py"]
