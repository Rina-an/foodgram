# Сборка выполняется из корня репозитория:
# docker build -f infra/Dockerfile -t foodgram_gateway .
FROM nginx:1.25.4-alpine

COPY infra/nginx.conf /etc/nginx/conf.d/default.conf
COPY docs/ /usr/share/nginx/html/api/docs/
