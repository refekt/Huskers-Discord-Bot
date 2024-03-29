from __future__ import annotations

import logging
import math
import os
from typing import Any

import cv2
import numpy
from PIL import Image
from PIL.Image import Image as ImgImg
from numpy import random

from objects.Logger import discordLogger, is_debugging

logger = discordLogger(
    name=__name__,
    level=logging.DEBUG if is_debugging() else logging.INFO,
)

__all__: list[str] = ["fry_image"]

face_cascade = cv2.CascadeClassifier(
    os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
)
eye_cascade = cv2.CascadeClassifier(
    os.path.join(cv2.data.haarcascades, "haarcascade_eye.xml")
)

deepfry_path = "resources/deepfry/"


# Pass an image to fry, pretty self-explanatory
def fry_image(image: ImgImg, emote_amount: int, noise: float, contrast: int) -> ImgImg:
    logger.debug(
        f"Frying an image with {emote_amount} emotes, {noise} noise, and {contrast} contrast."
    )
    gray = numpy.array(image.convert("L"))  # noqa

    eye_coords = find_eyes(gray)
    char_coords = find_chars(gray)

    add_flares(image, eye_coords)
    add_emotes(image, emote_amount)
    add_chars(image, char_coords)
    image = add_noise(image, random.random() * noise)
    image = change_contrast(image, math.ceil(random.random()) * contrast)

    [w, h] = [image.width - 1, image.height - 1]
    w *= numpy.random.random(1)
    h *= numpy.random.random(1)
    r = int(((image.width + image.height) / 14) * (numpy.random.random(1)[0] + 1))

    bulge_bool = random.choice([True, False])

    if bulge_bool:
        image = bulge(
            img=image, f=numpy.array([int(w), int(h)]), r=r, a=3, h=6, ior=2.25
        )

    logger.debug("Frying completed")
    return image


def find_chars(gray) -> list[tuple[Any, Any, Any, Any]]:
    logger.debug("Looking for characters")

    ret, mask = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
    image_final = cv2.bitwise_and(gray, gray, mask=mask)
    ret, new_img = cv2.threshold(image_final, 180, 255, cv2.THRESH_BINARY_INV)
    kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    dilated = cv2.dilate(new_img, kernel, iterations=1)
    contours, hierarchy = cv2.findContours(
        dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
    )

    coords = []
    for contour in contours:
        [x, y, w, h] = cv2.boundingRect(contour)
        if w > 70 and h > 70:
            continue
        coords.append((x, y, w, h))

    logger.debug(f"Characters, if found, are here: {coords}")
    return coords


def find_eyes(gray) -> list[tuple[float | Any, float | Any]]:
    logger.debug("Looking for eyes")

    coords = []

    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    for x, y, w, h in faces:
        roi_gray = gray[y : y + h, x : x + w]
        eyes = eye_cascade.detectMultiScale(roi_gray)
        for ex, ey, ew, eh in eyes:
            coords.append((x + ex + ew / 2, y + ey + eh / 2))
    if len(coords) == 0:
        pass

    logger.debug(f"Eyes, if found, are here: {coords}")
    return coords


def add_flares(image: ImgImg, coords: list[tuple[float | Any, float | Any]]) -> ImgImg:
    logger.debug(f"Adding flares at: {coords}")

    flare = Image.open(random_file(f"{deepfry_path}flares/")).convert("RGBA")
    for coord in coords:
        image.paste(
            flare,
            (int(coord[0] - flare.size[0] / 2), int(coord[1] - flare.size[1] / 2)),
            flare,
        )

    logger.debug("Flares added")
    return image


def add_chars(image: ImgImg, coords: list[tuple[Any, Any, Any, Any]]) -> ImgImg:
    logger.debug(f"Adding characters at {coords}")

    char = Image.open(random_file(f"{deepfry_path}chars/")).convert("RGBA")
    for coord in coords:
        if numpy.random.random(1)[0] > 0.1:
            continue
        resized = char.copy()
        try:
            resized.thumbnail((coord[2], coord[3]), Image.ANTIALIAS)
        except AttributeError:
            resized.thumbnail((coord[2], coord[3]), Image.LANCZOS)
        image.paste(resized, (int(coord[0]), int(coord[1])), resized)

    logger.debug("Characters added")
    return image


