import math
import random
from math import acos
from typing import List, Any

import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import pygame

WIDTH = 512
HEIGHT = 512


class Vektor3:
    x: float
    y: float
    z: float

    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z

    def copy(self):
        return Vektor3(self.x, self.y, self.z)


class Izvor:
    pos: Vektor3
    boja = Vektor3
    size: float

    def __init__(self, vrh, boja, size, tip='tocka'):
        self.pos = vrh
        self.boja = boja
        self.size = size
        self.tip = tip

    def get_spawning_point(self) -> Vektor3:
        if self.tip == 'tocka':
            return self.pos
        if self.tip == 'poligon':
            return Vektor3(random.randint(-20, 20), 30, random.randint(-20, 20))


class Cestica:
    pos: Vektor3
    v: float
    t: int
    smjer: Vektor3
    os: Vektor3
    kut: float
    size: float

    def __init__(self, direction, v, t, izvor: Izvor):
        self.izvor = izvor
        self.pos = izvor.get_spawning_point().copy()
        self.boja = izvor.boja.copy()
        self.v = v
        self.t = t
        self.smjer = direction
        self.os = Vektor3(0, 0, 0)
        self.kut = 0
        self.size = izvor.size

    def nacrtaj_cesticu(self):
        glColor3f(self.boja.x, self.boja.y, self.boja.z)
        glTranslatef(self.pos.x, self.pos.y, self.pos.z)
        glRotatef(self.kut, self.os.x, self.os.y, self.os.z)

        glBegin(GL_QUADS)
        glTexCoord2d(0.0, 0.0)
        glVertex3f(-self.size, -self.size, 0.0)
        glTexCoord2d(1.0, 0.0)
        glVertex3f(self.size, -self.size, 0.0)
        glTexCoord2d(1.0, 1.0)
        glVertex3f(self.size, self.size, 0.0)
        glTexCoord2d(0.0, 1.0)
        glVertex3f(-self.size, self.size, 0.0)
        glEnd()

        glRotatef(-self.kut, self.os.x, self.os.y, self.os.z)
        glTranslatef(-self.pos.x, -self.pos.y, -self.pos.z)

    def promijeni_poziciju_cestice(self):
        self.pos.x += self.v * self.smjer.x
        self.pos.y += self.v * self.smjer.y
        self.pos.z += self.v * self.smjer.z

    def promijeni_boju_i_velicinu(self):
        if self.izvor.tip == 'poligon':
            if self.boja.y > 0.5:
                self.boja.y -= 0.003
            if self.boja.x > 0.5:
                self.boja.x -= 0.003
            self.size += 0.05
        if self.izvor.tip == 'tocka':
            if self.boja.y < 1:
                self.boja.y += 0.015
            self.size += 0.03

    def postavi_os(self, os):
        self.os.x = os.x
        self.os.y = os.y
        self.os.z = os.z

    def postavi_kut(self, kut):
        self.kut = kut / (2 * math.pi) * 360


class Krivulja:
    def __init__(self, path):
        self.starting_points = []
        self.points = []
        self.vectors = []
        self.draw_points = []
        self.calculated_draw = False
        self.direction = 1
        self.current_point = 0
        self.load_data(path)
        for i in range(len(self.starting_points) - 3):
            self.calculate_points(*self.starting_points[i:i + 4])

    def load_data(self, path):
        with open(path, 'r') as file:
            for line in file.readlines():
                line = line.rstrip().split(" ")
                self.starting_points.append(Vektor3(float(line[0]), float(line[1]), float(line[2])))

    def get_next_point(self):
        self.current_point += self.direction
        return self.points[self.current_point % len(self.points)]

    def calculate_points(self, point_0, point_1, point_2, point_3):
        t = 0
        Bi3 = 1 / 6 * np.matrix([[-1, 3, -3, 1],
                                 [3, -6, 3, 0],
                                 [-3, 0, 3, 0],
                                 [1, 4, 1, 0]])
        Rx = np.matrix([[point_0.x],
                        [point_1.x],
                        [point_2.x],
                        [point_3.x]])
        Ry = np.matrix([[point_0.y],
                        [point_1.y],
                        [point_2.y],
                        [point_3.y]])
        Rz = np.matrix([[point_0.z],
                        [point_1.z],
                        [point_2.z],
                        [point_3.z]])
        multiply_point_x = np.matmul(Bi3, Rx)
        multiply_point_y = np.matmul(Bi3, Ry)
        multiply_point_z = np.matmul(Bi3, Rz)
        while t < 1:
            T3 = np.matrix([t ** 3, t ** 2, t, 1])
            T2 = np.matrix([3 * t ** 2, 2 * t, 1, 0])
            self.points.append(Vektor3(float(np.matmul(T3, multiply_point_x)), float(np.matmul(T3, multiply_point_y)),
                                       float(np.matmul(T3, multiply_point_z))))
            self.draw_points.append(
                Vektor3(float(np.matmul(T3, multiply_point_x)), float(np.matmul(T3, multiply_point_y)),
                        float(np.matmul(T3, multiply_point_z))))
            self.vectors.append(Vektor3(float(np.matmul(T2, multiply_point_x)), float(np.matmul(T2, multiply_point_y)),
                                        float(np.matmul(T2, multiply_point_z))))
            t += 0.02


