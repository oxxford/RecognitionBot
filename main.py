import io
import boto3
import requests
from PIL import Image, ImageDraw, ImageFont
from telegram.ext import CommandHandler
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext import Updater

token = '709661490:AAG6OK_phXyJ1E2_ALwK5HR0eylsTEjBd5A'
REQUEST_KWARGS = {}

s3 = boto3.resource('s3')
ssm = boto3.client('ssm')
rekognition = boto3.client('rekognition')
image_url = ''
MASK = Image.open("mask.png")


def start(bot, update):
    print('/start')
    bot.send_message(chat_id=update.message.chat_id, text="Hi! I'm Image recognition bot. To start, send me a photo")


def get_image():
    global image_url
    response = requests.get(image_url)
    image_bytes = response.content
    return image_bytes


def get_faces(image_bytes):
    response = rekognition.detect_faces(Image={'Bytes': image_bytes}, Attributes=['ALL'])
    if 'FaceDetails' in response:
        return response['FaceDetails']
    else:
        return []


def get_face_boxes(faces, source_size):
    # this list comprehension builds a bounding box around the faces
    return [
        (
            int(f['BoundingBox']['Left'] * source_size[0]),
            int(f['BoundingBox']['Top'] * source_size[1]),
            int((f['BoundingBox']['Left'] + f['BoundingBox']['Width']) * source_size[0]),
            int((f['BoundingBox']['Top'] + f['BoundingBox']['Height']) * source_size[1]),
            # we store the final coordinate of the bounding box as the pitch of the face
            f['Pose']['Roll']
        )
        for f in faces
    ]


def build_masked_image(source, mask, boxes):
    for box in boxes:
        size = (box[2] - box[0], box[3] - box[1])
        scaled_mask = mask.rotate(-box[4], expand=1).resize(size, Image.ANTIALIAS)
        # we cut off the final element of the box because it's the rotation
        source.paste(scaled_mask, box[:4], scaled_mask)


def get_masked_image(image_bytes, mask, bot, update):
    file_stream = io.BytesIO(image_bytes)
    image = Image.open(file_stream)
    boxes = get_face_boxes(get_faces(image_bytes), image.size)
    build_masked_image(image, mask, boxes)
    output = io.BytesIO()
    image.save(output, 'JPEG')
    output.seek(0)
    bot.send_photo(chat_id=update.message.chat_id, photo=output)
    file_stream.close()
    output.close()


def receive_photo(bot, update):
    global image_url
    file_id = update.message.photo[-1].file_id
    newFile = bot.getFile(file_id)
    bot.sendMessage(chat_id=update.message.chat_id,
                    text="Great, got your photo! Here's a list of things I can do to it:\n\n"
                         "/detect_emotions - is a guy on your photo sad? Or maybe you want to know "
                         "if a group of people are staring at you with anger?\n\n"
                         "/detect_age - I will magically guess your age... Or your frineds'...\n\n"
                         "/detect_beard - got any hairy dudes on your photo? Be sure that we will find that out :)\n\n"
                         "/celebrities - who the fuck is this guy???\n\n"
                         "/replace_faces - replace their faces with a mask")
    filePath = newFile.file_path
    truePath = filePath[filePath.find('photos'):]
    image_url = 'https://api.telegram.org/file/bot' + token + '/' + truePath


def check_photo_presence(bot, update):
    global image_url
    if image_url == '':
        bot.send_message(chat_id=update.message.chat_id,
                         text="I cannot analyze void :(\nSend me a photo to analyze, please")


def replace_faces(bot, update):
    print('replace_faces')
    check_photo_presence(bot, update)
    image_bytes = get_image()
    get_masked_image(image_bytes, MASK, bot, update)


def draw_rectangles(image_bytes, faces, bot, update):
    object = s3.Object('cc-bot', 'myimage.jpg')
    object.put(Body=image_bytes)
    file_stream = io.BytesIO()
    object.download_fileobj(file_stream)
    image = Image.open(file_stream)
    width, height = image.size
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("Verdana.ttf", size=30)
    for i in range(len(faces)):
        box = faces[i]['BoundingBox']
        left = width * box['Left']
        top = height * box['Top']
        draw.rectangle([left, top, left + (width * box['Width']), top + (height * box['Height'])], width=5)
        draw.rectangle([left - 20, top - 20, left + 10, top + 10], fill=(42, 50, 59))
        draw.text((left - 15, top - 25), str(i + 1), fill=(255, 255, 255), font=font)
    output = io.BytesIO()
    image.save(output, 'JPEG')
    output.seek(0)
    bot.send_photo(chat_id=update.message.chat_id, photo=output)
    object.delete()
    file_stream.close()
    output.close()


