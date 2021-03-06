# MyCryptoBot
Crypto Trading Bot working 24/7 on a Raspberry Pi 4


## Setup:
- Install a Raspberry Pi or host a server (for example AWS)
- Configure your Python environment 
- Clone the script
- Register at your crypto exchange of your choice (must serve API endpoints for placing an order) (Price data can be loaded by any other public API)
- Edit the script settings
    - Mail Notifications (Mails are sent whenever the Bot made a trade or an error occurred)
    - Log data path
    - Path of your private API key and Mail password (upload them to the desired folder on the Pi as .txt)
    - Edit the trading volume and leverage to your preferences
- Run Bot.py

## Comments:
- It is recommended to set up a crontab job for automatic restarting (every x hours) of the Bot due to network or API rate limit problems
- The Bot currently operates on the Kraken exchange
- Make sure to place limit orders to avoid high trading fees (maker vs taker fees)
- It is recommended to use linux packages such as tmux to run the Bot on additional SSH terminal windows (Allows setups and running the Bot simultaneously)
- In case you would like to connect to your Raspberry Pi outside of your local network, VPN tunnel services (like ngrok) are recommended (secure, no port forwarding needed)

## Trading Strategy:
The Bot continously (every x minutes) calculates the Relative Strength Index (RSI), which is a solid indicator for over bought / sold assets. Then, whenever a certain threshold is met, the Bot provides a buy/sell signal respectively. In case the momentum changes after a RSI triggered threshold, the Bot buys a leveraged crypto product (long/short). The Bot currently trades Bitcoin and Ethereum (5x leveraged). Leveraged products enable shorting a crypto asset. This way the Bot utilizes rising and falling prices.

The strategy serves multiple advantages when it comes to the uncertainty of future prices. It follows the principle "buy low, sell high" making use of the likelihood that the price will rise/fall again when an Asset is over bought/sold. Furthermore, the Bot is able to buy/sell at the peaks of the asset price due to the beneficial statistical properties of the RSI in combination with the momentum. Considering this, the implemented Bot yields promising results with low computational requirements.

## Limitations:
- A heavy price movement in one direction cannot be addressed by the Bot. (That is why the Bot trades only BTC and ETH since these cryptos are not objective of such price movements in the last years.)

## Open Todos:
- Implement generic API handling or
- Integrate Websockets
- Optimize buy / sell amount (at the moment: static amounts)
- Handle network problem and API rate limit exceptions in a sustainable manner
- Tryout ML/AI approaches for the prediction of the future time series
- Integrate a database storing historical data (training data for ML approach), in case the historical data is limited by public APIs


DISCLAIMER: The Bot represents a private free-time project for fun. Asset trading can be objective of financial losses and is highly speculative. This trading Bot invests real money where profit cannot be guaranteed.