class SustavCestica:
    def __init__(self, program, izvor, ociste, krivulja=None):
        self.program = program
        self.current_time = 0
        self.past_time = 0
        self.krivulja = krivulja
        self.izvor = izvor
        self.cestice: List[Cestica] = []
        self.ociste = ociste
        self.iteration = 0

    def update(self):
        self.current_time = glutGet(GLUT_ELAPSED_TIME)
        if self.current_time - self.past_time > 20:
            self.iteration += 1
            self.pomakni_izvor()
            self.stvori_cestice()
            self.osvjezi_cestice()
            self.past_time = self.current_time
        self.program.my_display()

    def pomakni_izvor(self):
        if self.krivulja:
            self.izvor.pos = self.krivulja.get_next_point()

    def stvori_cestice(self):
        n = random.randint(1, min((self.iteration // 50) + 1, 50))
        for j in range(n):
            y = random.uniform(-1, 1)
            if self.krivulja is not None:
                x = random.uniform(-1, 1)
                z = random.uniform(-1, 1)
            else:
                x = 0
                z = 0
            norm = (x ** 2 + y ** 2 + z ** 2) ** 0.5
            x /= norm
            y /= norm
            z /= norm
            self.cestice.append(Cestica(Vektor3(x, y, z), 0.5, random.randint(75, 85), self.izvor))

    def osvjezi_cestice(self):
        for cestica in self.cestice:
            os, kut = self.izracunaj_podatke_o_cestici(cestica)
            cestica.postavi_kut(kut)
            cestica.postavi_os(os)
            cestica.promijeni_poziciju_cestice()
            cestica.t -= 1
            cestica.promijeni_boju_i_velicinu()
            self.zavrsi_zivot_cestice(cestica)

    def izracunaj_podatke_o_cestici(self, cestica):
        s = Vektor3(0, 0, 1)
        e = Vektor3(cestica.pos.x - self.ociste.x, cestica.pos.y - self.ociste.y, cestica.pos.z - self.ociste.z)
        os = Vektor3(s.y * e.z - e.y * s.z, e.x * s.z - s.x * e.z, s.x * e.y - s.y * e.x)
        s_norm = (s.x ** 2 + s.y ** 2 + s.z ** 2) ** 0.5
        e_norm = (e.x ** 2 + e.y ** 2 + e.z ** 2) ** 0.5
        se = s.x * e.x + s.y * e.y + s.z * e.z
        kut = acos(se / (s_norm * e_norm))
        return os, kut

    def zavrsi_zivot_cestice(self, cestica):
        if cestica.t <= 0:
            self.cestice.remove(cestica)

    def nacrtaj_cestice(self):
        for cestica in self.cestice:
            cestica.nacrtaj_cesticu()


def load_texture(filename):
    surface = pygame.image.load(filename)
    data = pygame.image.tostring(surface, "RGB")
    texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
    gluBuild2DMipmaps(GL_TEXTURE_2D, 3, surface.get_width(), surface.get_height(), GL_RGB, GL_UNSIGNED_BYTE, data)
    return texture


class Program:
    izvor: Izvor
    sustav_cestica: SustavCestica
    window: Any
    texture: Any

    def __init__(self):
        self.krivulja = True
        self.ociste = Vektor3(0, 0, 50)
        if self.krivulja:
            self.izvor = Izvor(Vektor3(0, 0, 0), Vektor3(1, 0, 0), 0.8, tip='tocka')
            self.sustav_cestica = SustavCestica(self, self.izvor, self.ociste, Krivulja('krivulja.txt'))
        else:
            self.izvor = Izvor(Vektor3(0, 0, 0), Vektor3(1, 1, 1), 0.8, tip='poligon')
            self.sustav_cestica = SustavCestica(self, self.izvor, self.ociste)

    def my_display(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(self.ociste.x, self.ociste.y, -self.ociste.z)
        self.sustav_cestica.nacrtaj_cestice()
        glutSwapBuffers()

    def my_reshape(self, w, h):
        global WIDTH, HEIGHT
        WIDTH = w
        HEIGHT = h
        glViewport(0, 0, WIDTH, HEIGHT)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, WIDTH / HEIGHT, 0.1, 150)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glLoadIdentity()
        glClearColor(0, 0, 0, 0)
        glClear(GL_COLOR_BUFFER_BIT)
        glPointSize(1)
        glColor3f(0, 0, 0)

    def my_keyboard(self, the_key, *args):
        if the_key == b'q':
            self.izvor.pos.x -= 0.5
        if the_key == b'w':
            self.izvor.pos.x += 0.5
        if the_key == b'a':
            self.izvor.pos.y -= 0.5
        if the_key == b's':
            self.izvor.pos.y += 0.5
        if the_key == b'y':
            self.izvor.pos.z -= 0.5
        if the_key == b'x':
            self.izvor.pos.z += 0.5
        if the_key == b'e':
            self.ociste.x -= 0.5
        if the_key == b'r':
            self.ociste.x += 0.5
        if the_key == b'd':
            self.ociste.y -= 0.5
        if the_key == b'f':
            self.ociste.y += 0.5
        self.my_display()

    def main(self):
        glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
        glutInitWindowSize(WIDTH, HEIGHT)
        glutInitWindowPosition(10, 10)
        glutInit()
        self.window = glutCreateWindow("Sustav Cestica")
        glutReshapeFunc(self.my_reshape)
        glutDisplayFunc(self.my_display)
        glutKeyboardFunc(self.my_keyboard)
        glutIdleFunc(self.sustav_cestica.update)
        if self.krivulja:
            self.texture = load_texture("cestica.bmp")
        else:
            self.texture = load_texture("snow.bmp")
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glEnable(GL_BLEND)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture)

        glutMainLoop()


if __name__ == '__main__':
    p = Program()
    p.main()
