FROM python:3.9.6
# Run commands from /eveme directory inside container
WORKDIR /eveme
# Copy requirements from local to docker image
COPY requirements.txt /eveme
# Install the dependencies in the docker image
RUN pip3 install -r requirements.txt --no-cache-dir
# Copy everything from the current dir to the image
COPY . .