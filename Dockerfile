FROM python:3.7
RUN apt-get update
RUN apt-get install -y unzip xvfb libxi6 libgconf-2-4
RUN apt-get install -y default-jdk
RUN curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add
RUN echo "deb [arch=amd64]  http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list
RUN apt-get -y update
RUN apt-get -y install google-chrome-stable
RUN wget https://chromedriver.storage.googleapis.com/2.41/chromedriver_linux64.zip
RUN unzip chromedriver_linux64.zip
RUN mv chromedriver /usr/bin/chromedriver
RUN chown root:root /usr/bin/chromedriver
RUN chmod +x /usr/bin/chromedriver
RUN wget https://selenium-release.storage.googleapis.com/3.13/selenium-server-standalone-3.13.0.jar

RUN mkdir /LawinsiderScraper
WORKDIR LawinsiderScraper
RUN mkdir ./output
COPY clauseScraper.py ./
COPY requirements.txt ./requirements.txt
RUN pip install -r ./requirements.txt

CMD [ "python", "./clauseScraper.py" ]