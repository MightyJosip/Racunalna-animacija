import math

import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

WIDTH = 900
HEIGHT = 900


class Point:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.h = 1.0
        self.listeners = []
        self.transformation_matrix = np.matrix([[1, 0, 0, 0],
                                                [0, 1, 0, 0],
                                                [0, 0, 1, 0],
                                                [0, 0, 0, 1]])

    def __repr__(self):
        return f"({self.x}, {self.y}, {self.z}),"

    def get_my_matrix(self):
        return np.matrix([self.x, self.y, self.z, self.h])

    def set_position(self):
        matrix = np.matmul(self.get_my_matrix(), self.transformation_matrix)
        self.x = matrix[0, 0]
        self.y = matrix[0, 1]
        self.z = matrix[0, 2]
        self.notify_listeners()

    def translate(self, x, y, z):
        matrix = np.matrix([[1, 0, 0, 0],
                            [0, 1, 0, 0],
                            [0, 0, 1, 0],
                            [x, y, z, 1]])
        self.transformation_matrix = np.matmul(self.transformation_matrix, matrix)

    def scale(self, x, y, z):
        matrix = np.matrix([[x, 0, 0, 0],
                            [0, y, 0, 0],
                            [0, 0, z, 0],
                            [0, 0, 0, 1]])
        self.transformation_matrix = np.matmul(self.transformation_matrix, matrix)

    def notify_listeners(self):
        for listener in self.listeners:
            listener.refresh()


class Polygon:
    def __init__(self, p1, p2, p3):
        self.p1 = p1
        self.p1.listeners.append(self)
        self.p2 = p2
        self.p2.listeners.append(self)
        self.p3 = p3
        self.p3.listeners.append(self)
        self.a = self.calculate_a()
        self.b = self.calculate_b()
        self.c = self.calculate_c()
        self.d = self.calculate_d()

    def __repr__(self):
        return f"Polygon: ({self.p1}, {self.p2}, {self.p3}); Coef: ({self.a}, {self.b}, {self.c}, {self.d})"

    def calculate_a(self):
        return (self.p2.y - self.p1.y) * (self.p3.z - self.p1.z) - (self.p2.z - self.p1.z) * (self.p3.y - self.p1.y)

    def calculate_b(self):
        return -(self.p2.x - self.p1.x) * (self.p3.z - self.p1.z) + (self.p2.z - self.p1.z) * (self.p3.x - self.p1.x)

    def calculate_c(self):
        return (self.p2.x - self.p1.x) * (self.p3.y - self.p1.y) - (self.p2.y - self.p1.y) * (self.p3.x - self.p1.x)

    def calculate_d(self):
        return -self.a * self.p1.x - self.b * self.p1.y - self.c * self.p1.z

    def refresh(self):
        self.a = self.calculate_a()
        self.b = self.calculate_b()
        self.c = self.calculate_c()
        self.d = self.calculate_d()


class Body:
    def __init__(self, path):
        self.real_vertices = []
        self.vertices = []
        self.polygons = []
        self.load_data(path)
        self.center = Point(0, 0, 0)
        for vertex in self.real_vertices:
            vertex.scale(5, 5, 5)
            vertex.set_position()

    def __repr__(self):
        nl = '\n'
        return f"Vertices:\n{self.vertices}\nPolygons:\n{nl.join(str(p) for p in self.polygons)}"

    def load_data(self, path):
        with open(path, 'r') as file:
            for line in file.readlines():
                line = line.rstrip().split(" ")
                if line[0] == 'v':
                    self.real_vertices.append(Point(float(line[1]), float(line[2]), float(line[3])))
                    self.vertices.append(Point(float(line[1]), float(line[2]), float(line[3])))
                if line[0] == 'f':
                    self.polygons.append(Polygon(self.vertices[int(line[1]) - 1], self.vertices[int(line[2]) - 1],
                                                 self.vertices[int(line[3]) - 1]))


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
                self.starting_points.append(Point(float(line[0]), float(line[1]), float(line[2])))

    def get_next_point(self):
        self.current_point += self.direction
        try:
            return self.points[self.current_point - 1]
        except:
            self.direction *= -1
            return self.points[self.current_point - 2]

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
            self.points.append(Point(float(np.matmul(T3, multiply_point_x)), float(np.matmul(T3, multiply_point_y)),
                                     float(np.matmul(T3, multiply_point_z))))
            self.draw_points.append(
                Point(float(np.matmul(T3, multiply_point_x)), float(np.matmul(T3, multiply_point_y)),
                      float(np.matmul(T3, multiply_point_z))))
            self.vectors.append(Point(float(np.matmul(T2, multiply_point_x)), float(np.matmul(T2, multiply_point_y)),
                                      float(np.matmul(T2, multiply_point_z))))
            t += 0.02


def draw_polygon(poly):
    glBegin(GL_LINE_LOOP)
    glVertex3f((75 + poly.p1.x) * 5, (25 + poly.p1.y) * 5, 0)
    glVertex3f((75 + poly.p2.x) * 5, (25 + poly.p2.y) * 5, 0)
    glVertex3f((75 + poly.p3.x) * 5, (25 + poly.p3.y) * 5, 0)
    glEnd()


def draw_points(points):
    glBegin(GL_POINTS)
    for point in points:
        glVertex2f((75 + point.x) * 5, (25 + point.y) * 5)
    glEnd()


