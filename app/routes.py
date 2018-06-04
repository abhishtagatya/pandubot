import os
import sys
import json
import requests
from flask import Flask, request, abort, url_for, current_app

from app import app, db
from app.models import Users
from app.module.zomato import ZomatoAPI
from app.module.geomaps import GoogleMapsAPI
from instance.config import LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET_TOKEN
from instance.config import ZOMATO_API_KEY
from instance.config import GOOGLE_MAPS_API_KEY

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


@handler.add(PostbackEvent)
def handle_postback(event):

    command = (event.postback.data).split('=')

    if (command[0] == 'create_user'):
        if (command[1] == 'confirm'):
            findUser = Users.query.filter_by(id=event.source.user_id).first()

            if (findUser == None):
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
                            TextSendMessage(text='Berhasil membuat registrasi untuk user {user}'.format(user=user_profile.display_name)),
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

    elif (command[0] == 'search'):
        if (command[1] == 'location_confirm'):
            if (command[2] == 'True'):
                findUser = Users.query.filter_by(id=event.source.user_id).first()
                if (findUser != None):
                    if (command[3] == 'food'):
                        # Zomato API Call
                        # To Do:
                        #   - Clean Up code
                        #   - Fix Internal Server Error on line 134 - 164
                        restaurant_list = ZomatoAPI().geocode(latitude=findUser.latitude, longitude=findUser.longitude)

                        # To calculate travel_option
                        origin = ''

                        if (len(restaurant_list) > 2 and restaurant_list != None):
                            counter = 0

                            # The list of all the carousel columns
                            restaurant_carousel = []

                            # Temporary thumbnail_image
                            thumbnail_image = 'https://i.imgur.com/EFkDB2M.png'
                            for restaurant in restaurant_list:
                                destination = ''

                                # Carousel Column
                                restaurant_column = CarouselColumn(
                                    title=str(restaurant['restaurant']['name']),
                                    text=str(restaurant['restaurant']['location']['address'])[:60],
                                    thumbnail_image_url=thumbnail_image,
                                    actions=[
                                    URITemplateAction(
                                        label='Cek Restoran',
                                        uri=restaurant['restaurant']['url']),
                                    PostbackTemplateAction(
                                        label='Pilihan Perjalanan',
                                        data='travel_option={origin}={destination}'.format(origin=origin, destination=destination))
                                ])

                                # Force Stop by Counter
                                counter += 1
                                if counter < 6:
                                    restaurant_carousel.append(restaurant_column)
                                else :
                                    break

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

                        query = command[3]
                        # Google Maps API Call
                        # To Do:
                        #   - Clean Up code
                        search_places = GoogleMapsAPI().places(query=query, location=(findUser.latitude, findUser.longitude))
                        places_list = search_places['results']

                        # To calculate travel_option
                        origin = '{lat},{lng}'.format(lat=findUser.latitude, lng=findUser.longitude)

                        if (len(places_list) > 2 and places_list != None):
                            counter = 0

                            # The list of all the carousel columns
                            places_carousel = []

                            # Temporary thumbnail_image
                            thumbnail_image = 'https://i.imgur.com/EFkDB2M.png'
                            for places in places_list:
                                destination = '{lat},{lng}'.format(lat=places['geometry']['location']['lat'], lng=places['geometry']['location']['lng'])

                                # Carousel Column
                                places_column = CarouselColumn(
                                    title=str(places['name']),
                                    text=str(places['formatted_address'])[:60],
                                    thumbnail_image_url=thumbnail_image,
                                    actions=[
                                    URITemplateAction(
                                        label='Cek Peta',
                                        uri='https://www.google.com/maps/search/?api=1&query={destination}'.format(destination=destination)),
                                    PostbackTemplateAction(
                                        label='Pilihan Perjalanan',
                                        data='travel_option={origin}={destination}'.format(origin=origin, destination=destination))
                                ])

                                # Force Stop by Counter
                                counter += 1
                                if counter < 6:
                                    places_carousel.append(places_column)
                                else :
                                    break

                            search_carousel = CarouselTemplate(columns=places_carousel)
                            line_bot_api.reply_message(
                                event.reply_token,[
                                TextSendMessage(text="Kami akan carikan {query} didekat posisi Anda...".format(query=query)),
                                TemplateSendMessage(alt_text='Places Carousel', template=search_carousel)
                                ])

                        else :
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(text="Maaf...tapi saat ini kita tidak menemukan {query} di dekat Anda".format(query=query)))

                else :
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="Sepertinya Anda belum registrasi, silahkan registrasi terlebih dahulu"))
            else :
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="Baiklah, silahkan perbarui lokasi Anda dengan mengirimkan lokasi Anda"))

    elif (command[0] == 'travel_option'):
        pass

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

    if (findUser != None):
        try:
            findUser.location = (event.message.address)[:100]
            findUser.latitude = event.message.latitude
            findUser.longitude = event.message.longitude
            db.session.commit()

            thumbnail_image = 'https://i.imgur.com/EFkDB2M.png'

            image_option_template = ImageCarouselTemplate(columns=[
                ImageCarouselColumn(image_url=thumbnail_image,
                                    action=MessageTemplateAction(label='Cari Makan', text='Carikan tempat makan dekat lokasi saya')),
                ImageCarouselColumn(image_url=thumbnail_image,
                                    action=MessageTemplateAction(label='Cek Cuaca', text='Cek cuaca hari ini di lokasi saya'))
            ])

            line_bot_api.reply_message(
                event.reply_token,[
                TextSendMessage(text="Lokasi Anda sudah diperbarui!"),
                TemplateSendMessage(alt_text='Pilihan Aplikasi', template=image_carousel_template)
                ])

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

    if (findUser != None):
        if ('cari' in msg):
            if ('makan' in msg or 'jajan' in msg):
                data_search = 'food'
            elif ('bioskop' in msg or 'cinema' in msg):
                data_search = 'movie theater'
            elif ('mart' in msg or 'market' in msg):
                data_search = 'minimarket'
            elif ('fotokopi' in msg or 'print' in msg):
                data_search = 'print'
            elif ('busway' in msg or 'halte' in msg):
                data_search = 'bus station'
            else :
                data_search = 'else'

            location_confirm = ConfirmTemplate(text='Apakah anda sedang berada di {0}?'.format(findUser.location),
            actions=[
                PostbackTemplateAction(label='Iya', text='Iya', data='search=location_confirm=True={search}'.format(search=data_search)),
                PostbackTemplateAction(label='Tidak', text='Tidak', data='search=location_confirm=False'),
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

        elif ('cuaca' in msg):
            pass
        else :
            pass


@handler.default()
def default(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
        text="Jenis obrolan tidak didukung oleh ..."))
