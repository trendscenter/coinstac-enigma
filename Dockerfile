FROM coinstac/coinstac-base-python-stream

# Set the working directory
WORKDIR /computation

# Copy requirements.txt into the container
COPY requirements.txt /computation

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Copy the current directory contents into the container
COPY . /computation