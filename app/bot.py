import json
import random

from app import app, db
from app.models import *
from app.module import *
from instance.config import LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET_TOKEN

from flask import (
    Flask, request, abort
)

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
            text="Halo perkenalkan! Nama saya Pandu, disini untuk membantu menjadi pemandu Anda di Smart Environment kita!"),
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
        # If the user is not found on our database
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
                                text='Send Location dapat di temukan di bawah menu, silahkan klik tombol + dan klik Send Location atau bisa klik link ini line://nv/location')
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
        # If the user is found
        if (command[0] == 'search_location'):
            carousel_limit = 6

            sub_command = command[1].split(':')
            query, place_name = sub_command

            # To calculate travel_option
            origin = '{lat},{lng}'.format(lat=findUser.latitude, lng=findUser.longitude)

            if (query == 'food'):
                # Zomato API Call
                restaurant_list = ZomatoAPI().geocode(latitude=findUser.latitude, longitude=findUser.longitude)

                if (len(restaurant_list) > 2 and restaurant_list != None):
                    # The list of all the carousel columns
                    restaurant_carousel = []

                    # Temporary thumbnail_image
                    thumbnail_image = 'https://location-linebot.herokuapp.com/static/img/location_thumbnail/restaurant.png'
                    for restaurant in restaurant_list[:carousel_limit]:
                        destination = '{lat},{lng}'.format(
                            lat=restaurant['restaurant']['location']['latitude'],
                            lng=restaurant['restaurant']['location']['longitude'])

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
                                data='travel_option={origin}={destination}'.format(
                                    origin=origin, destination=destination))
                        ])

                        restaurant_carousel.append(restaurant_column)

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
                    for places in places_list[:carousel_limit]:
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

                        places_carousel.append(places_column)

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
                # If places not supported in keyword.json, make an attempt
                # to search via passed in string as argument
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
                        text="Baiklah, silahkan perbarui lokasi Anda dengan mengirimkan lokasi line://nv/location"))

        elif (command[0] == 'travel_option'):
            origin = command[1]
            destination = command[2]

            coordinate = [findUser.latitude, findUser.longitude]

            dist_calculation = GoogleMapsAPI().distanceCalculate(origin, destination)
            dist_cut = dist_calculation['rows'][0]['elements'][0]
            distance = {
                "text" : dist_cut['distance']['text'],
                "value" : dist_cut['distance']['value'],
                "duration" : dist_cut['duration']['text']
            }

            with open('data/travelopt.json', 'r') as travelopt:
                travel_options = json.load(travelopt)

            travel_carousel = []
            thumbnail_image = 'https://i.imgur.com/EFkDB2M.png'

            for options in travel_options:

                travel_column = ImageCarouselColumn(
                    image_url=options['thumbnail_image'],
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

            # Weather API
            with open('data/weathermapping.json', 'r') as wm:
                weather_mapping = json.load(wm)

            get_weather = OpenWeatherAPI().current_weather(coordinate=coordinate)
            current_weather = None

            for id, name in weather_code_range:
                if (get_weather['weather'][0]['id'] in id):
                    current_weather = name
                    break

            line_bot_api.reply_message(
                event.reply_token,[
                TextSendMessage(
                    text="Saya perkirakan bahwa Anda akan tiba pada lokasi dalam {time}".format(
                        time=distance['duration'])),
                TextSendMessage(
                    text="Dengan jarak {range}, di bawah adalah rekomendasian perjalanan".format(
                        range=distance['text'])),
                TemplateSendMessage(
                    alt_text='Pilihan Perjalanan', template=travel_option_template),
                TextSendMessage(
                    text="Cuaca di luar terlihat {weather}, {prompt}.".format(
                        weather=weather_mapping[current_weather]['name'],
                        prompt=weather_mapping[current_weather]['prompt']
                    ))
                ])

        elif (command[0] == 'point_exchange'):
            promotion_category = command[1]

            # Find Categories from database and iterate over them like a list
            findPromotion = TravelPointPromotion.query.filter_by(promotion_category=promotion_category).all()

            promotion_carousel = []

            for promotion in findPromotion:

                promotion_column = CarouselColumn(
                    title=str(promotion.promotion_name)[:40],
                    text=str(promotion.promotion_description)[:60],
                    actions=[
                    PostbackTemplateAction(
                        label='Tukar Point',
                        data="point_exchange_confirm={promotion_id}".format(
                            promotion_id=promotion.promotion_id
                        )),
                    PostbackTemplateAction(
                        label='Cek Harga Point',
                        data="check_promotion_price={cost}".format(
                            cost=promotion.promotion_cost
                        ))
                    ])

                promotion_carousel.append(promotion_column)


            promotion_template_carousel = CarouselTemplate(columns=promotion_carousel)
            line_bot_api.reply_message(
                event.reply_token,[
                TextSendMessage(
                    text="Saya akan carikan point exchange untuk kategori {category}".format(
                        category=promotion_category)),
                TemplateSendMessage(
                    alt_text='Promotion Carousel', template=promotion_template_carousel)
                ])

        elif (command[0] == 'point_exchange_confirm'):
            promotion_onconfirm = command[1]
            findPromotion = TravelPointPromotion.query.filter_by(promotion_id=promotion_onconfirm).first()

            if (findUser.travel_point > findPromotion.promotion_cost):
                findUser.travel_point -= findPromotion.promotion_cost
                db.session.commit()
                line_bot_api.reply_message(
                    event.reply_token, [
                    TextSendMessage(
                        text="Selamat Anda telah membeli promosi {name}, sisa poin Anda sekarang {point}".format(
                            name=findPromotion.promotion_name,
                            point=findUser.travel_point
                        )),
                    TextSendMessage(
                        text="Promotion Secret : {secret} ".format(
                            secret=findPromotion.promotion_secret
                        ))
                    ])
            else :
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="Point Anda kurang untuk melakukan transaksi ini"))

        elif (command[0] == 'check_promotion_price'):
            cost_of_promotion = command[1]

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="Dibutuhkan {cost} point untuk melakukan transaksi ini, Anda memiliki {point}".format(
                        cost=cost_of_promotion,
                        point=findUser.travel_point
                    )))

        elif (command[0] == 'waste_market'):
            waste_category = command[1]

            findMarket = MarketPlaceDatabase.query.filter_by(market_demand=waste_category).all()

            if (len(findMarket) >= 2):
                market_carousel = []

                for market in findMarket:

                    market_column = CarouselColumn(
                        title=str(market.market_name)[:40],
                        text="Rp{price}/kg\n{description}\nMore...".format(
                            price=str(market.market_price),
                            description=market.market_description[:45]
                        ),
                        actions=[
                        PostbackTemplateAction(
                            label='Deskripsi',
                            data="waste_market_info={market_id}".format(
                                market_id=market.market_id
                            )),
                        URITemplateAction(
                            label='Contact',
                            uri="tel:{number}".format(
                                number=market.market_owner_number
                            ))
                        ])

                    market_carousel.append(market_column)


                market_template_carousel = CarouselTemplate(columns=market_carousel)
                line_bot_api.reply_message(
                    event.reply_token,[
                    TextSendMessage(
                        text="Mencari Pasar limbah dalam kategori {category}".format(
                            category=waste_category)),
                    TemplateSendMessage(
                        alt_text='Waste Market Carousel', template=market_template_carousel)
                    ])

            else :
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="Masalah dalam mencari pasar limbah, silahkan coba lagi dalam sesaat..."))

        elif (command[0] == 'waste_market_info'):
            passed_market_id = command[1]
            findMarket = MarketPlaceDatabase.query.filter_by(market_id=passed_market_id).first()

            description_string = "{name}\n{owner}\n\n{demand}\n{description}\n\n{additional}\n\nRp{price}/kg\n\nContact\n{line} - {number}".format(
                name=findMarket.market_name,
                owner=findMarket.market_owner,
                demand=findMarket.market_demand,
                description=findMarket.market_description,
                additional=findMarket.market_additional,
                price=findMarket.market_price,
                line=findMarket.market_owner_line_id,
                number=findMarket.market_owner_number
            )

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=description_string))

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

    findUser = Users.query.filter_by(id=event.source.user_id).first()

    if (findUser != None):
        try:
            findUser.location = (event.message.address)[:100]
            findUser.latitude = event.message.latitude
            findUser.longitude = event.message.longitude
            db.session.commit()

            thumbnail_image = (
                'https://location-linebot.herokuapp.com/static/img/location_thumbnail/restaurant.png',
                'https://location-linebot.herokuapp.com/static/img/location_thumbnail/ticketbooth.png',
                'https://location-linebot.herokuapp.com/static/img/location_thumbnail/mart.png',
                'https://location-linebot.herokuapp.com/static/img/location_thumbnail/busstation.png',
                'https://location-linebot.herokuapp.com/static/img/location_thumbnail/qm.png'
            )

            image_option_template = ImageCarouselTemplate(columns=[
                ImageCarouselColumn(image_url=thumbnail_image[0],
                                    action=MessageTemplateAction(
                                        label='Makan', text='Carikan tempat makan di dekat lokasi saya')),
                ImageCarouselColumn(image_url=thumbnail_image[1],
                                    action=MessageTemplateAction(
                                        label='Bioskop', text='Carikan bioskop di dekat lokasi saya')),
                ImageCarouselColumn(image_url=thumbnail_image[2],
                                    action=MessageTemplateAction(
                                        label='Minimarket', text='Carikan minimartket di dekat lokasi saya')),
                ImageCarouselColumn(image_url=thumbnail_image[3],
                                    action=MessageTemplateAction(
                                        label='Halte Bus', text='Carikan halte bus di dekat lokasi saya')),
                ImageCarouselColumn(image_url=thumbnail_image[4],
                                    action=MessageTemplateAction(
                                        label='Lainnya', text='Carikan {place} di dekat lokasi saya'.format(
                                            place=random.choice(['restoran', 'atm', 'tempat poton rambut', 'salon', 'halte bus', 'warung', 'bioskop'])
                                        ))),
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
                TextSendMessage(text="Silahkan coba lagi nanti")
                ])
    else :
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="Sepertinya Anda belum registrasi, silahkan registrasi terlebih dahulu"))

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """ Here's all the messages will be handled and processed by the program """
    msg = (event.message.text).lower()

    findUser = Users.query.filter_by(id=event.source.user_id).first()
    if (findUser != None):
        with open('data/keyword.json', 'r') as keyword_list:
            keyword = json.load(keyword_list)
        if ('cari' in msg):
            data_search = None
            # In keyword.json, iterate over the json
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
                        label='Iya', text='Iya', data='search_location={search}'.format(search=data_search)),
                    PostbackTemplateAction(
                        label='Tidak', text='Tidak', data='location_update=None')
                    ])

                line_bot_api.reply_message(
                    event.reply_token,[
                    LocationSendMessage(
                        title='Posisi Terakhir Anda', address=findUser.location,
                        latitude=findUser.latitude, longitude=findUser.longitude
                    ),
                    TemplateSendMessage(
                        alt_text='Location Confirmation', template=location_confirm)
                    ])

        elif ('cuaca' in msg):
            coordinate = [findUser.latitude, findUser.longitude]
            get_weather = OpenWeatherAPI().current_weather(coordinate=coordinate)

            with open('data/weathermapping.json', 'r') as wm:
                weather_mapping = json.load(wm)

            for id, name in weather_code_range:
                if (get_weather['weather'][0]['id'] in id):
                    current_weather = name
                    break

            if (get_weather['cod'] == 200 and current_weather != None):
                line_bot_api.reply_message(
                    event.reply_token,[
                    TextSendMessage(
                        text="Coba Pandu cek di openweathermap.org"
                    ),
                    TextSendMessage(
                        text="Cuaca di luar terlihat {weather}, {prompt}.".format(
                            weather=weather_mapping[current_weather]['name'],
                            prompt=weather_mapping[current_weather]['prompt']
                        ))])
            else :
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="Sepertinya kita sedang mengalami masalah mendapatkan cuaca tempat Anda, silahkan mencoba lagi dalam beberapa saat."))

        elif ('bersih' in msg or 'lingkungan' in msg):
            with open('data/envtips.json', 'r') as envtips:
                env_json = json.load(envtips)

            randomize_article = random.choice(env_json)
            article_string = "{title}\n\n{tips}\n\n{source}".format(
                title=randomize_article['title'],
                tips=randomize_article['tips'],
                source=randomize_article['source']
            )
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=article_string))

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
            thumbnail_image = 'https://i.imgur.com/EFkDB2M.png'
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
                                        label='Tiket Murah', data='point_exchange=tiket'))
            ])

            line_bot_api.reply_message(
                event.reply_token,[
                TextSendMessage(text="Silahkan Pilih dari kategori yang kami sediakan!"),
                TemplateSendMessage(
                    alt_text='Pilihan Tukar Point', template=exchange_option_template)
                ])

        elif ('cek' in msg):

            line_bot_api.reply_message(
                event.reply_token, [
                TextSendMessage(
                    text="Travel point Anda sekarang {point}".format(
                        point=findUser.travel_point
                    )),
                TextSendMessage(
                    text="Ingin menukar point Anda? Tinggal minta aja sama Pandu!"
                )
            ])

        elif ('web' in msg):

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="Ini website buatan Digibot Solution http://location-linebot.herokuapp.com"
                ))


        elif ('pandu' in msg and 'id' in msg):

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="Pandu ID : {id}\nTolong di rahasiakan.".format(
                        id=(findUser.id)[:12]
                    )))

        elif ('pasar' in msg and 'limbah' in msg):

            thumbnail_image = 'https://location-linebot.herokuapp.com/static/img/feature_thumbnail/3R.png'
            market_option_template = ImageCarouselTemplate(columns=[
                ImageCarouselColumn(image_url=thumbnail_image,
                                    action=PostbackTemplateAction(
                                        label='Plastik', data='waste_market=plastik')),
                ImageCarouselColumn(image_url=thumbnail_image,
                                    action=PostbackTemplateAction(
                                        label='Kertas', data='waste_market=kertas')),
                ImageCarouselColumn(image_url=thumbnail_image,
                                    action=PostbackTemplateAction(
                                        label='Kardus', data='waste_market=kardus')),
                ImageCarouselColumn(image_url=thumbnail_image,
                                    action=PostbackTemplateAction(
                                        label='Kayu', data='waste_market=kayu')),
                ImageCarouselColumn(image_url=thumbnail_image,
                                    action=PostbackTemplateAction(
                                        label='Gelas', data='waste_market=gelas')),
                ImageCarouselColumn(image_url=thumbnail_image,
                                    action=PostbackTemplateAction(
                                        label='Beling', data='waste_market=beling')),
                ImageCarouselColumn(image_url=thumbnail_image,
                                    action=PostbackTemplateAction(
                                        label='Baterai', data='waste_market=baterai')),
                ImageCarouselColumn(image_url=thumbnail_image,
                                    action=PostbackTemplateAction(
                                        label='E-Waste', data='waste_market=electronic waste')),
                ImageCarouselColumn(image_url=thumbnail_image,
                                    action=PostbackTemplateAction(
                                        label='Lainnya', data='waste_market=lainnya')),
            ])

            line_bot_api.reply_message(
                event.reply_token,[
                TextSendMessage(text="Silahkan cari dari kategori yang kami sediakan!"),
                TemplateSendMessage(
                    alt_text='Pilihan Kategori Pasar Limbah', template=market_option_template),
                TextSendMessage(text="Ingin membuka pasar sendiri? Tinggal buka link ini http://location-linebot.herokuapp.com/store/add")
                ])

        else :
            # Interaction
            interaction_response = None
            with open('data/speech.json', 'r') as speechwords:
                speech = json.load(speechwords)

            for key, value in keyword['interaction'].items():
                for word in value:
                    if (word in msg.split()):
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
                if ('iya' not in msg.split() and 'tidak' not in msg.split()):
                    thumbnail_image = (
                        'https://location-linebot.herokuapp.com/static/img/feature_thumbnail/location.png',
                        'https://location-linebot.herokuapp.com/static/img/feature_thumbnail/weather.png',
                        'https://location-linebot.herokuapp.com/static/img/feature_thumbnail/3R.png',
                        'https://location-linebot.herokuapp.com/static/img/feature_thumbnail/coin.png',
                        'https://location-linebot.herokuapp.com/static/img/feature_thumbnail/gogreen.png',
                        'https://location-linebot.herokuapp.com/static/img/feature_thumbnail/www.png'
                    )
                    image_option_template = ImageCarouselTemplate(columns=[
                        ImageCarouselColumn(image_url=thumbnail_image[0],
                                            action=MessageTemplateAction(
                                                label='Cari Lokasi', text='Pandu, tolong cariin {place} deket sini'.format(
                                                    place=random.choice(['restoran', 'atm', 'tempat poton rambut', 'salon', 'halte bus', 'warung', 'bioskop'])
                                                ))),
                        ImageCarouselColumn(image_url=thumbnail_image[1],
                                            action=MessageTemplateAction(
                                                label='Cuaca Kini', text='Hari ini cuaca nya seperti apa Pan?')),
                        ImageCarouselColumn(image_url=thumbnail_image[2],
                                            action=MessageTemplateAction(
                                                label='Pasar Limbah', text='Pan, tolong buka Pasar Limbah')),
                        ImageCarouselColumn(image_url=thumbnail_image[3],
                                            action=MessageTemplateAction(
                                                label='Travel Point', text='Pandu, tolong cek deh travel point')),
                        ImageCarouselColumn(image_url=thumbnail_image[4],
                                            action=MessageTemplateAction(
                                                label='Go Green', text='Tips and tricks dong untuk jaga lingkungan kita!')),
                        ImageCarouselColumn(image_url=thumbnail_image[4],
                                            action=MessageTemplateAction(
                                                label='Buka Web', text='Pandu buka website Official dari Digibot Solution'))
                    ])

                    line_bot_api.reply_message(
                        event.reply_token,[
                        TextSendMessage(text="Pandu tidak mengenal kata-kata dalam percakapan, mungkin ada yang bisa Pandu bantu?"),
                        TemplateSendMessage(
                            alt_text='Guide Pandu Bot', template=image_option_template)
                        ])

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
