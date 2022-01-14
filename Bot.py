import krakenex
from pykrakenapi import KrakenAPI
from pykrakenapi.pykrakenapi import KrakenAPIError
from datetime import datetime, timedelta
import time
import threading
import pandas_ta as ta
import logging
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import csv


timezone = 1


class Bot(threading.Thread):

    def __init__(self, pair, *args, **kwargs):
        # Thread
        super(Bot, self).__init__(*args, **kwargs)
        self.__flag = threading.Event()
        self.__flag.set()  # Set to True
        self.__running = threading.Event()  # Busy Ste
        self.__running.set()  # Set running to True

        # Bot Information
        self.pair = pair
        self.token_information = get_token_information(self.pair)
        self.macd_data = None
        self.rsi_data = None
        self.rsi_15_data = None
        self.market_data = None

        self.volume = str(self.token_information["minimal_volume"])
        self.leverage = self.token_information["leverage"]

    def __calculate_rsi__(self):
        self.rsi_data = self.market_data.ta.rsi(close='close', length=14, append=False)

    def __calculate_rsi_15__(self):
        time.sleep(1)
        new_data, last_date_new = k.get_ohlc_data(self.pair, interval=15, since=0)
        new_data = new_data.iloc[::-1]
        new_data = new_data[["time", "close"]]
        self.rsi_15_data = new_data.ta.rsi(close='close', length=14, append=False)

    def __calculate_macd__(self):
        time.sleep(1)
        new_data, last_date_new = k.get_ohlc_data(self.pair, interval=1, since=0)
        new_data = new_data.iloc[::-1]
        self.macd_data = new_data.ta.macd(close='close', fast=12, slow=26, signal=9, append=False)

    def run(self):
        log("%s - Start Loop" % self.pair, "info")

        is_rsi_triggered = False
        is_rsi_bullish = False
        while self.__running.isSet():
            self.__flag.wait()

            if not is_rsi_triggered:
                time.sleep(1)
                new_data, last_date_new = k.get_ohlc_data(self.pair, interval=5, since=0)
                new_data = new_data.iloc[::-1]
                self.market_data = new_data[["time", "close"]]
                self.__calculate_rsi__()
                log("%s - RSI: %f at %s" % (
                    self.pair, self.rsi_data[-1], str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))))

                # Sell
                if self.rsi_data[-1] > 70:
                    self.__calculate_rsi_15__()
                    if self.rsi_15_data[-1] > 70:
                        self.volume = str(round(float(self.token_information["minimal_volume"]) * 6, 6))
                    else:
                        self.volume = str(self.token_information["minimal_volume"])
                    is_rsi_triggered = True
                    is_rsi_bullish = False


                # Buy
                elif self.rsi_data[-1] < 30:
                    self.__calculate_rsi_15__()
                    if self.rsi_15_data[-1] < 30:
                        self.volume = str(round(float(self.token_information["minimal_volume"]) * 6, 6))
                    else:
                        self.volume = str(self.token_information["minimal_volume"])
                    is_rsi_triggered = True
                    is_rsi_bullish = True

                if not is_rsi_triggered:
                    time.sleep(60*3)

            else:
                self.__calculate_macd__()
                second_last_value = self.macd_data["MACDh_12_26_9"].iloc[-2]
                last_value = self.macd_data["MACDh_12_26_9"].iloc[-1]
                # Buy
                if is_rsi_bullish:
                    if second_last_value < float(0.10):
                        if last_value < second_last_value:
                            is_rsi_triggered = False
                            is_rsi_bullish = False
                            try:
                                manage_order(self, 4, "buy")
                            except KrakenAPIError:
                                time.sleep(60 * 4)
                    else:
                        is_rsi_triggered = False
                # Sell
                else:
                    if second_last_value > float(0.10):
                        if last_value < second_last_value:
                            is_rsi_triggered = False
                            is_rsi_bullish = False
                            try:
                                manage_order(self, 4, "sell")
                            except KrakenAPIError:
                                time.sleep(60 * 4)
                    else:
                        is_rsi_triggered = False

                if not is_rsi_triggered:
                    time.sleep(60)
                else:
                    time.sleep(60*2)

    def pause(self):
        self.__flag.clear()  # Set to False to block the thread

    def resume(self):
        self.__flag.set()  # Set to True, let the thread stop blocking

    def stop(self):
        self.__flag.set()  # Resume the thread from the suspended state, if it is already suspended
        self.__running.clear()


