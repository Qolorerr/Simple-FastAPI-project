# Simple FastAPI project for Avito internship
This project provides an API for managing banner advertisements

## Project Overview
The Banner API allows creating, updating, and deleting banner advertisements. It was created to manage advertising campaigns on the Avito website.

## Installation
1. Install Docker on your system
2. Clone this repository: `git clone https://github.com/Qolorerr/Simple-FastAPI-project.git banner_api`
3. Build the Docker image: `docker build -t banner-api .`
4. Run the Docker container: `docker run -p 80:80 banner-api`
The API will now be available on port 80 of your Docker host.

## Configuration
The database file is defined using the DB_PATH environment variable inside the Docker container.

## Usage
You can now make requests to the API running inside the Docker container on port 80.

## API Documentation
[api.yaml](https://github.com/avito-tech/backend-trainee-assignment-2024/blob/main/api.yaml)
