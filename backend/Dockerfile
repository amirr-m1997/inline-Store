FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements/base.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
# Headless Chromium for official A4 invoice PDFs.
RUN apt-get update && apt-get install -y --no-install-recommends chromium fontconfig \
 && rm -rf /var/lib/apt/lists/*
COPY . .
# Bundled Vazirmatn subsets so invoice PDFs render Persian deterministically.
RUN mkdir -p /usr/share/fonts/vazirmatn \
 && cp /app/apps/orders/fonts/*.woff2 /usr/share/fonts/vazirmatn/ \
 && fc-cache -f
EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py runserver 0.0.0.0:8000"]