def process_trade_signal(pair, volume, leverage, type_of_order, limit=True):
    expire_time = 15

    # Open an order
    try:
        if type_of_order == "sell":
            if limit:
                open_sell_order(pair, volume, leverage, expire_time)
            else:
                open_sell_order(pair, volume, leverage, expire_time, limit=False)
        else:
            if limit:
                open_buy_order(pair, volume, leverage, expire_time)
            else:
                open_buy_order(pair, volume, leverage, expire_time, limit=False)
    except KrakenAPIError as err:
        raise err

    time.sleep(expire_time + 1)


def manage_order(bot, tryouts, type_of_order):
    while_counter = 0
    order_is_expired = True
    error_occurred = False
    while while_counter < tryouts:

        if not order_is_expired or error_occurred:
            break

        log("%s - Order Loop %i" % (bot.pair, while_counter + 1))

        if while_counter == 0:
            try:
                process_trade_signal(bot.pair, bot.volume, bot.leverage, type_of_order)
            except KrakenAPIError as err:
                log("%s - Order Placement failed - Error: %s" % (bot.pair, err.args[0][0]))
                error_occurred = True
                send_email("Error Occured during %s %s" % (type_of_order.capitalize(), bot.pair),
                          "The Error %s orcurred." % err.args[0][0])
                raise err
                break
        else:
            closed_orders = k.get_closed_orders()
            closed_orders = closed_orders[0]
            for_counter = 0
            for i in closed_orders["descr_pair"]:
                if i == bot.pair:
                    if closed_orders["status"][for_counter] != "closed":
                        try:
                            helper = closed_orders["opentm"][for_counter].item()
                            helper = k.unixtime_to_datetime(helper) + timedelta(hours=timezone)
                            log("%s - Last Order for %s was %s with opentime %s" % (bot.pair, closed_orders["descr_price"][for_counter],
                                                                                    closed_orders["status"][for_counter], helper))
                            process_trade_signal(bot.pair, bot.volume, bot.leverage, type_of_order)
                            break
                        except KrakenAPIError as err:
                            log("%s - Order Placement failed - Error: %s" % (bot.pair, err.args[0][0]))
                            error_occurred = True
                            raise err
                            break

                    else:
                        log("%s - Order successfully filled within the last order" % bot.pair)
                        send_email("%s %s" % (type_of_order.capitalize(), bot.pair),
                                   "%s %s of %s at the price of %s" %
                                   (type_of_order.capitalize(), bot.volume, bot.pair, closed_orders["descr_price"][for_counter]))
                        order_is_expired = False
                        break
                for_counter += 1
        while_counter += 1

    if order_is_expired:
        helper = closed_orders["opentm"][for_counter].item()
        helper = k.unixtime_to_datetime(helper) + timedelta(hours=timezone)
        log("%s - Last Order for %s was %s with opentime %s" % (bot.pair, closed_orders["descr_price"][for_counter],
                                                                closed_orders["status"][for_counter], helper))
        log("%s - Orders were not filled. Terminate Loop" % bot.pair)
        time.sleep(60 * 2)
    else:
        time.sleep(60 * 3)


