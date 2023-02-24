## notes
superuser: root/adminadmin

## Quick start
```sh
# build dockerfile
docker compose build --build-arg HTTP_PROXY=http://host.docker.internal:3128 --build-arg HTTPS_PROXY=http://host.docker.internal:3128 --build-arg http_proxy=http://host.docker.internal:3128 --build-arg https_proxy=http://host.docker.internal:3128

# change external ip in .env file to enable kafka listen outside host
docker compose --env-file ./docker.env up -d
```