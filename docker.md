## Docker cheatsheet

https://groupe-sii.github.io/cheat-sheets/docker/index.html

### Docker images

`stretch/buster/jessie`

> Images tagged with stretch, buster, or jessie are codenames for _different Debian releases_.

`-alpine`

> This image is the most highly recommended if space is a concern.

> Alpine images are based on the _Alpine Linux Project_, which is an operating system that was built specifically for use inside of containers.

> The main reason to use an Alpine image is to make your resulting image as small as possible.

`-slim`

> This image generally only installs the minimal packages needed to run your particular tool.

### Dockerfiles

> Dockerfiles are how we containerize our application, or how we build a new container from an already pre-built image and add custom logic to start our application. From a Dockerfile, we use the Docker build command to create an image.

> Think of a Dockerfile as a text document that contains the commands we call on the command line to build an image.

#### Dockerfile reference

### Docker compose

> Docker Compose is a Docker tool used to define and run multi-container applications. With Compose, you use a YAML file to configure your application’s services and create all the app’s services from that configuration.

#### Basic structure of a Docker Compose YAML file

```sh
version: '3' # version of docker compose, will provide appropriate features
services:
  web:
    # Path to dockerfile.
    # '.' represents the current directory in which
    # docker-compose.yml is present.
    build: .

    # Mapping of container port to host, (host:container)

    ports:
      - "5000:5000"
    # Mount volume
    volumes:
      - "/usercode/:/code"

    # Link database container to app container
    # for reachability.
    links:
      - "database:backenddb"

  database:

    # image to fetch from docker hub
    image: mysql/mysql-server:5.7

    # Environment variables for startup script
    # container will use these variables
    # to start the container with these define variables.
    environment:
      - "MYSQL_ROOT_PASSWORD=root"
      - "MYSQL_USER=testuser"
      - "MYSQL_PASSWORD=admin123"
      - "MYSQL_DATABASE=backend"
    # Mount init.sql file to automatically run
    # and create tables for us.
    # everything in docker-entrypoint-initdb.d folder
    # is executed as soon as container is up nd running.
    volumes:
      - "/usercode/db/init.sql:/docker-entrypoint-initdb.d/init.sql"
    depends_on:
      - redis
```

> `version '3': This denotes that we are using version 3 of Docker Compose, and Docker will provide the appropriate features. At the time of writing this article, version 3.7 is latest version of Compose.`

> `services: This section defines all the different containers we will create. In our example, we have two services, web and database.`

> `web: This is the name of our Flask app service. Docker Compose will create containers with the name we provide.`

> `build: This specifies the location of our Dockerfile, and . represents the directory where the docker-compose.yml file is located.`

> `ports: This is used to map the container’s ports to the host machine.`

> `volumes: This is just like the -v option for mounting disks in Docker. In this example, we attach our code files directory to the containers’ ./code directory. This way, we won’t have to rebuild the images if changes are made.`

> `command: command overrides the default command declared by the container image (i.e. by Dockerfile’s CMD).`

> `links: This will link one service to another. For the bridge network, we must specify which container should be accessible to which container using links.`

> `image: If we don’t have a Dockerfile and want to run a service using a pre-built image, we specify the image location using the image clause. Compose will fork a container from that image.`

> `environment: The clause allows us to set up an environment variable in the container. This is the same as the -e argument in Docker when running a container.`

> `depends_on: We kept this service dependent on redis so that untill redis won’t start, backend service will not start.`

### Build

Build an image from the Dockerfile in the current directory and tag the image

```sh
docker build -t myimage:1.0 .
```

List all images that are locally stored with the Docker Engine

```sh
docker image ls
```

Delete an image from the local image store

```sh
docker image rm alpine:3.4
```

### Share

[Deploy to another registry](https://sylhare.github.io/2019/08/05/Docker-private-registry.html)

```sh
# prepare docker image, tag the image
# docker tag [OPTIONS] IMAGE[:TAG] [REGISTRYHOST/][USERNAME/]NAME[:TAG]
docker tag python3-pytest artifactory.private.registry.ca:5000/python/python3-pytest:1
# login
docker login artifactory.private.registry.ca:5000
# upload to private registry, push using that same tag
docker push artifactory.private.registry.ca:5000/python/python3-pytest:1
```

Pull an image from a registry

```sh
docker pull myimage:1.0
```

Retag a local image with a new image name and tag

```sh
docker tag myimage:1.0 myrepo/myimage:2.0
```

Push an image to a registry

```sh
docker push myrepo/myimage:2.0
```

Run a container from the Alpine version 3.9 image, name the running container "web" and expose port 5000 externally, mapped to port 80 inside the container.

```sh
docker container run --name web -p 5000:80 alpine:3.9
```

Stop a running container through SIGTERM

```sh
docker container stop web
```

Stop a running container through SIGKILL

```sh
docker container kill web
```

List the networks

```sh
docker network ls
```

List the running containers (add --all to include stopped containers)

```sh
docker container ls
```

Delete all running and stopped containers

```sh
docker container rm -f $(docker ps -aq)
```

Print the last 100 lines of a container’s logs

```sh
docker container logs --tail 100 web
```

### Note

```sh
docker run -it --rm python:rc
```

`-it: running container interactive`

`--rm: remove container after use`

`rc: shorthand tag for release candiate and points to the latest development version`