def open_sell_order(pair, volume, leverage, expire_time, limit=True):
    try:
        if limit:
            k.add_standard_order(pair=pair, type="sell", ordertype="limit", oflags="post",
                                 price="+0.0004%", expiretm="+%i" % expire_time, volume=volume, leverage=leverage, validate=False)
            log("%s - Limit Margin Sell Order for %s at opentime %s" % (
                pair, volume, str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))))
        else:
            k.add_standard_order(pair=pair, type="sell", ordertype="market", volume=volume, leverage=leverage, validate=False)
            log("%s - Market Sell Order at opentime %s" % (
                pair, str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))))

    except KrakenAPIError as err:
        raise err


def open_buy_order(pair, volume, leverage, expire_time, limit=True):
    try:
        if limit:
            k.add_standard_order(pair=pair, type="buy", ordertype="limit", oflags="post",
                                 price="-0.0004%", expiretm="+%i" % expire_time, volume=volume, leverage=leverage, validate=False)
            log("%s - Limit Margin Buy Order for %s at opentime %s" % (
                pair, volume, str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))))
        else:
            k.add_standard_order(pair=pair, type="buy", ordertype="market", volume=volume, leverage=leverage, validate=False)
            log("%s - Market Margin Buy Order at the opentime %s" % (
                pair, str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))))
    except KrakenAPIError as err:
        raise err


def get_token_information(pair):
    ret = None
    if pair == "XBTEUR":
        ret = {
            "minimal_volume": "0.0004",
            "price_precision": "1",
            "account_balance_name": "XXBT",
            "leverage": 5
        }

    if pair == "ETHEUR":
        ret = {
            "minimal_volume": "0.004",
            "price_precision": "2",
            "account_balance_name": "XETH",
            "leverage": 5
        }

    if pair == "ADAEUR":
        ret = {
            "minimal_volume": "5",
            "price_precision": "6",
            "account_balance_name": "ADA",
            "leverage": 1
        }

    if pair == "SOLEUR":
        ret = {
            "minimal_volume": "0.02",
            "price_precision": "2",
            "account_balance_name": "SOL",
            "leverage": 1
        }

    return ret


def log(log_string, log_type=None):
    print(log_string)
    if log_type is None:
        logging.info(log_string)
    else:
        if log_type == "debug":
            logging.debug(log_string)
        elif log_type == "info":
            logging.info(log_string)
        elif log_type == "warning":
            logging.warning(log_string)
        elif log_type == "error":
            logging.error(log_string)


def send_email(subject, text):
    send_mail = "Nils.Rethschulte@gmx.de"
    receive_mail = "Nils.Rethschulte@gmx.de"
    msg = MIMEMultipart()
    msg['From'] = send_mail
    msg['To'] = receive_mail
    msg['Subject'] = subject

    msg.attach(MIMEText(text, 'html'))

    server = smtplib.SMTP('mail.gmx.net', 587)
    server.starttls()
    server.login(send_mail, read_file("passwort.txt"))
    text = msg.as_string()
    server.sendmail(send_mail, receive_mail, text)
    server.quit()


def read_file(filename):
    filehandler = open(filename)
    for i in filehandler:
        ret = i
    filehandler.close()
    return ret


api = krakenex.API()
# api.load_key("C:\\Users\\NilsRethschulte\\PycharmProjects\\bot\\Kraken Bot\\kraken.txt")
api.load_key("/home/pi/python/kraken.txt")
k = KrakenAPI(api, crl_sleep=1, retry=2)

version = "V1.6"
log_filename = str(datetime.now().strftime('%Y-%m-%d %H:%M')) + " " + version

logging.basicConfig(filemode="w", filename='/home/pi/python/Logs/%s.log' % log_filename,
                    format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)
# logging.basicConfig(filename='%s.log' % log_filename, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.DEBUG)

myBot1 = Bot("XBTEUR")
try:
    myBot1.start()
except Exception as err:
    log(err)

time.sleep(20)

myBot2 = Bot("ETHEUR")
try:
    myBot2.start()
except Exception as err:
    log(err)
