import os
import sys
import json
import requests
from flask import Flask, request, abort, url_for, current_app

from app import app, db
from app.models import Users
from app.module.zomato import ZomatoAPI
from instance.config import LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET_TOKEN
from instance.config import ZOMATO_API_KEY

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    SourceUser, SourceGroup, SourceRoom,
    TemplateSendMessage, ConfirmTemplate, MessageTemplateAction,
    ButtonsTemplate, ImageCarouselTemplate, ImageCarouselColumn, URITemplateAction,
    PostbackTemplateAction, DatetimePickerTemplateAction,
    CarouselTemplate, CarouselColumn, PostbackEvent,
    StickerMessage, StickerSendMessage, LocationMessage, LocationSendMessage,
    ImageMessage, VideoMessage, AudioMessage, FileMessage,
    UnfollowEvent, FollowEvent, JoinEvent, LeaveEvent, BeaconEvent
)

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET_TOKEN)

@app.route("/callback", methods=['POST'])
def callback():
    # Get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # Get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # Handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(FollowEvent)
def handle_followevent(event):
    """ When a FollowEvent is done, it will activate the SignUp Flow"""
    confirm_template = ConfirmTemplate(text='Untuk mengoptimalkan penggunaan aplikasi, apakah anda berkenan untuk registrasi secara otomatis?', actions=[
        PostbackTemplateAction(label='Iya', text='Iya, registrasikan akun saya', data='create_user=confirm'),
        PostbackTemplateAction(label='Tidak', text='Tidak, jangan registrasikan akun saya', data='create_user=decline'),
    ])
    line_bot_api.reply_message(
        event.reply_token,[
        TextSendMessage(text="Halo perkenalkan! Nama saya ... disini untuk membantu Anda"),
        TemplateSendMessage(
            alt_text='User Confirmation', template=confirm_template)])

@handler.add(UnfollowEvent)
def handle_unfollow(event):
    app.logger.info("Got Unfollow event")
    print("Got Unfollow event")

    findUser = Users.query.filter_by(id=event.source.user_id).first()

    if findUser != None:
        db.session.delete(findUser)
        app.logger.info("User {} deleted from Database".format(event.source.user_id))
    else :
        app.logger.info("Unable to perform deletion upon user {}".format(event.source.user_id))

@handler.add(PostbackEvent)
def handle_postback(event):

    command = (event.postback.data).split('=')

    if command[0] == 'create_user':
        if command[1] == 'confirm':
            findUser = Users.query.filter_by(id=event.source.user_id).first()

            if findUser == None:
                try :
                    user_profile = line_bot_api.get_profile(event.source.user_id)
                    new_user = Users(
                        id=user_profile.user_id,
                        name=user_profile.display_name,
                        location='Jakarta, Indonesia',
                        latitude=-6.17511,
                        longitude=106.8650395
                    )
                    db.session.add(new_user)
                    # Logging
                    app.logger.info("Create User Request: " + user_profile.user_id)
                    line_bot_api.reply_message(
                        event.reply_token, [
                            TextSendMessage(text='Berhasil membuat registrasi untuk user {}'.format(user_profile.display_name)),
                            TextSendMessage(text='Untuk mengetahui lingkungan Anda, dapatkah Anda membagikan lokasi Anda?')
                        ])

                    db.session.commit()

                except :
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="Sepertinya ada masalah dalam memperoleh informasi profil Anda"))

            else :
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="Sepertinya Anda sudah registrasi, membatalkan proses registrasi"))
        else :
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="Tahap registrasi di tunda, silahkan registrasi untuk menggunakan aplikasi secara lengkap :)"))

    elif command[0] == 'location_confirm':
        if command[1] == 'True':
            findUser = Users.query.filter_by(id=event.source.user_id).first()
            if findUser != None:
                if command[2] == 'food':

                    # Zomato API Call
                    restaurant_carousel = []
                    restaurant_list = ZomatoAPI().geocode(latitude=findUser.latitude, longitude=findUser.longitude)

                    counter = 0

                    if len(restaurant_list) > 2:
                        for restaurant in restaurant_list:
                            if (restaurant['restaurant']['featured_image'] == '' or restaurant['restaurant']['featured_image'] == None):
                                thumbnail_image = 'https://i.imgur.com/EFkDB2M.png'
                            else :
                                thumbnail_image = (restaurant['restaurant']['featured_image']).replace('webp', 'png')

                            restaurant_column = CarouselColumn(
                                text=restaurant['restaurant']['location']['address'],
                                title=restaurant['restaurant']['name'],
                                thumbnail_image_url=thumbnail_image,
                                actions=[
                                URITemplateAction(
                                    label='Cek Menu', uri=restaurant['restaurant']['menu_url']),
                                    PostbackTemplateAction(label='Informasi Lebih', data='restaurant_details')
                                    ])
                            restaurant_carousel.append(restaurant_column)



                            food_carousel = CarouselTemplate(columns=restaurant_carousel)

                            line_bot_api.reply_message(
                            event.reply_token,[
                                TextSendMessage(text="Kami akan carikan tempat makan didekat posisi Anda..."),
                                TemplateSendMessage(alt_text='Restaurant Carousel', template=food_carousel)
                                ])

                    else :
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(text="Maaf...tapi saat ini kita tidak menemukan restaurant di dekat Anda"))
                else :
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="Kami akan carikan tempat didekat posisi Anda..."))
            else :
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="Sepertinya Anda belum registrasi, silahkan registrasi terlebih dahulu"))
        else :
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="Baiklah, silahkan perbarui lokasi Anda dengan mengirimkan lokasi Anda"))

    else :
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="Sepertinya ada masalah dalam PostbackEvent Anda"))


@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    #current_location = {}
    #current_location['location'] = event.message.address
    #current_location['latitude'] = event.message.latitude
    #current_location['longitude'] = event.message.longitude

    findUser = Users.query.filter_by(id=event.source.user_id).first()

    if findUser != None:
        try:
            findUser.location = (event.message.address)[:100]
            findUser.latitude = event.message.latitude
            findUser.longitude = event.message.longitude
            db.session.commit()

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="Lokasi Anda sudah diperbarui!"))

        except :
            line_bot_api.reply_message(
                event.reply_token,[
                TextSendMessage(text="Lokasi Anda tidak berhasil diperbarui!"),
                TextSendMessage(text="Silahkan coba lagi nanti")])
    else :
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="Sepertinya Anda belum registrasi, silahkan registrasi terlebih dahulu"))

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """ Here's all the messages will be handled and processed by the program """
    msg = event.message.text
    findUser = Users.query.filter_by(id=event.source.user_id).first()

    if findUser != None:
            if 'cari' in msg:
                if 'makan' in msg:
                    data_search = 'food'
                else :
                    data_search = 'else'

                location_confirm = ConfirmTemplate(text='Apakah anda sedang berada di {0}?'.format(findUser.location),
                actions=[
                    PostbackTemplateAction(label='Iya', text='Iya', data='location_confirm=True={}'.format(data_search)),
                    PostbackTemplateAction(label='Tidak', text='Tidak', data='location_confirm=False'),
                    ])

                line_bot_api.reply_message(
                    event.reply_token,[
                    LocationSendMessage(
                        title='Posisi Terakhir Anda', address='{0}'.format(findUser.location),
                        latitude=findUser.latitude, longitude=findUser.longitude
                    ),
                    TemplateSendMessage(
                        alt_text='Location Confirmation', template=location_confirm)
                    ])


@handler.default()
def default(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
        text="Jenis obrolan tidak didukung oleh ..."))
