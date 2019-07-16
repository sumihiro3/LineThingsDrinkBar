# -*- coding: utf-8 -*-
import os
import uuid
import logging
from datetime import datetime as dt
from flask import (
    render_template, jsonify, request, abort, redirect
)

# LINE
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError,
)
from linebot.models import (
    FollowEvent,
)

from . import app, db
from .models import (
    User, UserRole, PurchaseOrder, PurchaseOrderDetail, Item,
    PurchaseOrderStatus
)
from .line_pay import LinePay
from . import json_util

LINE_PAY_URL = os.getenv('LINE_PAY_URL', None)
LINE_PAY_CHANNEL_ID = os.getenv('LINE_PAY_CHANNEL_ID', None)
LINE_PAY_CHANNEL_SECRET = os.getenv('LINE_PAY_CHANNEL_SECRET', None)
LINE_PAY_CONFIRM_URL = os.getenv('LINE_PAY_CONFIRM_URL', None)
PROXY_URL = os.getenv('QUOTAGUARDSTATIC_URL', None)

pay = LinePay(
    channel_id=LINE_PAY_CHANNEL_ID,
    channel_secret=LINE_PAY_CHANNEL_SECRET,
    line_pay_url=LINE_PAY_URL,
    confirm_url=LINE_PAY_CONFIRM_URL,
    proxy_url=PROXY_URL
)

# Logger
app.logger.setLevel(logging.DEBUG)


@app.route('/')
def index():
    app.logger.info('handler index called!')
    app.logger.debug('LINEBOT_CHANNEL_ACCESS_TOKEN[%s]', os.getenv('LINEBOT_CHANNEL_ACCESS_TOKEN'))
    app.logger.debug('LINEBOT_CHANNEL_SECRET[%s]', os.getenv('LINEBOT_CHANNEL_SECRET'))
    items = Item.query.all()
    return render_template(
        'index.html',
        title='Hello world',
        items=items
    )


@app.route('/drink_bar', methods=['GET'])
def get_drink_bar():
    app.logger.info('handler get_drink_bar called!')
    return render_template(
        'drink_bar.html',
        # message=None,
        # transaction_id=None
    )


@app.route('/pay_by_line_pay', methods=['GET'])
def get_pay_by_line_pay():
    app.logger.info('handler get_pay_by_line_pay called!')
    return render_template(
        'pay_by_line_pay.html',
    )

#
@app.route('/api/items', methods=['GET'])
def get_items():
    app.logger.info('handler get_items called!')
    item_list = Item.query.filter(Item.active == True).all()
    app.logger.debug(item_list)
    items = []
    for i in item_list:
        item = {
            'id': i.id,
            'name': i.name,
            'description': i.description,
            'unit_price': i.unit_price,
            'stock': i.stock,
            'image_url': i.image_url
        }
        app.logger.debug(item)
        items.append(item)
    # return items
    app.logger.debug(items)
    return jsonify({
        'items': items
    })


@app.route('/api/purchase_order', methods=['POST'])
def post_purchase_order():
    app.logger.info('handler post_purchase_order called!')
    app.logger.debug('Request json: %s', request.json)
    request_dict = request.json
    user_id = request_dict.get('user_id', None)
    user = User.query.filter(User.id == user_id).first()
    order_items = request_dict.get('order_items', [])
    order_item_list = Item.query.filter(Item.id.in_(order_items))
    app.logger.debug('order_item_list: %s', order_item_list)
    # order !
    order = add_purchase_order(user, order_item_list)
    ordered_item = Item.query.filter(Item.id == order.details[0].item_id).first()
    # return
    return jsonify({
        'order_id': order.id,
        'order_title': order.title,
        'order_amount': order.amount,
        'order_item_slot': ordered_item.slot,
        'ordered_item_image_url': ordered_item.image_url
    })


@app.route('/api/order/<user_id>/<order_id>', methods=['GET'])
def get_order_info(user_id, order_id):
    app.logger.info('handler get_order_info called!')
    app.logger.debug('user_id: %s', user_id)
    app.logger.debug('order_id: %s', order_id)
    # query order
    order = PurchaseOrder.query.filter(PurchaseOrder.id == order_id).first()
    # return
    return jsonify({
        'order': {
            'id': order.id,
            'title': order.title,
            'amount': order.amount
        }
    })


@app.route('/api/transaction_order/<user_id>/<transaction_id>', methods=['GET'])
def get_order_info_by_transaction(user_id, transaction_id):
    app.logger.info('handler get_order_info_by_transaction called!')
    app.logger.debug('user_id: %s', user_id)
    app.logger.debug('transaction_id: %s', transaction_id)
    # query order
    order = PurchaseOrder.query.filter(PurchaseOrder.transaction_id == transaction_id).first()
    ordered_item = Item.query.filter(Item.id == order.details[0].item_id).first()
    # return
    return jsonify({
        'order': {
            'id': order.id,
            'title': order.title,
            'amount': order.amount,
            'item_slot': ordered_item.slot,
            'item_image_url': ordered_item.image_url
        }
    })


