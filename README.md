Installation and running steps:

Step 1 - Download and install dependencies:
- Python 3.7.4 64-bit
- Docker
- Docker Compose

Step 2 - Install virtualenv:
- `pip3 install virtualenv`

Step 3 - Create a virtual environment using virtualenv:
- `virtualenv -p python3 env`

Step 4 - Activate the virtual environment:
- `source env/bin/activate`

Step 5 - Install dependencies into the current active virtual environment:
- `pip install -r requirements.txt`

Step 6 - Start the docker containers (Optional, if you use docker):
- `docker-compose up -d`

Step 7 - Create language2test database in postgres (Optional, if you use docker):
- `docker exec -it --user postgres `docker ps | grep postgres | cut -f 1 -d\ | head -n 1` bash`
- `createdb language2test`

Step 8 - Create the database schema:
- `python make_db.py`

Step 9 - Launch the server:
- `python app.py`
