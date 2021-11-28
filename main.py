import telegram.ext
import requests
from bs4 import BeautifulSoup
import json
from jsonpath_ng import jsonpath, parse
from pymongo import MongoClient
import datetime


with open('token.txt', 'r') as f:
    TOKEN = f.read()
with open('mongo.txt', 'r') as f:
    MONGO = f.read()

def start(update, context):
    update.message.reply_text("Hello")

def help(update, context):
    update.message.reply_text("help message")

def discount(update, context):
    try:
        update.message.reply_text("Getiriliyor")
        client = MongoClient('mongodb+srv://hkayakoku:{}@cluster0.rn62h.mongodb.net/test'.format(MONGO))
        db = client['migros-product']
        col = db['migros']

        dt = datetime.datetime.now()
        today_str = "{}-{}-{}".format(dt.year, dt.month, dt.day)

        dt = datetime.datetime.now() - datetime.timedelta(days=1)
        yesterday_str = "{}-{}-{}".format(dt.year, dt.month, dt.day)

        # Some working Commands
        # { $expr: { $gt : [ "$PriceDict.2021-11-22.sale_price" , "$PriceDict.2021-11-23.sale_price" ] } }
        product = col.find({"$expr": {
            "$gt": ["$PriceDict.{}.sale_price".format(yesterday_str), "$PriceDict.{}.sale_price".format(today_str)]}})

        dis_str = ""
        for x in product:
            if yesterday_str in x['PriceDict'] and today_str in x['PriceDict']:
                yesterday_price = x['PriceDict'][yesterday_str]['sale_price']
                today_price = x['PriceDict'][today_str]['sale_price']
                diff = today_price - yesterday_price
                dis_str = dis_str + "\n" + ("{} - www.migros.com.tr/{} t-1 {} t {} diff: {:.2f}".format(x['category'],
                                                                                  x['_id'], yesterday_price,
                                                                                  today_price,
                                                                                  today_price - yesterday_price))

        dis_str = dis_str + "\n" + "Yukselenler"

        product = col.find({"$expr": {
            "$gt": ["$PriceDict.{}.sale_price".format(today_str), "$PriceDict.{}.sale_price".format(yesterday_str)]}})

        for x in product:
            if yesterday_str in x['PriceDict'] and today_str in x['PriceDict']:
                yesterday_price = x['PriceDict'][yesterday_str]['sale_price']
                today_price = x['PriceDict'][today_str]['sale_price']
                dis_str = dis_str + "\n" + ("{} - www.migros.com.tr/{} t-1 {} t {} diff: {:.2f}".format(x['category'],
                                                                                  x['_id'], yesterday_price,
                                                                                  today_price,
                                                                                  today_price - yesterday_price))

        update.message.reply_text(dis_str)
    except Exception as e:
        msg = update.message.reply_text("HATA: {}".format(str(e)))


def migros(update, context):
    # Any send_* methods return the sent message object
    msg = update.message.reply_text("Başlatılıyor...")

    class Product:
        def __init__(self):
            self._id = None
            self.category = None
            self.name = None
            self.PriceDict = {}


    class Price:
        def __init__(self):
            self.sale_price = None
            self.regular_price = None
            self.discount_rate = None

    try:
        category_list = ["meyve-sebze-c-2",
                         "et-tavuk-balik-c-3",
                         "sut-kahvaltilik-c-4",
                         "temel-gida-c-5",
                         "meze-hazir-yemek-donuk-c-7d",
                         "firin-pastane-c-7e",
                         "dondurma-c-41b",
                         "atistirmalik-c-113fb",
                         "icecek-c-6",
                         "deterjan-temizlik-c-7",
                         "kisisel-bakim-kozmetik-c-8",
                         "anne-bebek-c-9",
                         "ev-yasam-c-a",
                         "kitap-kirtasiye-oyuncak-c-118ec",
                         "cicek-c-502",
                         "pet-shop-c-a0",
                         "elektronik-c-a6"]

        product_info_list = []
        client = MongoClient('mongodb+srv://hkayakoku:{}@cluster0.rn62h.mongodb.net/test'.format(MONGO))
        db = client['migros-product']
        col = db['migros']

        # today
        dt = datetime.datetime.now()
        today_str = "{}-{}-{}".format(dt.year, dt.month, dt.day)
        id_set = set()
        for category in category_list:
            page_list = []
            request_mig = "https://www.migros.com.tr/rest/search/screens/{}".format(category)
            res = requests.get(request_mig)
            market_json = json.loads(res.content)
            # TODO solve double request problem

            page_count = market_json["data"]["searchInfo"]["pageCount"]
            # page_count = 1;

            for i in range(1, page_count + 1, 1):
                page_list.append("{}?sayfa={}".format(request_mig, i))

            for res_url in page_list:
                msg.edit_text("Requesting... {}".format(res_url))
                # print("Requesting... {}".format(res_url))
                res = requests.get(res_url)
                market_json = json.loads(res.content)
                jsonpath_expression = parse('data[*].searchInfo[*].storeProductInfos[*]')
                for match in jsonpath_expression.find(market_json):
                    p_dict = match.value
                    if p_dict["saleable"] is not True or p_dict['status'] != 'IN_SALE':
                        # delist
                        # check existance of db
                        delete_result = col.delete_one({"_id": p_dict["prettyName"]})
                        msg.edit_text("Deleted: {}".format({p_dict["prettyName"]}))
                    else:
                        if p_dict["prettyName"] not in id_set:
                            id_set.add(p_dict["prettyName"])
                            p = Product()
                            p._id = p_dict["prettyName"]
                            p.name = p_dict["name"]
                            p.category = category

                            price = Price()
                            price.sale_price = p_dict["shownPrice"] / 100
                            price.regular_price = p_dict["regularPrice"] / 100
                            price.discount_rate = p_dict["discountRate"]

                            update_need = False
                            # check existance of db
                            ret = col.find_one({"_id": p_dict["prettyName"]})
                            if ret is not None and 'PriceDict' in ret:
                                if today_str in ret['PriceDict']:
                                    if ret['PriceDict'][today_str]['sale_price'] != price.sale_price:
                                        update.message.reply_text("Today's Price Changed in {} from {} to {}".format
                                                                  (p_dict["prettyName"],
                                                                                                 price.sale_price,
                                                                                                 ret['PriceDict'][today_str][
                                                                                                     'sale_price']))
                                ret['PriceDict'][today_str] = price.__dict__
                                update_need = True

                                if ret['category'] != category:
                                    ret['category'] = category
                                    update_need = True

                                if update_need:
                                    update_result = col.update_one({'_id': p_dict["prettyName"]}, {'$set': ret})

                            else:
                                p.PriceDict[today_str] = price.__dict__
                                msg.edit_text("Added new item: {}".format(p_dict["prettyName"]))
                                product_info_list.append(p.__dict__)

        x = col.insert_many(product_info_list)
        msg = update.message.reply_text("Completed")
    except Exception as e:
        msg = update.message.reply_text("HATA: {}".format(str(e)))

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
disp.add_handler(telegram.ext.CommandHandler("migros", migros))
disp.add_handler(telegram.ext.CommandHandler("discount", discount))
# print("BOT started")
updater.start_polling()
updater.idle()
