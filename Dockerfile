# Builds the OMSCS course study app
# In addition to files on github, manually setting up .env required
FROM ubuntu:latest
WORKDIR /root/course_study
COPY ["coursexp.py", "etracker.py", "regpage.py", "requirements.txt", ".env", "./"]
RUN apt-get update && apt-get install -y \
    wget \
    firefox \
    python3.6 \
    python3-pip
RUN echo 'alias python=python3.6' >> ~/.bashrc
RUN echo 'alias pip=pip3' >> ~/.bashrc

# Latest geckodriver when dockerfile created
RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.21.0/geckodriver-v0.21.0-linux64.tar.gz \
    && tar -xzf geckodriver* \
    && mv geckodriver /usr/local/bin/
RUN pip3 install -r requirements.txt
