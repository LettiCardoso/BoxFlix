FROM python:3.12-slim

WORKDIR /app

# Copia e instala as dependências primeiro (cache mais eficiente)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o resto do código (app.py, templates/, static/, boxflix.db, etc.)
COPY . .

# Flask geralmente roda na porta 5000
EXPOSE 5000

# Ajustado para app.py, que é o seu arquivo de entrada
CMD ["python", "app.py"]