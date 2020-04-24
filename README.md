1. Create input.csv with clauses list in iofiles directory
2. Docker build:
docker build -t selenium .
3. Docker run:
docker run --rm --name seleniumscraper -v /home/mikhail/Parley/iofiles:/LawinsiderScraper/iofiles/ --env LAWINSIDER_LOGIN=login --env LAWINSIDER_PASSWORD=password selenium
