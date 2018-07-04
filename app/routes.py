import re
import os
import sys
import json
import random
import requests
from flask import (
    Flask, request, abort, url_for, current_app, render_template
)

from app import app, db
from app.models import Users, TravelPointToken
from app.module.zomato import ZomatoAPI
from app.module.geomaps import GoogleMapsAPI
from instance.config import LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET_TOKEN

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

@app.route('/')
def index():
    return render_template('index.html')

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
    confirm_template = ConfirmTemplate(
        text='Untuk mengoptimalkan penggunaan aplikasi, apakah anda berkenan untuk registrasi secara otomatis?',
     actions=[
        PostbackTemplateAction(
            label='Iya', text='Iya', data='create_user=confirm'),
        PostbackTemplateAction(
            label='Tidak', text='Tidak', data='create_user=decline'),
    ])
    line_bot_api.reply_message(
        event.reply_token,[
        TextSendMessage(
            text="Halo perkenalkan! Nama saya Pandu, disini untuk membantu menjadi pemandu di Smart Environment kita!"),
        TemplateSendMessage(
            alt_text='User Confirmation', template=confirm_template)])

@handler.add(UnfollowEvent)
def handle_unfollow(event):
    app.logger.info("Got Unfollow event")


@handler.add(PostbackEvent)
def handle_postback(event):

    command = (event.postback.data).split('=')

    findUser = Users.query.filter_by(id=event.source.user_id).first()
    if (findUser == None):
        if (command[0] == 'create_user'):
            if (command[1] == 'confirm'):

                try :
                    user_profile = line_bot_api.get_profile(event.source.user_id)
                    new_user = Users(
                        id=user_profile.user_id,
                        name=user_profile.display_name,
                        location='Jakarta, Indonesia',
                        latitude=-6.17511,
                        longitude=106.8650395,
                        travel_point=0
                    )
                    db.session.add(new_user)
                    # Logging
                    app.logger.info("Create User Request: " + user_profile.user_id)
                    line_bot_api.reply_message(
                        event.reply_token, [
                            TextSendMessage(
                                text='Berhasil membuat registrasi untuk user {user}'.format(
                                    user=user_profile.display_name)),
                            TextSendMessage(
                                text='Untuk mengetahui lingkungan Anda, dapatkah Anda membagikan lokasi Anda dengan mengirimkan Send Location?'),
                            TextSendMessage(
                                text='Send Location dapat di temukan di bawah menu, silahkan klik tombol + dan klik Send Location')
                        ])

                    db.session.commit()

                except :
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="Sepertinya ada masalah dalam memperoleh informasi profil Anda"))

            else :
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="Tahap registrasi di tunda, silahkan registrasi untuk menggunakan aplikasi secara lengkap :)"))

    else :
        if (command[0] == 'search_location'):

            sub_command = (command[1]).split(':')
            query, place_name = sub_command

            # To calculate travel_option
            origin = '{lat},{lng}'.format(lat=findUser.latitude, lng=findUser.longitude)

            if (query == 'food'):
                # Zomato API Call
                restaurant_list = ZomatoAPI().geocode(latitude=findUser.latitude, longitude=findUser.longitude)
                price_range = command[2]
                # price_range
                # 1 : < 80
                # 2 : 80 - 150
                # 3 : 150 - 400
                # 4 : > 400

                if (len(restaurant_list) > 2 and restaurant_list != None):
                    # The list of all the carousel columns
                    restaurant_carousel = []

                    # Temporary thumbnail_image
                    thumbnail_image = 'https://i.imgur.com/EFkDB2M.png'
                    for counter, restaurant in enumerate(restaurant_list):
                        destination = '{lat},{lng}'.format(lat=restaurant['restaurant']['location']['latitude'], lng=restaurant['restaurant']['location']['longitude'])
                        # Carousel Column
                        restaurant_column = CarouselColumn(
                            title=str(restaurant['restaurant']['name'])[:40],
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
                        if counter < 6:
                            restaurant_carousel.append(restaurant_column)
                        else :
                            break

                    food_carousel = CarouselTemplate(columns=restaurant_carousel)
                    line_bot_api.reply_message(
                        event.reply_token,[
                        TextSendMessage(
                            text="Saya akan carikan tempat {place} didekat posisi Anda...".format(
                                place=place_name)),
                        TemplateSendMessage(
                            alt_text='Restaurant Carousel', template=food_carousel)
                        ])

                else :
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="Maaf...tapi saat ini kita tidak menemukan restaurant di dekat Anda"))

            else :
                search_places = GoogleMapsAPI().places(query=query, location=(findUser.latitude, findUser.longitude))
                places_list = search_places['results']

                if (len(places_list) > 2 and places_list != None):
                    # The list of all the carousel columns
                    places_carousel = []
                    # Temporary thumbnail_image
                    thumbnail_image = 'https://i.imgur.com/EFkDB2M.png'
                    for counter, places in enumerate(places_list):
                        destination = '{lat},{lng}'.format(
                            lat=places['geometry']['location']['lat'],
                            lng=places['geometry']['location']['lng'])

                        # Carousel Column
                        places_column = CarouselColumn(
                            title=str(places['name'])[:40],
                            text=str(places['formatted_address'])[:60],
                            thumbnail_image_url=thumbnail_image,
                            actions=[
                            URITemplateAction(
                                label='Cek Peta',
                                uri='https://www.google.com/maps/search/?api=1&query={destination}'.format(
                                    destination=destination)),
                            PostbackTemplateAction(
                                label='Pilihan Perjalanan',
                                data='travel_option={origin}={destination}'.format(
                                    origin=origin, destination=destination))
                        ])

                        # Force Stop by Counter
                        if counter < 6:
                            places_carousel.append(places_column)
                        else :
                            break

                    search_carousel = CarouselTemplate(columns=places_carousel)
                    line_bot_api.reply_message(
                        event.reply_token,[
                        TextSendMessage(text="Saya akan carikan {place} didekat posisi Anda...".format(
                            place=place_name)),
                        TemplateSendMessage(
                            alt_text='Places Carousel', template=search_carousel)
                        ])

                else :
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="Maaf...tapi saat ini kita tidak menemukan {query} di dekat Anda".format(
                                query=query)))

        elif (command[0] == 'location_update'):
            if (command[1] == 'search_for_unknown'):
                data_search = command[2]
                location_confirm = ConfirmTemplate(text='Apakah anda sedang berada di {location}?'.format(location=findUser.location),
                actions=[
                    PostbackTemplateAction(
                        label='Iya', text='Iya', data='search_location={search}'.format(search=data_search)),
                    PostbackTemplateAction(
                        label='Tidak', text='Tidak', data='location_update=None')
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

            else :
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="Baiklah, silahkan perbarui lokasi Anda dengan mengirimkan lokasi"))


        elif (command[0] == 'travel_option'):
            origin = command[1]
            destination = command[2]

            dist_calculation = GoogleMapsAPI().distanceCalculate(origin, destination)
            dist_cut = dist_calculation['rows'][0]['elements'][0]
            distance = {
                "text" : dist_cut['distance']['text'],
                "value" : dist_cut['distance']['value'],
                "duration" : dist_cut['duration']['text']
            }

            travel_options = [
            {'label' : 'Jalan Kaki', 'uri' : 'https://www.google.com/maps/dir/?api=1&parameters'},
            {'label' : 'Naik Sepeda', 'uri' : 'https://www.google.com/maps/dir/?api=1&parameters'},
            {'label' : 'Naik Bus', 'uri' : 'https://www.google.com/maps/dir/?api=1&parameters'},
            {'label' : 'Menyetir', 'uri' : 'https://www.google.com/maps/dir/?api=1&parameters'}
            ]

            travel_carousel = []
            thumbnail_image = 'https://i.imgur.com/EFkDB2M.png'

            for options in travel_options:

                travel_column = ImageCarouselColumn(
                    image_url=thumbnail_image,
                    action=URITemplateAction(
                        label=options['label'],
                        uri=options['uri']))

                if (distance['value'] >= 5000):
                    # Don't recommend walking more than 5km
                    if (options['label'] != 'Jalan Kaki'):
                        travel_carousel.append(travel_column)
                else :
                    travel_carousel.append(travel_column)

            travel_option_template = ImageCarouselTemplate(columns=travel_carousel)

            line_bot_api.reply_message(
                event.reply_token,[
                TextSendMessage(
                    text="Saya perkirakan bahwa Anda akan tiba pada lokasi dalam {time}".format(
                        time=distance['duration'])),
                TextSendMessage(
                    text="Dengan jarak {range}, di bawah adalah rekomendasian perjalanan".format(
                        range=distance['text'])),
                TemplateSendMessage(
                    alt_text='Pilihan Perjalanan', template=travel_option_template)
                ])

        elif (command[0] == 'point_exchange'):
            promotion_category = command[1]

            # Find Categories from database and iterate over them like a list
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="Anda sudah melakukan registrasi otomatis"))

        elif (command[0] == 'create_user'):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="Anda sudah melakukan registrasi otomatis"))

        else :
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="Sepertinya ada masalah dalam PostbackEvent Anda"))


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
                                    action=MessageTemplateAction(
                                        label='Makan', text='Carikan tempat makan di dekat lokasi saya')),
                ImageCarouselColumn(image_url=thumbnail_image,
                                    action=MessageTemplateAction(
                                        label='Bioskop', text='Carikan bioskop di dekat lokasi saya')),
                ImageCarouselColumn(image_url=thumbnail_image,
                                    action=MessageTemplateAction(
                                        label='Minimarket', text='Carikan minimartket di dekat lokasi saya')),
                ImageCarouselColumn(image_url=thumbnail_image,
                                    action=MessageTemplateAction(
                                        label='Halte Bus', text='Carikan halte bus di dekat lokasi saya')),
                ImageCarouselColumn(image_url=thumbnail_image,
                                    action=MessageTemplateAction(
                                        label='Cuaca', text='Cek cuaca hari ini di lokasi saya'))
            ])

            line_bot_api.reply_message(
                event.reply_token,[
                TextSendMessage(text="Lokasi Anda sudah diperbarui!"),
                TemplateSendMessage(
                    alt_text='Pilihan Aplikasi', template=image_option_template)
                ])

        except :
            line_bot_api.reply_message(
                event.reply_token,[
                TextSendMessage(text="Lokasi Anda tidak berhasil diperbarui!"),
                TextSendMessage(text="Silahkan coba lagi nanti")])
    else :
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="Sepertinya Anda belum registrasi, silahkan registrasi terlebih dahulu"))

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """ Here's all the messages will be handled and processed by the program """
    msg = (event.message.text).lower()
    price_range = None

    findUser = Users.query.filter_by(id=event.source.user_id).first()
    if (findUser != None):
        with open('data/keyword.json', 'r') as keyword_list:
            keyword = json.load(keyword_list)
        if ('cari' in msg):
            data_search = None
            # In keyword.json, iterate over the multidimensional array
            # to find a match to any keyword in msg
            for key, value in keyword['search'].items():
                for word in value:
                    if (word in msg):
                        data_search = key
                        break

            # If data_search is not updated, then search is not found
            if (data_search is None):
                # If no search is found by the keyword, then ask the user if they still want an answer
                # By searching for the whole message
                search_confirm = ConfirmTemplate(
                    text='Sepertinya kata kunci ini belum di registrasikan secara resmi oleh Pandu, apakah ingin tetap mencari {message}?'.format(
                        message=msg
                    ),
                actions=[
                    PostbackTemplateAction(
                        label='Iya', text='Iya', data='location_update=search_for_unknown={search}'.format(
                            search=msg + ':hasil pencarian')),
                    PostbackTemplateAction(
                        label='Tidak', text='Tidak', data='location_update=None')
                    ])

                line_bot_api.reply_message(
                    event.reply_token,[
                    TemplateSendMessage(
                        alt_text='Unknown Keyword Confirmation', template=search_confirm),
                    TextSendMessage(
                        text='Hasil pencarian mungkin tidak akurat karena kata kunci belum terdaftar secara resmi sebagai titik pencarian yang valid.'
                    )
                    ])

            else :
                # this line will execute if it has found a match in keyword.json
                location_confirm = ConfirmTemplate(text='Apakah anda sedang berada di {location}?'.format(location=findUser.location),
                actions=[
                    PostbackTemplateAction(
                        label='Iya', text='Iya', data='search_location={search}={price}'.format(search=data_search, price=price_range)),
                    PostbackTemplateAction(
                        label='Tidak', text='Tidak', data='location_update=None')
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
            # Placeholder
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="Terlihat mendung sih di jalanan"))

        elif ('token' in msg):
            input_token = (msg.split()[1]).upper()

            find_token = TravelPointToken.query.filter_by(token_id=input_token).first()

            if (find_token != None):
                findUser.travel_point += find_token.token_point_value
                app.logger.info('{user} gained {value} points from {provider_name}'.format(
                    user=findUser.id,
                    value=find_token.token_point_value,
                    provider_name=find_token.token_name
                ))
                find_token.token_point_visitor += 1
                db.session.commit()

                line_bot_api.reply_message(
                    event.reply_token,[
                    TextSendMessage(
                        text="Selamat! Anda mendapatkan {value} Points dari {provider_name}".format(
                            value=find_token.token_point_value,
                            provider_name=find_token.token_name
                        )),
                    TextSendMessage(
                        text="Travel point Anda sekarang {point} token entered : {token}".format(
                            point=findUser.travel_point,
                            token=input_token
                        ))
                    ])

            else :
                line_bot_api.reply_message(
                    event.reply_token,[
                    TextSendMessage(
                        text="Token tidak dikenal oleh Pandu, coba cek kembali token yang di berikan"),
                    TextSendMessage(
                        text="Travel point Anda sekarang {point}".format(
                            point=findUser.travel_point
                        ))
                    ])

        elif ('tukar' in msg or 'tuker' in msg):
            exchange_option_template = ImageCarouselTemplate(columns=[
                ImageCarouselColumn(image_url=thumbnail_image,
                                    action=PostbackTemplateAction(
                                        label='Belanja', data='point_exchange=shop')),
                ImageCarouselColumn(image_url=thumbnail_image,
                                    action=PostbackTemplateAction(
                                        label='Makan Murah', data='point_exchange=food')),
                ImageCarouselColumn(image_url=thumbnail_image,
                                    action=PostbackTemplateAction(
                                        label='Voucher Game', data='point_exchange=game')),
                ImageCarouselColumn(image_url=thumbnail_image,
                                    action=PostbackTemplateAction(
                                        label='Isi Pulsa', data='point_exchange=pulsa')),
                ImageCarouselColumn(image_url=thumbnail_image,
                                    action=PostbackTemplateAction(
                                        label='Tiket Murah', text='Cek cuaca hari ini di lokasi saya'))
            ])

            line_bot_api.reply_message(
                event.reply_token,[
                TextSendMessage(text="Silahkan Pilih dari kategori yang kami sediakan!"),
                TemplateSendMessage(
                    alt_text='Pilihan Tukar Point', template=exchange_option_template)
                ])

        elif ('cek' in msg):

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="Travel point Anda sekarang {point}".format(
                        point=findUser.travel_point
                    )))

        else :
            # Interaction
            interaction_response = None
            with open('data/speech.json', 'r') as speechwords:
                speech = json.load(speechwords)

            for key, value in keyword['interaction'].items():
                for word in value:
                    if (word in msg):
                        interaction_response = (random.choice(speech['speech'][key]['answer']).format(
                            name = findUser.name,
                            baseball = 'baseball'
                        ))
                        break

            if (interaction_response != None):
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text=interaction_response))

    else :
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="Sepertinya Anda belum registrasi, silahkan registrasi terlebih dahulu"))


@handler.default()
def default(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text="Jenis obrolan tidak didukung oleh ..."))
