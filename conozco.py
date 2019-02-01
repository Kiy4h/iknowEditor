#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Conozco
# Copyright (C) 2008, 2012 Gabriel Eirea
# Copyright (C) 2011, 2012 Alan Aguiar
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact information:
# Gabriel Eirea geirea@gmail.com
# Alan Aguiar alanjas@hotmail.com
# Ceibal Jam http://ceibaljam.org

import os
import sys
import random
import pygame
import time
import imp
import gettext
import ConfigParser
from gettext import gettext as _
from gi.repository import Gtk

X_SIZE = 800.0
Y_SIZE = 900.0

# constantes
RADIO = 10
RADIO2 = RADIO**2
XMAPAMAX = 786
DXPANEL = 414
XCENTROPANEL = 1002
YGLOBITO = 100
DXBICHO = 255
DYBICHO = 412
XBICHO = 1200-DXBICHO
YBICHO = 900-DYBICHO-80
XPUERTA = 786
YPUERTA = 279
XBARRA_P = 840
YBARRA_P = 790
ABARRA_P = 40
YTEXTO = 370
XBARRA_A= XMAPAMAX+20
YBARRA_A = 900 - ABARRA_P - 20
ABARRA_A = DXPANEL-40
CAMINORECURSOS = "recursos"
CAMINOCOMUN = "comun"
CAMINOFUENTES = "fuentes"
CAMINODATOS = "datos"
CAMINOIMAGENES = "imagenes"
CAMINOSONIDOS = "sonidos"
ARCHIVONIVELES = "levels"
ARCHIVOEXPLORACIONES = "explorations"
COLORNOMBREDEPTO = (10,10,10)
COLORNOMBRECAPITAL = (10,10,10)
COLORNOMBRERIO = (10,10,10)
COLORNOMBRERUTA = (10,10,10)
COLORNOMBREELEVACION = (10,10,10)
COLORESTADISTICAS1 = (10, 10, 150)
COLORESTADISTICAS2 = (10, 10, 10)
COLORPREGUNTAS = (80,80,155)
COLORPANEL = (156,158,172)
COLORBARRA_P = (255, 0, 0)
COLORBARRA_A = (0, 0, 255)
TOTALAVANCE = 7
EVENTORESPUESTA = pygame.USEREVENT+1
TIEMPORESPUESTA = 2300
EVENTODESPEGUE = EVENTORESPUESTA+1
EVENTOREFRESCO = EVENTODESPEGUE+1
TIEMPOREFRESCO = 250
ESTADONORMAL = 1
ESTADOPESTANAS = 2
ESTADOFRENTE = 3
ESTADODESPEGUE = 4

# variables globales para adaptar la pantalla a distintas resoluciones
scale = 1
shift_x = 0
shift_y = 0
xo_resolution = True

clock = pygame.time.Clock()

def wait_events():
    """ Funcion para esperar por eventos de pygame sin consumir CPU """
    global clock
    clock.tick(20)
    return pygame.event.get()

class Punto():
    """Clase para objetos geograficos que se pueden definir como un punto.

    La posicion esta dada por un par de coordenadas (x,y) medida en pixels
    dentro del mapa.
    """

    def __init__(self,nombre,tipo,simbolo,posicion,postexto):
        global scale, shift_x, shift_y
        self.nombre = nombre
        self.tipo = int(tipo)
        self.posicion = (int(int(posicion[0])*scale+shift_x),
                        int(int(posicion[1])*scale+shift_y))
        self.postexto = (int(int(postexto[0])*scale)+self.posicion[0],
                        int(int(postexto[1])*scale)+self.posicion[1])
        self.simbolo = simbolo

    def estaAca(self,pos):
        """Devuelve un booleano indicando si esta en la coordenada pos,
        la precision viene dada por la constante global RADIO"""
        if (pos[0]-self.posicion[0])**2 + \
                (pos[1]-self.posicion[1])**2 < RADIO2:
            return True
        else:
            return False

    def dibujar(self,pantalla,flipAhora):
        """Dibuja un punto en su posicion"""
        pantalla.blit(self.simbolo, (self.posicion[0]-8, self.posicion[1]-8))
        if flipAhora:
            pygame.display.flip()

    def mostrarNombre(self,pantalla,fuente,color,flipAhora):
        """Escribe el nombre del punto en su posicion"""
        text = fuente.render(self.nombre, 1, color)
        textrect = text.get_rect()
        textrect.center = (self.postexto[0], self.postexto[1])
        pantalla.blit(text, textrect)
        if flipAhora:
            pygame.display.flip()


