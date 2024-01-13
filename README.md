# thrift-yield-api

Thrift Yield API project.

## Create Project

Mapped through docker-compose _volumes_ **./app:/app**

`docker-compose run --rm app sh -c "django-admin startproject app ."`

### Create a new app

`docker-compose run --rm app sh -c "python manage.py startapp core"`

## Run linting

`docker-compose run --rm app sh -c "flake8"`

## Run test

`docker-compose run --rm app sh -c "python manage.py test"`

## Run custom commands

`docker-compose run --rm app sh -c "python manage.py wait_for_db"`

## Start the service

`docker-compose down`
`docker-compose build`
`docker-compose up`