def add_emotes(image, max_emotes) -> None:
    logger.debug(f"Adding {max_emotes} emotes")

    for i in range(max_emotes):
        emote = Image.open(random_file(f"{deepfry_path}/emotes/")).convert("RGBA")
        coord = numpy.random.random(2) * numpy.array([image.width, image.height])
        size = int((image.width / 10) * (numpy.random.random(1)[0] + 1))
        try:
            emote.thumbnail((size, size), Image.ANTIALIAS)
        except AttributeError:
            emote.thumbnail((size, size), Image.LANCZOS)
        image.paste(emote, (int(coord[0]), int(coord[1])), emote)

    logger.debug("Emotes added")
    return


def change_contrast(image: ImgImg, level: int) -> ImgImg:
    logger.debug(f"Changing contracts to {level} level")

    factor = (259 * (level + 255)) / (255 * (259 - level))

    def contrast(c) -> float:
        return 128 + factor * (c - 128)

    logger.debug("Contrast changed")
    return image.point(contrast)


def add_noise(image: ImgImg, factor) -> ImgImg:
    logger.debug(f"Adding {factor} noise")

    def noise(c) -> float:
        return c * (1 + numpy.random.random(1)[0] * factor - factor / 2)

    logger.debug("Noise added")
    return image.point(noise)