class Zona():
    """Clase para objetos geograficos que se pueden definir como una zona.

    La posicion esta dada por una imagen bitmap pintada con un color
    especifico, dado por la clave (valor 0 a 255 del componente rojo).
    """

    def __init__(self,mapa,nombre,claveColor,tipo,posicion,rotacion):
        self.mapa = mapa # esto hace una copia en memoria o no????
        self.nombre = nombre
        self.claveColor = int(claveColor)
        self.tipo = int(tipo)
        self.posicion = (int(int(posicion[0])*scale+shift_x),
                        int(int(posicion[1])*scale+shift_y))
        self.rotacion = int(rotacion)

    def estaAca(self,pos):
        """Devuelve True si la coordenada pos esta en la zona"""
        if pos[0] < XMAPAMAX*scale+shift_x:
            try:
                colorAca = self.mapa.get_at((int(pos[0]-shift_x),
                                            int(pos[1]-shift_y)))
            except: # probablemente click fuera de la imagen
                return False
            if colorAca[0] == self.claveColor:
                return True
            else:
                return False
        else:
            return False

    def mostrarNombre(self,pantalla,fuente,color,flipAhora):
        """Escribe el nombre de la zona en su posicion"""
        text = fuente.render(self.nombre, 1, color)
        textrot = pygame.transform.rotate(text, self.rotacion)
        textrect = textrot.get_rect()
        textrect.center = (self.posicion[0], self.posicion[1])
        pantalla.blit(textrot, textrect)
        if flipAhora:
            pygame.display.flip()


class Nivel():
    """Clase para definir los niveles del juego.

    Cada nivel tiene un dibujo inicial, los elementos pueden estar
    etiquetados con el nombre o no, y un conjunto de preguntas.
    """

    def __init__(self,nombre):
        self.nombre = nombre
        self.dibujoInicial = list()
        self.nombreInicial = list()
        self.preguntas = list()
        self.indicePreguntaActual = 0
        self.elementosActivos = list()

    def prepararPreguntas(self):
        """Este metodo sirve para preparar la lista de preguntas al azar."""
        random.shuffle(self.preguntas)

    def siguientePregunta(self,listaSufijos,listaPrefijos):
        """Prepara el texto de la pregunta siguiente"""
        self.preguntaActual = self.preguntas[self.indicePreguntaActual]
        self.sufijoActual = random.randint(1,len(listaSufijos))-1
        self.prefijoActual = random.randint(1,len(listaPrefijos))-1
        lineas = listaPrefijos[self.prefijoActual].split("\n")
        lineas.extend(self.preguntaActual[0].split("\n"))
        lineas.extend(listaSufijos[self.sufijoActual].split("\n"))
        self.indicePreguntaActual = self.indicePreguntaActual+1
        if self.indicePreguntaActual == len(self.preguntas):
            self.indicePreguntaActual = 0
        return lineas

    def devolverAyuda(self):
        """Devuelve la linea de ayuda"""
        self.preguntaActual = self.preguntas[self.indicePreguntaActual-1]
        return self.preguntaActual[3].split("\n")

