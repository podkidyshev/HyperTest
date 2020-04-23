rm docker-compose.prod.yaml
rm docker-compose.yaml
mv docker-compose.dev.yaml docker-compose.yaml
cp docker/front/dev/Dockerfile front/