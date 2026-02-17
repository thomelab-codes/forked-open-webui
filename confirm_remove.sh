#!/bin/bash
echo "Warning: This will remove all containers and volumes, including persistent data. Do you want to continue? [Y/N]"
read ans
if [ "$ans" == "Y" ] || [ "$ans" == "y" ]; then
  if docker compose version &>/dev/null; then
    docker compose down -v
  else
    docker-compose down -v
  fi
else
  echo "Operation cancelled."
fi