class Program:
    def __init__(self):
        self.body = None
        self.window = None
        self.krivulja = None
        self.ociste = Point(100, 100, 100)
        self.glediste = Point(-200, -200, -200)
        self.H = math.sqrt((self.ociste.x - self.glediste.x) ** 2 + (self.ociste.y - self.glediste.y) ** 2 + (
                    self.ociste.z - self.glediste.z) ** 2)
        self.T = self.get_view_transform_matrix()
        self.P = self.get_perspective_projection_matrix()
        self.projection_matrix = np.matmul(self.T, self.P)

    def get_view_transform_matrix(self):
        t1 = np.matrix([[1, 0, 0, 0],
                        [0, 1, 0, 0],
                        [0, 0, 1, 0],
                        [-self.ociste.x, -self.ociste.y, -self.ociste.z, 1]])
        g1 = np.matmul(self.glediste.get_my_matrix(), t1)
        cosa = g1[0, 0] / math.sqrt(g1[0, 0] ** 2 + g1[0, 1] ** 2)
        sina = g1[0, 1] / math.sqrt(g1[0, 0] ** 2 + g1[0, 1] ** 2)
        t2 = np.matrix([[cosa, -sina, 0, 0],
                        [sina, cosa, 0, 0],
                        [0, 0, 1, 0],
                        [0, 0, 0, 1]])
        g2 = np.matmul(g1, t2)
        sinb = g2[0, 0] / math.sqrt(g2[0, 0] ** 2 + g2[0, 2] ** 2)
        cosb = g2[0, 2] / math.sqrt(g2[0, 0] ** 2 + g2[0, 2] ** 2)
        t3 = np.matrix([[cosb, 0, sinb, 0],
                        [0, 1, 0, 0],
                        [-sinb, 0, cosb, 0],
                        [0, 0, 0, 1]])
        t4 = np.matrix([[0, -1, 0, 0],
                        [1, 0, 0, 0],
                        [0, 0, 1, 0],
                        [0, 0, 0, 1]])
        t5 = np.matrix([[-1, 0, 0, 0],
                        [0, 1, 0, 0],
                        [0, 0, 1, 0],
                        [0, 0, 0, 1]])
        t = np.matmul(t1, t2)
        t = np.matmul(t, t3)
        t = np.matmul(t, t4)
        t = np.matmul(t, t5)
        return t

    def get_perspective_projection_matrix(self):
        return np.matrix([[1, 0, 0, 0],
                          [0, 1, 0, 0],
                          [0, 0, 0, 1 / self.H],
                          [0, 0, 0, 0]])

    def my_reshape(self, w, h):
        glViewport(0, 0, WIDTH, HEIGHT)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, WIDTH, 0, HEIGHT)
        glClearColor(1.0, 1.0, 1.0, 0.0)
        glClear(GL_COLOR_BUFFER_BIT)
        glPointSize(1.0)
        glColor3f(0.0, 0.0, 0.0)

    def calculate_points(self):
        if not self.krivulja.calculated_draw:
            print("CALCULATING")
            for index, point in enumerate(self.krivulja.points):
                Ap = np.matmul(point.get_my_matrix(), self.projection_matrix)
                if Ap[0, 3] != 0:
                    self.krivulja.draw_points[index].x = Ap[0, 0] / Ap[0, 3]
                    self.krivulja.draw_points[index].y = Ap[0, 1] / Ap[0, 3]
                    self.krivulja.draw_points[index].z = Ap[0, 2] / Ap[0, 3]
                else:
                    self.krivulja.draw_points[index].x = 0
                    self.krivulja.draw_points[index].y = 0
                    self.krivulja.draw_points[index].z = 0
            self.krivulja.calculated_draw = True

    def calculate_points2(self):
        for index, point1 in enumerate(self.body.real_vertices):
            point = Point(point1.x + self.body.center.x, point1.y + self.body.center.y, point1.z + self.body.center.z)
            Ap = np.matmul(point.get_my_matrix(), self.projection_matrix)
            if Ap[0, 3] != 0:
                self.body.vertices[index].x = Ap[0, 0] / Ap[0, 3]
                self.body.vertices[index].y = Ap[0, 1] / Ap[0, 3]
                self.body.vertices[index].z = Ap[0, 2] / Ap[0, 3]
            else:
                self.body.vertices[index].x = 0
                self.body.vertices[index].y = 0
                self.body.vertices[index].z = 0

    def my_keyboard(self, the_key, mouse_x, mouse_y):
        if the_key == b'a':
            self.body.center = self.krivulja.get_next_point()
        self.my_display()

    def my_display(self):
        glClear(GL_COLOR_BUFFER_BIT)
        self.calculate_points2()
        for polygon in self.body.polygons:
            draw_polygon(polygon)
        self.calculate_points()
        draw_points(self.krivulja.draw_points)
        glFlush()

    def main(self):
        self.body = Body('aircraft747.obj')
        self.krivulja = Krivulja('krivulja.txt')
        glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
        glutInitWindowSize(WIDTH, HEIGHT)
        glutInitWindowPosition(10, 10)
        glutInit()
        self.window = glutCreateWindow("OpenGL Objekt")
        glutReshapeFunc(self.my_reshape)
        glutDisplayFunc(self.my_display)
        glutKeyboardFunc(self.my_keyboard)
        glutMainLoop()


if __name__ == '__main__':
    p = Program()
    p.main()
