# coding=utf-8
# Author: Andreas Christian Mueller <t3kcit@gmail.com>
#
# (c) 2012
# Modified by: Paul Nechifor <paul@nechifor.net>
#
# License: MIT

import numpy as np


def query_integral_image(integral_image, size_x, size_y):
    """Query the integral image for the sum of a rectangle.

    Parameters
    ----------
    integral_image : nd-array, shape (height, width)
        Integral image.
    size_x : int
        Width of the rectangle.
    size_y : int
        Height of the rectangle.

    Returns
    -------
    sum : int
        Sum of the rectangle.
    """
    # Get the dimensions of the integral image
    height, width = integral_image.shape
    
    # Calculate the coordinates for the rectangle
    # The rectangle goes from (0, 0) to (size_x, size_y)
    x1, y1 = 0, 0
    x2, y2 = min(size_x, width), min(size_y, height)
    
    # Calculate the sum using the integral image
    # The sum of rectangle (x1,y1) to (x2,y2) is:
    # integral[y2,x2] - integral[y1,x2] - integral[y2,x1] + integral[y1,x1]
    if x1 == 0 and y1 == 0:
        return integral_image[y2-1, x2-1]
    elif x1 == 0:
        return integral_image[y2-1, x2-1] - integral_image[y1-1, x2-1]
    elif y1 == 0:
        return integral_image[y2-1, x2-1] - integral_image[y2-1, x1-1]
    else:
        return (integral_image[y2-1, x2-1] - 
                integral_image[y1-1, x2-1] - 
                integral_image[y2-1, x1-1] + 
                integral_image[y1-1, x1-1])