class Conozco():
    """Clase principal del juego.

    """



    def loadCommons(self):
                
        self.listaPrefijos = list()
        self.listaSufijos = list()
        self.listaCorrecto = list()
        self.listaMal = list()
        self.listaDespedidasB = list()
        self.listaDespedidasM = list()
        self.listaPresentacion = list()
        self.listaCreditos = list()
        

        r_path = os.path.join(CAMINORECURSOS, CAMINOCOMUN, 'datos', 'commons.py')
        a_path = os.path.abspath(r_path)
        f = None
        try:
            f = imp.load_source('commons', a_path)
        except:
            print _('Cannot open %s') % 'commons'

        if f:
            if hasattr(f, 'ACTIVITY_NAME'):
                e = f.ACTIVITY_NAME
                self.activity_name = unicode(e, 'UTF-8')
            if hasattr(f, 'PREFIX'):
                for e in f.PREFIX:
                    e1 = unicode(e, 'UTF-8')
                    self.listaPrefijos.append(e1)
            if hasattr(f, 'SUFIX'):
                for e in f.SUFIX:
                    e1 = unicode(e, 'UTF-8')
                    self.listaSufijos.append(e1)  
            if hasattr(f, 'CORRECT'):
                for e in f.CORRECT:
                    e1 = unicode(e, 'UTF-8')
                    self.listaCorrecto.append(e1)
            if hasattr(f, 'WRONG'):
                for e in f.WRONG:
                    e1 = unicode(e, 'UTF-8')
                    self.listaMal.append(e1)
            if hasattr(f, 'BYE_C'):
                for e in f.BYE_C:
                    e1 = unicode(e, 'UTF-8')
                    self.listaDespedidasB.append(e1)
            if hasattr(f, 'BYE_W'):
                for e in f.BYE_W:
                    e1 = unicode(e, 'UTF-8')
                    self.listaDespedidasM.append(e1)
            if hasattr(f, 'PRESENTATION'):
                for e in f.PRESENTATION:
                    e1 = unicode(e, 'UTF-8')
                    self.listaPresentacion.append(e1)
            if hasattr(f, 'CREDITS'):
                for e in f.CREDITS:
                    e1 = unicode(e, 'UTF-8')
                    self.listaCreditos.append(e1)

        self.numeroSufijos = len(self.listaSufijos)
        self.numeroPrefijos = len(self.listaPrefijos)
        self.numeroCorrecto = len(self.listaCorrecto)
        self.numeroMal = len(self.listaMal)
        self.numeroDespedidasB = len(self.listaDespedidasB)
        self.numeroDespedidasM = len(self.listaDespedidasM)
 

    def cargarImagen(self,nombre):
        """Carga una imagen y la escala de acuerdo a la resolucion"""
        global scale, xo_resolution
        imagen = None
        archivo = os.path.join(self.camino_imagenes, nombre)
        if os.path.exists(archivo):
            if xo_resolution:
                imagen = pygame.image.load( \
                    os.path.join(self.camino_imagenes,nombre))
            else:
                imagen0 = pygame.image.load( \
                    os.path.join(self.camino_imagenes,nombre))
                imagen = pygame.transform.scale(imagen0,
                            (int(imagen0.get_width()*scale),
                            int(imagen0.get_height()*scale)))
                del imagen0
        return imagen

    def __init__(self, parent):
        self.parent = parent
        file_activity_info = ConfigParser.ConfigParser()
        activity_info_path = os.path.abspath('activity/activity.info')
        file_activity_info.read(activity_info_path)
        bundle_id = file_activity_info.get('Activity', 'bundle_id')
        self.activity_name = file_activity_info.get('Activity', 'name')
        path = os.path.abspath('locale')
        gettext.bindtextdomain(bundle_id, path)
        gettext.textdomain(bundle_id)
        global _
        _ = gettext.gettext


    def loadAll(self):
        global scale, shift_x, shift_y, xo_resolution
        pygame.init()
        pygame.display.init()
        self.pantalla = pygame.display.get_surface()
        if not(self.pantalla):
            info = pygame.display.Info()
            self.pantalla = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
            pygame.display.set_caption(_(self.activity_name))
        self.anchoPantalla = self.pantalla.get_width()
        self.altoPantalla = self.pantalla.get_height()

        pygame.display.flip()
        if self.anchoPantalla==X_SIZE and self.altoPantalla==Y_SIZE:
            xo_resolution = True
            scale = 1
            shift_x = 0
            shift_y = 0
        else:
            xo_resolution = False
            if self.anchoPantalla/X_SIZE<self.altoPantalla/Y_SIZE:
                scale = self.anchoPantalla/X_SIZE
                shift_x = 0
                shift_y = int((self.altoPantalla-scale*Y_SIZE)/2)
            else:
                scale = self.altoPantalla/Y_SIZE
                shift_x = int((self.anchoPantalla-scale*X_SIZE)/2)
                shift_y = 0
        # cargar imagenes generales
        self.camino_imagenes = os.path.join(CAMINORECURSOS,
                                            CAMINOCOMUN,
                                            CAMINOIMAGENES)
        self.fondo = None


        # Otros


        self.terron = self.cargarImagen("terron.png")
        self.simboloCapitalD = self.cargarImagen("capitalD.png")
        self.simboloCapitalN = self.cargarImagen("capitalN.png")
        self.simboloCiudad = self.cargarImagen("ciudad.png")
        self.simboloCerro = self.cargarImagen("cerro.png")


        # cargar fuentes
        self.fuente60 = pygame.font.Font(os.path.join(CAMINORECURSOS,\
                                                        CAMINOCOMUN,\
                                                        CAMINOFUENTES,\
                                                        "Share-Regular.ttf"),
                                        int(60*scale))
        self.fuente40 = pygame.font.Font(os.path.join(CAMINORECURSOS,\
                                                        CAMINOCOMUN,\
                                                        CAMINOFUENTES,\
                                                        "Share-Regular.ttf"),
                                        int(34*scale))
        self.fuente9 = pygame.font.Font(os.path.join(CAMINORECURSOS,\
                                                        CAMINOCOMUN,\
                                                        CAMINOFUENTES,\
                                                        "Share-Regular.ttf"),
                                        int(20*scale))
        self.fuente32 = pygame.font.Font(None, int(30*scale))
        self.fuente24 = pygame.font.Font(None, int(24*scale))
        # cursor
        datos_cursor = (
            "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX  ",
            "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX ",
            "XXX.........................XXXX",
            "XXX..........................XXX",
            "XXX..........................XXX",
            "XXX.........................XXXX",
            "XXX.......XXXXXXXXXXXXXXXXXXXXX ",
            "XXX........XXXXXXXXXXXXXXXXXXX  ",
            "XXX.........XXX                 ",
            "XXX..........XXX                ",
            "XXX...........XXX               ",
            "XXX....X.......XXX              ",
            "XXX....XX.......XXX             ",
            "XXX....XXX.......XXX            ",
            "XXX....XXXX.......XXX           ",
            "XXX....XXXXX.......XXX          ",
            "XXX....XXXXXX.......XXX         ",
            "XXX....XXX XXX.......XXX        ",
            "XXX....XXX  XXX.......XXX       ",
            "XXX....XXX   XXX.......XXX      ",
            "XXX....XXX    XXX.......XXX     ",
            "XXX....XXX     XXX.......XXX    ",
            "XXX....XXX      XXX.......XXX   ",
            "XXX....XXX       XXX.......XXX  ",
            "XXX....XXX        XXX.......XXX ",
            "XXX....XXX         XXX.......XXX",
            "XXX....XXX          XXX......XXX",
            "XXX....XXX           XXX.....XXX",
            "XXX....XXX            XXX...XXXX",
            " XXX..XXX              XXXXXXXX ",
            "  XXXXXX                XXXXXX  ",
            "   XXXX                  XXXX   ")
        self.cursor = pygame.cursors.compile(datos_cursor)
        pygame.mouse.set_cursor((32,32), (1,1), *self.cursor)
        datos_cursor_espera = (
            "                                ",
            "                                ",
            "                                ",
            "                                ",
            "                                ",
            "                                ",
            "                                ",
            "                                ",
            "                                ",
            "                                ",
            "  XXXXXX     XXXXXX     XXXXXX  ",
            " XXXXXXXX   XXXXXXXX   XXXXXXXX ",
            "XXXX..XXXX XXXX..XXXX XXXX..XXXX",
            "XXX....XXX XXX....XXX XXX....XXX",
            "XXX....XXX XXX....XXX XXX....XXX",
            "XXX....XXX XXX....XXX XXX....XXX",
            "XXXX..XXXX XXXX..XXXX XXXX..XXXX",
            " XXXXXXXX   XXXXXXXX   XXXXXXXX ",
            "  XXXXXX     XXXXXX      XXXXX  ",
            "                                ",
            "                                ",
            "                                ",
            "                                ",
            "                                ",
            "                                ",
            "                                ",
            "                                ",
            "                                ",
            "                                ",
            "                                ",
            "                                ",
            "                                ")
        self.cursor_espera = pygame.cursors.compile(datos_cursor_espera)

    def set_background(self, image):
        x = int(image.get_width() * scale)
        y = int(image.get_height() * scale)
        self.fondo = pygame.transform.scale(image, (x,y))
        self.pantalla.fill((0,0,0))
        self.pantalla.blit(self.fondo, (shift_x, shift_y))

    def showName(self, text, pos, font, color=(0,0,0)):
        t = font.render(text, 1, color)
        r = t.get_rect()
        r.center = (pos[0], pos[1])
        self.pantalla.blit(t, r)

    def update_points(self, l):
        self.pantalla.fill((0,0,0))
        self.pantalla.blit(self.fondo, (shift_x, shift_y))
        for p in l:
            name = p[0]
            x = p[1]
            y = p[2]
            dx = int(p[3] * scale)
            dy = int(p[4] * scale)
            pos_n = (x + dx, y + dy)
            pos_c = (x - 8, y - 8)
            self.showName(name, pos_n, self.fuente9)
            self.pantalla.blit(self.simboloCiudad, pos_c)

    def getScale(self):
        return scale

    def getShiftX(self):
        return shift_x

    def getShiftY(self):
        return shift_y

    def principal(self):
        """Este es el loop principal del juego"""
        global scale, shift_x, shift_y
        pygame.time.set_timer(EVENTOREFRESCO,TIEMPOREFRESCO)

        self.loadAll()

        self.loadCommons()

        pygame.mouse.set_cursor((32,32), (1,1), *self.cursor)

        while 1:

            while Gtk.events_pending():
                Gtk.main_iteration()

            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                    #self.pantalla.blit(self.simboloCiudad, pos)
                    self.parent._add_coor(pos)
                    #print pos



            pygame.display.flip()



