# MyCryptoBot
The Bot trades crypto 24/7 on a Raspberry Pi 4


Setup:
- Install a Raspberry Pi or host a server (for example AWS)
- Configure your Python environment 
- Clone the script
- Register at your crypto exchange of your choice (must serve API endpoints for placing an order) (Price data can be loaded by any API, there are alot)
- Edit the Mail Notification settings in Bot.py and transfer the API key and Mail password to the desired folder on the Pi
- Run Bot.py

Comments:
- It is recommended to set up a crontab job for automatic restarting of the Bot due to network or API rate limit problems
- The Bot currently operates on the Kraken exchange
- Make sure to place limit orders to avoid high trading fees (maker vs taker fees)
- It is recommended to use linux packages such as tmux to run the bot on additional SSH windows (Allows setups and running the Bot simultaneously)
