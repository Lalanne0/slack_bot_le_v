.PHONY: up down clean

up:
	docker compose up -d --build

down:
	docker compose down

clean:
	docker system prune -a --volumes -f