def add_purchase_order(user, order_items):
    """
    注文情報を生成する
    :param user:
    :type user: User
    :param order_items:
    :type order_items: list
    :return: purchase order
    :rtype: PurchaseOrder
    """
    app.logger.info('add_purchase_order called!')
    order_id = uuid.uuid4().hex
    timestamp = int(dt.now().timestamp())
    details = []
    amount = 0
    for item in order_items:
        detail = PurchaseOrderDetail()
        detail.id = order_id + '-' + item.id
        detail.unit_price = item.unit_price
        detail.quantity = 1
        detail.amount = item.unit_price * detail.quantity
        detail.item = item
        detail.created_timestamp = timestamp
        db.session.add(detail)
        details.append(detail)
        amount = amount + detail.amount
    # generate PurchaseOrder
    order_title = details[0].item.name
    if len(details) > 1:
        order_title = '{} 他'.format(order_title)
    order = PurchaseOrder(order_id, order_title, amount)
    order.user_id = user.id
    order.details.extend(details)
    db.session.add(order)
    db.session.commit()
    return order


"""
===================================
LINE Pay メソッド
===================================
"""


@app.route("/pay/reserve", methods=['POST'])
def handle_pay_reserve():
    app.logger.info('handler handle_pay_reserve called!')
    # app.logger.debug('Request from data: %s', request.form)
    # order_id = request.form.get('order_id', None)
    # user_id = request.form.get('user_id', None)
    app.logger.debug('Request json: %s', request.json)
    request_dict = request.json
    user_id = request_dict.get('user_id', None)
    order_id = request_dict.get('order_id', None)
    # get PurchaseOrder and User
    order = PurchaseOrder.query.filter(PurchaseOrder.id == order_id).first()
    app.logger.debug('PurchaseOrder: %s', order)
    user = User.query.filter(User.id == user_id).first()
    app.logger.debug('User: %s', user)
    ordered_item = Item.query.filter(Item.id == order.details[0].item_id).first()
    app.logger.debug('Ordered Item: %s', ordered_item)

    response = pay.reserve_payment(order, product_image_url=ordered_item.image_url)
    app.logger.debug('Response: %s', json_util.dump_json_with_pretty_format(response))
    app.logger.debug('returnCode: %s', response["returnCode"])
    app.logger.debug('returnMessage: %s', response["returnMessage"])

    transaction_id = response["info"]["transactionId"]
    app.logger.debug('transaction_id: %s', transaction_id)
    # set TransactionId and User to PurchaseOrder
    order.user_id = user.id
    order.transaction_id = transaction_id
    db.session.commit()
    db.session.close()
    payment_url = response["info"]["paymentUrl"]["web"]
    # return
    return jsonify({
        'payment_url': payment_url
    })
    # return redirect(payment_url)


@app.route("/pay/confirm", methods=['GET'])
def handle_pay_confirm():
    app.logger.info('handler handle_pay_confirm called!')
    transaction_id = request.args.get('transactionId')
    order = PurchaseOrder.query.filter_by(transaction_id=transaction_id).one_or_none()
    if order is None:
        raise Exception("Error: transaction_id not found.")
    # run confirm API
    response = pay.confirm_payments(order)
    app.logger.debug('returnCode: %s', response["returnCode"])
    app.logger.debug('returnMessage: %s', response["returnMessage"])

    order.status = PurchaseOrderStatus.PAYMENT_COMPLETED.value
    db.session.commit()
    db.session.close()
    return render_template(
        'drink_bar.html',
        message='Payment successfully completed.',
        transaction_id=transaction_id
    )


"""
===================================
LINE BOT Webhook handler メソッド
===================================
"""


# LINE bot settings
line_bot_api = LineBotApi(os.getenv('LINEBOT_CHANNEL_ACCESS_TOKEN', ''))
handler = WebhookHandler(os.getenv('LINEBOT_CHANNEL_SECRET', ''))


@app.route("/linebot/webhook", methods=['POST'])
def linebot_webhook_handler():
    """
    LINE からのWebhook を受け付けるメソッド

    :return:
    """
    app.logger.info('method linebot_webhook_handler called!!')
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info('Request body: %s', body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError as e:
        app.logger.error('InvalidSignatureError occurred!: %s', e)
        abort(400)
    except Exception as e:
        app.logger.error('Error at line bot webhook: %s', e)
        abort(400)
    return 'OK'


'''
=======================
<LINE BOT>
Follow イベント処理
=======================
'''


@handler.add(FollowEvent)
def follow_event_handler(event):
    """
    フォローイベント（おともだち追加）受信時
    """
    app.logger.info('handler FollowEvent called!! event:%s', event)
    app.logger.info('UserID: %s', event.source.user_id)
    app.logger.info('User type: %s', event.source.type)
    # save user info to db
    user_id = event.source.user_id
    user = User(user_id, 'dummy', UserRole.CONSUMER)
    db.session.add(user)
    db.session.commit()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=True)
    app.logger('LINEBOT_CHANNEL_ACCESS_TOKEN[%s]', os.getenv('LINEBOT_CHANNEL_ACCESS_TOKEN'))
    app.logger('LINEBOT_CHANNEL_SECRET[%s', os.getenv('LINEBOT_CHANNEL_SECRET'))
