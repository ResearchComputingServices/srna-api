Installation and running steps:

Step 1 - Download and install dependencies:

Python 3.7.4 64-bit
Docker
Docker Compose
Step 2 - Install virtualenv:

pip3 install virtualenv
Step 3 - Create a virtual environment using virtualenv:

virtualenv -p python3 env
Step 4 - Activate the virtual environment:

source env/bin/activate
Step 5 - Install dependencies into the current active virtual environment:

pip install -r requirements.txt
Step 6 - Launch the server:

python app.py