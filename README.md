# thrift-yield-api

Thrift Yield API project.

## Create Project

Mapped through docker-compose _volumes_ **./app:/app**

`docker-compose run --rm app sh -c "django-admin startproject app ."`

## Run linting

`docker-compose run --rm app sh -c "flake8"`

## Run test

`docker-compose run --rm app sh -c "python manage.py test"`

## Start the service

`docker-compose up`
