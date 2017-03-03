from django.shortcuts import render
from django.conf import settings

import os
import random
import math
import shutil
import string

from PIL import Image
import PIL.ImageOps
import PIL.ImageFilter


ORIG_IMG_DIR = 'img'
DISTORT_IMG_DIR = 'img_dist'

ORIG_IMG_DIR_ABS = os.path.join(settings.MEDIA_ROOT, ORIG_IMG_DIR)
DISTORT_IMG_DIR_ABS = os.path.join(settings.MEDIA_ROOT, DISTORT_IMG_DIR)

distortions = {}

def distortion(distortion_func):
  '''
  Registratind decorator for distortion function
  TODO: wrap to DRY repeats
  '''
  distortions[distortion_func.__name__] = distortion_func
  return distortion_func


def randomword(length):
    '''
    Random letter sequence for preventing images caching
    '''
    return ''.join(random.choice(string.ascii_lowercase) for i in range(length))

@distortion
def blur(img):
    '''
    blurs the image
    '''

    new_filename = '{}_{}'.format('blur', img)
    new_filepath = os.path.join(DISTORT_IMG_DIR_ABS, new_filename)

    image = Image.open(os.path.join(ORIG_IMG_DIR_ABS, img))
    blurred_image = image.filter(PIL.ImageFilter.GaussianBlur(radius=2) )
    blurred_image.save(new_filepath)

    return new_filename

@distortion
def negative(img):
    '''
    inverts image colors
    '''

    new_filename = '{}_{}'.format('negative', img)
    new_filepath = os.path.join(DISTORT_IMG_DIR_ABS, new_filename)

    image = Image.open(os.path.join(ORIG_IMG_DIR_ABS, img))
    inverted_image = PIL.ImageOps.invert(image)
    inverted_image.save(new_filepath)

    return new_filename


def get_pics(secret, session):

    '''
    creates pictures set for a preset secret
    1) chooses random original pics
    2) creates distorted if they don't exist already
    3) populates session folder with pairs according to the secret 

    TODO: clean-up and struct
    '''

    if not os.path.isdir(DISTORT_IMG_DIR_ABS):
        os.mkdir(DISTORT_IMG_DIR_ABS)

    if not session.session_key: # making sure sessuin has a key
        session.save()

    secret_bin = "{0:b}".format(secret).zfill(settings.NUMBER_OF_PICS)
    original_images = [random.choice(os.listdir(ORIG_IMG_DIR_ABS)) for i in range(settings.NUMBER_OF_PICS)]

    images = []

    for img in original_images:
        random_distortion_name = random.choice(list(distortions.keys()))
        img_distorted = '{}_{}'.format(random_distortion_name, img)
        img_distorted_path = os.path.join(DISTORT_IMG_DIR_ABS, img_distorted)

        if not os.path.isfile(img_distorted_path):
            img_distorted = distortions[random_distortion_name](img)

        images.append((os.path.join(ORIG_IMG_DIR, img), os.path.join(DISTORT_IMG_DIR, img_distorted)))

    session_dir = os.path.join(settings.MEDIA_ROOT, session.session_key)

    try:
        shutil.rmtree(session_dir)
    except Exception: # TODO: 
        pass

    os.mkdir(session_dir)

    pairs = []
    for i, (char, img) in enumerate(zip(secret_bin, images)):
        if char == '1':
            src = os.path.join(settings.MEDIA_ROOT, img[1])
            first_img_filename = '{}_1_{}.jpg'.format(i, randomword(10))
            dst = os.path.join(session_dir, first_img_filename)
            shutil.copyfile(src, dst)

            second_img_filename = '{}_2._{}jpg'.format(i, randomword(10))
            src = os.path.join(settings.MEDIA_ROOT, img[0])
            dst = os.path.join(session_dir, second_img_filename)
            shutil.copyfile(src, dst)

        else:
            src = os.path.join(settings.MEDIA_ROOT, img[0])
            first_img_filename = '{}_1_{}.jpg'.format(i, randomword(10))
            dst = os.path.join(session_dir, first_img_filename)
            shutil.copyfile(src, dst)

            src = os.path.join(settings.MEDIA_ROOT, img[1])
            second_img_filename = '{}_2_{}.jpg'.format(i, randomword(10))
            dst = os.path.join(session_dir, second_img_filename)
            shutil.copyfile(src, dst)

        pairs.append((os.path.join(session.session_key, first_img_filename), os.path.join(session.session_key, second_img_filename)))

    return pairs


def index(request):

    '''
    Main controller
    '''

    new = False
    success = 0
    guess = ''

    if request.method == "POST":
        new = request.POST.get("new", False)
        if not new:
            guess = request.POST.get("guess", False)

    secret = request.session.get('secret', None)
    pics = request.session.get('pics', None)

    if not secret or not pics or new:
        random.seed()
        secret = request.session['secret'] = random.randint(0, math.pow(2, settings.NUMBER_OF_PICS)-1)
        pics = get_pics(secret, request.session)
        request.session['pics'] = pics

    elif secret and guess:
        if "{0:b}".format(secret).zfill(settings.NUMBER_OF_PICS) == guess:
            success = 1
        else:
            success = -1

    secret_bin = "{0:b}".format(secret).zfill(settings.NUMBER_OF_PICS)

    data = {'secret': secret_bin, 
            'pics': pics,
            'success': success}

    return render(request, 'pictcha_app/index.html', data)
