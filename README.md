# MyCryptoBot
Crypto Trading Bot working 24/7 on a Raspberry Pi 4


## Setup:
- Install a Raspberry Pi or host a server (for example AWS)
- Configure your Python environment 
- Clone the script
- Register at your crypto exchange of your choice (must serve API endpoints for placing an order) (Price data can be loaded by any API, there are alot)
- Edit the Mail Notification settings in Bot.py and transfer the API key and Mail password to the desired folder on the Pi
- Run Bot.py

## Comments:
- It is recommended to set up a crontab job for automatic restarting (every x hours) of the Bot due to network or API rate limit problems
- The Bot currently operates on the Kraken exchange
- Make sure to place limit orders to avoid high trading fees (maker vs taker fees)
- It is recommended to use linux packages such as tmux to run the bot on additional SSH windows (Allows setups and running the Bot simultaneously)
- In case you would like to connect to your Raspberry Pi outside of your local network, VPN tunnel services (like ngrok) are recommended (secure, no port forwarding needed)

## Trading Strategy:
The Bot continously (every x minutes) calculates the Relative Strength Index (RSI), which is a solid indicator for over bought and sold assets. Then, whenever a certain threshold is met, the Bot provides a buy/sell signal respectively. In case the momentum changes after a RSI triggered threshold, the Bot buys a leveraged crypto product (long/short). The Bot currently trades Bitcoin and Ethereum (5x leveraged). 

The strategy serves multiple advantages when it comes to the uncertainty of future prices. It follows the principle "buy low, sell high" making use of the likelihood that the price will rise/fall again when an Asset is over bought/sold. Furthermore, the Bot is able to buy/sell at the peaks of the asset price due to the beneficial statistical properties of the RSI in combination of the momentum. Considering this, the implemented Bot performs better than simple grid trading strategys for example.

## Limitations:
- A heavy price movement in one direction for a long time period cannot be addressed by the Bot. (That is why the Bot trades only BTC and ETH since these cryptos are likely not objective of such price movements.)

## Open Todos:
- The implemented API calls are only working for the Kraken exchange with regards to the used KrakenAPI Python Package -> Implement generic API handling
- Optimize buy / sell amount (at the moment: static amounts)
- Handle network problem and API rate limit exceptions in a sustainable manner
- Tryout ML/AI approaches for the price prediction
- Integrate a database storing historical data (training data for ML approach)
