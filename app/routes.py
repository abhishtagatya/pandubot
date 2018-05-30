from flask import Flask, request, abort, url_for

from app import app, db
from app.models import Users
from app.config import LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET_TOKEN

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
    """  """
    confirm_template = ConfirmTemplate(text='Untuk mengoptimalkan penggunaan aplikasi, apakah anda berkenan untuk registrasi secara otomatis?', actions=[
        PostbackTemplateAction(label='Yes', text='Yes', data='create_user=confirm'),
        PostbackTemplateAction(label='No', text='No', data='create_user=decline'),
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
                    # Logs
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="Membuat registrasi data untuk user {}".format(user_profile.display_name)))

                    db.session.add(new_user)

                    line_bot_api.reply_message(
                        event.reply_token, [
                            TextSendMessage(
                                text='Berhasil! Tinggal satu langkah lagi'
                            ),
                            TextSendMessage(
                                text='Untuk mengetahui lingkungan Anda, dapatkah Anda membagikan lokasi Anda?'
                            )
                        ]
                    )

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
                TextSendMessage(text="Sepertinya ada masalah dalam PostbackEvent Anda"))


    elif event.postback.data == 'datetime_postback':
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=event.postback.params['datetime']))
    elif event.postback.data == 'date_postback':
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=event.postback.params['date']))
    else :
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=event.postback.data))

@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    #current_location = {}
    #current_location['location'] = event.message.address
    #current_location['latitude'] = event.message.latitude
    #current_location['longitude'] = event.message.longitude

    findUser = Users.query.filter_by(id=event.source.user_id).first()

    if findUser != None:
        try:
            findUser.location = (event.message.address)[20]
            findUser.latitude = event.message.latitude
            findUser.longitude = event.message.longitude

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="Lokasi Anda sudah diperbarui!"))

            db.session.commit()
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
    findUser = Users.query.filter_by(id=event.source.user_id).first()

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=findUser.location))

@handler.default()
def default(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="Jenis obrolan tidak didukung oleh ..."))