def detect_emotions(bot, update):
    print('detect_emotions')
    check_photo_presence(bot, update)
    image_bytes = get_image()
    faces = get_faces(image_bytes)
    if len(faces) > 1:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="There are multiple people in this photo! I will analyze them one-by-one:")
        draw_rectangles(image_bytes, faces, bot, update)
        for i in range(0, len(faces)):
            message = "Person number " + str(i + 1) + "\n"
            emotions = faces[i]['Emotions']
            for em in emotions:
                conf = em['Confidence']
                type = em['Type']
                em_out = ("%.2f" % conf) + '% probability that person in this photo is ' + type + '\n'
                message += em_out
            bot.sendMessage(chat_id=update.message.chat_id, text=message)
    else:
        message = 'There is\n'
        emotions = faces[0]['Emotions']
        for em in emotions:
            conf = em['Confidence']
            type = em['Type']
            em_out = ("%.2f" % conf) + '% probability that person in this photo is ' + type + '\n'
            message += em_out
        bot.sendMessage(chat_id=update.message.chat_id, text=message)


def detect_age(bot, update):
    print('detect_age')
    check_photo_presence(bot, update)
    image_bytes = get_image()
    faces = get_faces(image_bytes)
    if len(faces) > 1:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="There are multiple people in this photo! I will analyze them one-by-one:")
        draw_rectangles(image_bytes, faces, bot, update)
        for i in range(0, len(faces)):
            message = "Person number " + str(i + 1) + " is approximately "
            age = faces[i]['AgeRange']
            high = age['High']
            low = age['Low']
            message += str(low) + " to " + str(high) + " years old"
            bot.sendMessage(chat_id=update.message.chat_id, text=message)
    else:
        age = faces[0]['AgeRange']
        high = age['High']
        low = age['Low']
        message = "Person in this photo is approximately " + str(low) + " to " + str(high) + " years old"
        bot.sendMessage(chat_id=update.message.chat_id, text=message)


def detect_beard(bot, update):
    print('detect_beard')
    check_photo_presence(bot, update)
    image_bytes = get_image()
    faces = get_faces(image_bytes)
    if len(faces) > 1:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="There are multiple people in this photo! I will analyze them one-by-one:")
        draw_rectangles(image_bytes, faces, bot, update)
        for i in range(0, len(faces)):
            message = "Person number " + str(i + 1) + " "
            beard = faces[i]['Beard']
            conf = beard['Confidence']
            has_beard = beard['Value']
            if has_beard:
                beard_out = "has a beard with " + ("%.2f" % conf) + '% probability. \n'
            else:
                beard_out = "doesn't have a beard with " + ("%.2f" % conf) + '% probability. \n'
            message += beard_out
            bot.sendMessage(chat_id=update.message.chat_id, text=message)
    else:
        message = 'This person '
        beard = faces[0]['Beard']
        conf = beard['Confidence']
        has_beard = beard['Value']
        if has_beard:
            beard_out = "has a beard with " + ("%.2f" % conf) + '% probability. \n'
        else:
            beard_out = "doesn't have a beard with " + ("%.2f" % conf) + '% probability. \n'
        message += beard_out
        bot.sendMessage(chat_id=update.message.chat_id, text=message)


def detect_celebrities(bot, update):
    print('detect_celebrities')
    check_photo_presence(bot, update)
    image_bytes = get_image()
    rekognition_response = rekognition.recognize_celebrities(Image={'Bytes': image_bytes})
    celebrities = rekognition_response['CelebrityFaces']
    if len(celebrities) > 0:
        for celebrity in celebrities:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="Hello, " + celebrity['Name'])
    else:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="You are not a celebrity, sorry((")


updater = Updater(token=token)
dispatcher = updater.dispatcher

start_handler = CommandHandler('start', start)
receive_photo_handler = MessageHandler(Filters.photo, receive_photo)
detect_emotions_handler = CommandHandler('detect_emotions', detect_emotions)
detect_age_handler = CommandHandler('detect_age', detect_age)
detect_celebrities_handler = CommandHandler('celebrities', detect_celebrities)
detect_beard_handler = CommandHandler('detect_beard', detect_beard)
replace_faces_handler = CommandHandler('replace_faces', replace_faces)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(receive_photo_handler)
dispatcher.add_handler(detect_emotions_handler)
dispatcher.add_handler(detect_age_handler)
dispatcher.add_handler(detect_celebrities_handler)
dispatcher.add_handler(detect_beard_handler)
dispatcher.add_handler(replace_faces_handler)

updater.start_polling()
