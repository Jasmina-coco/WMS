FROM python:3.12-alpine
WORKDIR /app
COPY autoscaler.py .
# Docker socket'iga ulanishi uchun root kerak; konteyner faqat manager tugunda ishlaydi
CMD ["python", "-u", "autoscaler.py"]
