# BSCWatchBot

Simple Telegram bot to monitor BNB Smart Chain addresses. The bot is available @BSCWatchBot.

Commands:
* /start - displays a greeting
* /watch (address) - starts monitoring an address
* /forget (address) - stops monitoring an address
* /list - lists the currently monitored addresses

The bot is using the [bscscan API](https://bscscan.com/apis). In order to avoid service abuse it checks the addresses every 1 minute. It stops watching an address after 24 hours.


## To run a Markdown file using Docker, you can follow these steps:

Build the Docker image by running the following command in the terminal:

```
docker build -t bsc-watcher .
```

Once the image is built, you can run a Docker container from it using the following command:

```
docker run -d --name bsc-watcher -v $(pwd)/watch.db:/app/watch.db bsc-watcher
```



## To-do

This current version is a very barebone MVP, and there's a lot more to do:
- [x] ~~Porting it to Web3.js so the API limitations don't apply.~~ Turned out watching an address with Web3.js is a pain.
- [ ] Implementing a database, so the watchlist is not dropped every time the bot is restarted.
- [x] Implementing a /forget command.