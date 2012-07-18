# -*- coding: utf-8 -*-
"""
Created on Mon Jul 16 22:58:11 2012

@author: Laurent
"""
import sys
import numpy as np
import pygame
from pygame.locals import *
from OpenGL.GL import *
import math
from navier_strokes_orig import NavierStrokesOrig
from navier_strokes import NavierStrokes

class LazyNavier(object):
    def __init__(self, main, size=5, dt=.1, diff=0., visc=0., force=5.,
                 source=100.):
        self.size = size + 2
        self.dt = dt
        self.diff = diff
        self.visc = visc
        self.force = force
        self.source = source
        
        self.me = main(self.size)
        
    def velocity_step(self, dt=None):
        if dt is None:
            dt = self.dt
            
        self.me.velocity_step(self.me.u, self.me.v,
                              self.me.u_prev, self.me.v_prev,
                              self.visc, dt)
                              
    def density_step(self, dt=None):
        if dt is None:
            dt = self.dt
                              
        self.me.density_step(self.me.density, self.me.density_prev,
                             self.me.u, self.me.v, self.diff, dt)

class MatrixDensity(object):
    def __init__(self, matrix, x, y, width, height):
        self._matrix = matrix
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        
        self._case_width = width / float(matrix.shape[0])
        self._case_height = height / float(matrix.shape[1])
    
    def render(self):
        w = self._case_width
        h = self._case_height
        
        it = np.nditer(self._matrix, flags=['multi_index'])
        while not it.finished:
            value, (X, Y) = it[0], it.multi_index
            x = self._x + X * w
            y = self._y + Y * h

            glBegin(GL_QUADS)
            glColor3f(value, value, value)
            glVertex2f(x, y)
            glColor3f(value, value, value)
            glVertex2f(x + w, y)
            glColor3f(value, value, value)
            glVertex2f(x + w, y + h)
            glColor3f(value, value, value)
            glVertex2f(x, y + h)
            glEnd()
            
            it.iternext()
            
    def click_at(self, x, y):
        X = int(math.floor((x - self._x) / self._case_width))
        Y = (-1
             + self._matrix.shape[1]
             - int(math.floor((y - self._y) / self._case_height)))
        
        self._matrix[X, Y] = 0.5
            
class MatrixVectors(object):
    def __init__(self, u, v, x, y, width, height):
        self._u = u
        self._v = v
        self._x = x
        self._y= y
        self._width = width
        self._height = height
        
        self._case_width = width / float(u.shape[0])
        self._case_height = height / float(v.shape[1])
    
    def render(self):
        w = self._case_width
        h = self._case_height
        
        it = np.nditer(self._u, flags=['multi_index'])
        
        glColor3f (1.0, 0.0, 0.0);
        glLineWidth(1.0);

        glBegin(GL_LINES)
        while not it.finished:
            value_u, (X, Y) = it[0], it.multi_index
            value_v = self._v[X, Y]
            
            x = self._x + (X + 0.5) * w
            y = self._y + (Y + 0.5) * h
            
            glVertex2f(x, y)
            glVertex2f(x + value_u * w, y + value_v * h)
            
            it.iternext()
        glEnd()
        
    def move_at(self, x, y, rel_x, rel_y):    
        X = int(math.floor((x - self._x) / self._case_width))
        Y = (-1
             + self._u.shape[1]
             - int(math.floor((y - self._y) / self._case_height)))

        REL_X = rel_x / self._case_width
        REL_Y = rel_y / self._case_height
        
        self._u[X, Y] = REL_X
        self._v[X, Y] = -REL_Y

        self._u[X+1, Y] = REL_X / 2.0
        self._v[X+1, Y] = -REL_Y / 2.0
        self._u[X-1, Y] = REL_X / 2.0
        self._v[X-1, Y] = -REL_Y / 2.0
        self._u[X, Y+1] = REL_X / 2.0
        self._v[X, Y+1] = -REL_Y / 2.0        
        self._u[X, Y-1] = REL_X / 2.0
        self._v[X, Y-1] = -REL_Y / 2.0
    
            
def init():
    pygame.init()
    pygame.display.set_mode((640, 480), OPENGL|DOUBLEBUF)
    
    glClearColor(1.0, 1.0, 1.0, 0.0)
    glColor3f(0.0, 0.0, 0.0)
    glPointSize(4.0)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho (0, 640, 0, 480, -1, 1)
    
def update(delta, mdensity, mvectors):
    event = pygame.event.poll ()
    
    mdensity._matrix *= 0
    mvectors._u *= 0
    mvectors._v *= 0
    
    if event.type is QUIT:
      sys.exit(0)
    elif event.type is KEYDOWN:
      if event.key is K_ESCAPE:
        sys.exit(0)
    elif event.type is MOUSEMOTION	:
        right = event.buttons[2]
        left = event.buttons[0]
        if right:
            lazy = list(event.pos) + list(event.rel)
            mvectors.move_at(*lazy)
        elif left:
            mdensity.click_at(*event.pos)
        
def draw(rendered):
    glClear(GL_COLOR_BUFFER_BIT)
    for r in rendered:
        r.render()
    glFlush()
    pygame.display.flip()


def main(args):
    init()
    
    size = 10
    nats = LazyNavier(NavierStrokes, size=size)
    #nats = LazyNavier(NavierStrokesOrig, size=size)
    
    mdensity = MatrixDensity(nats.me.density_prev, 0, 0, 640, 480)
    mvectors = MatrixVectors(nats.me.u_prev, nats.me.v_prev, 0, 0, 640, 480)
    
    rendered = [mdensity, mvectors]
    
    clock = pygame.time.Clock()
    clock.tick()
    
    while True:
        delta = clock.get_time() / 1000.0
        update(delta, mdensity, mvectors)
        
        nats.velocity_step(delta)
        nats.density_step(delta)

        draw(rendered)
        clock.tick()

if __name__ == "__main__":
    main(sys.argv[1:])