# creates a bulge like distortion to the image
# parameters:
#   img = PIL image
#   f   = numpy.array([x, y]) coordinates of the centre of the bulge
#   r   = radius of the bulge
#   a   = flatness of the bulge, 1 = spherical, > 1 increases flatness
#   h   = height of the bulge
#   ior = index of refraction of the bulge material
def bulge(img: ImgImg, f: numpy.ndarray, r: int, a: int, h: int, ior: float) -> ImgImg:
    logger.debug(f"Creating a buldge at {f[0]}, {f[1]} with a {r} radius. ior = {ior}")
    # print("Creating a bulge at ({0}, {1}) with radius {2}... ".format(f[0], f[1], r))

    # load image to numpy array
    width = img.width
    height = img.height
    img_data = numpy.array(img)  # noqa

    # ignore too large images
    if width * height > 3000 * 3000:
        return img

    # determine range of pixels to be checked (square enclosing bulge), max exclusive
    x_min = int(f[0] - r)
    if x_min < 0:
        x_min = 0
    x_max = int(f[0] + r)
    if x_max > width:
        x_max = width
    y_min = int(f[1] - r)
    if y_min < 0:
        y_min = 0
    y_max = int(f[1] + r)
    if y_max > height:
        y_max = height

    # make sure that bounds are int and not numpy array
    if isinstance(x_min, type(numpy.array([]))):
        x_min = x_min[0]
    if isinstance(x_max, type(numpy.array([]))):
        x_max = x_max[0]
    if isinstance(y_min, type(numpy.array([]))):
        y_min = y_min[0]
    if isinstance(y_max, type(numpy.array([]))):
        y_max = y_max[0]

    f_new = f
    bulge_square = numpy.copy(img_data)  # img_data[x_min:x_max, y_min:y_max]

    # following is equivalent to s = length(ray - f)
    bulge_y, bulge_x = numpy.mgrid[0 : bulge_square.shape[0], 0 : bulge_square.shape[1]]
    bulge_x = bulge_x - f_new[0]
    bulge_y = bulge_y - f_new[1]
    bulge_s = numpy.hypot(bulge_x, bulge_y)
    circle = (0 < bulge_s) & (bulge_s < r)

    # following is equivalent to m = -s / (a * math.sqrt(r ** 2 - s ** 2))
    bulge_m = numpy.copy(bulge_s)
    bulge_m[circle] = (-1 * bulge_m[circle]) / (
        a * numpy.sqrt(r**2 - bulge_m[circle] ** 2)
    )

    # following is equivalent to theta = numpy.pi / 2 + numpy.arctan(1 / m)
    bulge_theta = numpy.copy(bulge_s)
    bulge_theta[circle] = (numpy.pi / 2) + numpy.arctan(1 / bulge_m[circle])

    # following is equivalent to phi = numpy.abs(numpy.arctan(1 / m) - numpy.arcsin(numpy.sin(theta) / ior))
    bulge_phi = numpy.copy(bulge_s)
    bulge_phi[circle] = numpy.abs(
        numpy.arctan(1 / bulge_m[circle])
        - numpy.arcsin(numpy.sin(bulge_theta[circle]) / ior)
    )

    # following is equivalent to k = (h + (math.sqrt(r ** 2 - s ** 2) / a)) / numpy.sin(phi)
    bulge_k = numpy.copy(bulge_s)
    bulge_k[circle] = (h + (numpy.sqrt(r**2 - bulge_s[circle] ** 2) / a)) / numpy.sin(
        bulge_phi[circle]
    )

    bulge_norm_y, bulge_norm_x = numpy.mgrid[
        0 : bulge_square.shape[0], 0 : bulge_square.shape[1]
    ].astype(numpy.float32)
    bulge_norm_x = f_new[1] - bulge_norm_x
    bulge_norm_y = f_new[0] - bulge_norm_y
    bulge_norm_x[circle] = bulge_norm_x[circle] / bulge_s[circle]
    bulge_norm_y[circle] = bulge_norm_y[circle] / bulge_s[circle]

    # following is equivalent to intersect = ray + (normalise(f - ray)) * k
    bulge_intersect_y, bulge_intersect_x = numpy.mgrid[
        0 : bulge_square.shape[0], 0 : bulge_square.shape[1]
    ].astype(numpy.float32)
    bulge_intersect_x[circle] = (
        bulge_intersect_x[circle] + (bulge_norm_x[circle]) * bulge_k[circle]
    )
    bulge_intersect_y[circle] = (
        bulge_intersect_y[circle] + (bulge_norm_y[circle]) * bulge_k[circle]
    )

    # if 0 < intersect[0] < width - 1 and 0 < intersect[1] < height - 1:
    # bulged[y][x] = img_data[int(intersect[1])][int(intersect[0])]
    # else:
    # bulged[y][x] = [0, 0, 0, 0]
    orig_image_square = numpy.copy(img_data)
    intersect_area = (
        (0 < bulge_intersect_x) & (bulge_intersect_x < orig_image_square.shape[1])
    ) & ((0 < bulge_intersect_y) & (bulge_intersect_y < orig_image_square.shape[0]))
    # bulge_square[(numpy.logical_not(intersect_area)&circle)] = [0,0,0,0]
    bulge_square = replace_values(
        numpy.copy(orig_image_square),
        numpy.copy(bulge_square),
        circle,
        intersect_area,
        bulge_intersect_x,
        bulge_intersect_y,
    )
    bulge_square[numpy.logical_not(circle)] = orig_image_square[
        numpy.logical_not(circle)
    ]

    bulged = numpy.copy(img_data)
    bulged = bulge_square

    img = Image.fromarray(bulged)
    logger.debug("Bulge created")
    return img


def replace_values(
    orig_image_square: numpy.ndarray,
    bulge_square: numpy.ndarray,
    circle: numpy.ndarray,
    intersect_area: numpy.ndarray,
    bulge_intersect_x: numpy.ndarray,
    bulge_intersect_y: numpy.ndarray,
) -> numpy.ndarray:
    indices = numpy.transpose(numpy.nonzero(intersect_area & circle))

    img_ix = (
        # bulge_intersect_y[[*indices.T]].astype(int),
        # bulge_intersect_x[[*indices.T]].astype(int),
        bulge_intersect_y[tuple(indices.T)].astype(int),
        bulge_intersect_x[tuple(indices.T)].astype(int),
    )
    orig_img_ix = numpy.transpose(img_ix)

    # bulge_square[[*indices.T]] = orig_image_square[[*orig_img_ix.T]]
    bulge_square[tuple(indices.T)] = orig_image_square[tuple(orig_img_ix.T)]

    return bulge_square


def random_file(path: str) -> str:
    return path + numpy.random.choice(os.listdir(path))


logger.info(f"{str(__name__).title()} module loaded!")
