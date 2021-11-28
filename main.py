import telegram.ext
import requests
from bs4 import BeautifulSoup

with open('token.txt', 'r') as f:
    TOKEN = f.read()

def start(update, context):
    update.message.reply_text("Hello")

def help(update, context):
    update.message.reply_text("help message")

def doviz(update, context):
    update.message.reply_text("Alınıyor... İşbank")

    request_mig = "https://www.isbank.com.tr/doviz-kurlari"

    us = "ctl00_ctl18_g_1e38731d_affa_44fc_85c6_ae10fda79f73_ctl00_FxRatesRepeater_ctl00_fxItem"
    eur = "ctl00_ctl18_g_1e38731d_affa_44fc_85c6_ae10fda79f73_ctl00_FxRatesRepeater_ctl01_fxItem"
    gbp = "ctl00_ctl18_g_1e38731d_affa_44fc_85c6_ae10fda79f73_ctl00_FxRatesRepeater_ctl02_fxItem"

    curr_dict = {'us': us, 'eur': eur, 'gbp': gbp}
    res = requests.get(request_mig)
    res_str = ""
    for key, curr_item in curr_dict.items():
        html_content = BeautifulSoup(res.content, "html.parser")
        tr_tag = html_content.find("tr", {"id": curr_item})
        split_list = tr_tag.text.split()
        curr_alis = float(split_list[-1].replace(',', '.'))
        curr_satis = float(split_list[-2].replace(',', '.'))
        res_str = res_str + "{} diff: {:.3f}".format(" ".join(tr_tag.text.split()), curr_satis - curr_alis) + " \n "
    update.message.reply_text(res_str)


updater = telegram.ext.Updater(TOKEN, use_context=True)
disp = updater.dispatcher

disp.add_handler(telegram.ext.CommandHandler("start", start))
disp.add_handler(telegram.ext.CommandHandler("help", help))
disp.add_handler(telegram.ext.CommandHandler("doviz", doviz))
print("BOT started")
updater.start_polling()
updater.idle()
