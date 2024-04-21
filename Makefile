.PHONY: server consumer faust kafka

# Start Django server
server:
	python manage.py runserver

# Run Django Kafka consumer
consumer:
	python manage.py runconsumer

# Run Faust app
faust:
	faust -A stream_processors.popular_product worker --loglevel=info

# Start Kafka using Docker Compose
services:
	docker-compose up

# Stop and remove all Docker containers and networks
services-down:
	docker-compose down
