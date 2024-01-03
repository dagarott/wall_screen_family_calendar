import sqlite3
from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QApplication, QListWidgetItem, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextCharFormat, QColor
from PyQt5.QtCore import QDate
from PyQt5.uic import loadUi
import sys
import signal
import time
import random
import datetime
from datetime import datetime
# from luma.led_matrix.device import max7219
# from luma.core.interface.serial import spi, noop
# from luma.core.render import canvas
# from luma.core.virtual import viewport
# from luma.core.legacy import text, show_message, textsize
# from luma.core.legacy.font import proportional ,CP437_FONT, ATARI_FONT, TINY_FONT, SINCLAIR_FONT, LCD_FONT, ATARI_FONT
# documentation: https://www.eclipse.org/paho/clients/python/docs/
import paho.mqtt.client as mqtt


# create matrix device
# serial = spi(port=0, device=1, gpio=noop())
# device = max7219(serial, cascaded= 8, block_orientation=-90)
# print("Created device")

broker = "maqiatto.com"
port = 8883
topic = "dagarott@gmail.com/frame"
# Generate a Client ID with the publish prefix.
client_id = f'publish-{random.randint(0, 1000)}'
username = "dagarott@gmail.com"
password = "Dau8queL"
client_id = f'python-mqtt-{random.randint(0, 1000)}'


class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()
        loadUi("main.ui", self)
        # self.calendarDateChanged()
        # self.saveButton.clicked.connect(self.saveChanges)
        # self.addButton.clicked.connect(self.addNewTask)
        # mqtt client
        self.client = mqtt.Client(client_id, transport="websockets")
        self.client.username_pw_set(username, password)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.mqtt_connected = False
        print(f'Connecting now to {broker}:{port}')
        self.client.connect(broker, port)
        self.client.loop_start()
        self.client.subscribe(topic)
        self.update_calendar_status()
        self.update_events_listview()

    def calendarDateChanged(self):
        print("The calendar date was changed.")
        dateSelected = self.calendarWidget.selectedDate().toPyDate()
        print("Date selected:", dateSelected)
        # self.updateTaskList(dateSelected)
        # self.msg = "MAX7219 LED Matrix Demo"
        # print(self.msg)
        # show_message(device, self.msg, fill="white", font=proportional(CP437_FONT))

    def update_events_listview(self):

        # Obtener la fecha actual
        currentMonth = datetime.now().month
        currentYear = datetime.now().year
        fecha_actual = datetime.now().strftime("%Y-%m")
        print(currentMonth)
        print(currentYear)
        print(fecha_actual)
        # Obtener eventos del mes actual de la base de datos
        conn = sqlite3.connect("eventos.db")
        c = conn.cursor()
        # c.execute("SELECT tipo, fecha, hora, descripcion FROM eventos WHERE strftime('%m', fecha) = ? AND strftime('%Y', fecha) = ?", (currentMonth, currentYear))
        c.execute(
            f"SELECT tipo, fecha, hora, descripcion FROM eventos WHERE fecha LIKE '{fecha_actual}%'")
        eventos = c.fetchall()
        conn.close()
        # Agregar los eventos al QListWidget
        for evento in eventos:
            self.EventList.addItem(
                evento[0] + ',' + evento[2] + ',' + evento[3])
            print(evento[0] + ',' + evento[2] + ',' + evento[3])

    def update_calendar_status(self):
        conn = sqlite3.connect("eventos.db")
        c = conn.cursor()
        c.execute(
            "CREATE TABLE IF NOT EXISTS eventos (tipo TYPE,fecha DATE, hora TIME, descripcion TEXT);")
        # Reemplazar 'tabla' con la tabla correcta de la base de datos
        c.execute("SELECT fecha FROM eventos")
        fechas = c.fetchall()
        conn.close()

        for fecha in fechas:
            # Convertir la tupla de fecha a una cadena
            fecha_str = fecha[0]
            # Convertir la cadena de fecha a un objeto de tipo QDate
            fecha_qdate = QDate.fromString(fecha_str, "yyyy-MM-dd")
            # Obtener los campos de año, mes y día
            year = int(fecha_qdate.year())
            month = int(fecha_qdate.month())
            day = int(fecha_qdate.day())
            self.colour_event_day(year, month, day)

    def colour_event_day(self, year, month, day):
        # day = QDate(date.year, date.month, date.day)
        format = QTextCharFormat()
        format.setBackground(QColor(255, 0, 0))
        self.calendarWidget.setDateTextFormat(QDate(year, month, day), format)

    def save_events(self, msg_eventtype, msg_date, msg_time, msg_description):
        self.eventype = msg_eventtype
        self.fecha = msg_date
        self.hora = msg_time
        self.descripcion = msg_description

        # Guardar evento en la base de datos
        conn = sqlite3.connect("eventos.db")
        c = conn.cursor()
        c.execute(
            "CREATE TABLE IF NOT EXISTS eventos (tipo TYPE,fecha DATE, hora TIME, descripcion TEXT);")
        # Lee los datos existentes en la base de datos para poder verificar si los nuevos datos ya existen.
        c.execute("SELECT COUNT(*) FROM eventos WHERE tipo = ? AND fecha = ? AND hora = ? AND descripcion = ?", (self.eventype, self.fecha,
                  self.hora, self.descripcion))
        count = c.fetchone()[0]  # Obtiene el resultado de la consulta

        if count == 0:
            c.execute("INSERT INTO eventos VALUES (?, ?, ?, ?);",
                      (self.eventype, self.fecha, self.hora, self.descripcion))
            conn.commit()
            conn.close()
            print("Evento guardado exitosamente.")
        else:
            print("Evento ya existia en db")

    def shown_on_display_coming_event(self):
        # Obtener la fecha de mañana
        mañana = datetime.date.today() + datetime.timedelta(days=1)
        print(mañana)

        # Obtener eventos programados para mañana desde la base de datos
        conn = sqlite3.connect("eventos.db")
        c = conn.cursor()
        c.execute(
            "SELECT tipo, fecha, hora, descripcion FROM eventos WHERE fecha = ?;", (mañana,))
        eventos = c.fetchall()
        conn.close()

        if eventos:
            texto_eventos = "\n".join(
                [f"{evento[0]} {evento[1]} {evento[2]} {evento[3]}" for evento in eventos])
            print(texto_eventos)
        else:
            print("No hay eventos programados para mañana.")

    def on_connect(self, client, userdata, flags, rc):
        print("Connected With Result Code " + str(rc))
        self.mqtt_connected = True

    def on_disconnect(self, *args):
        print("Disconnected from broker")
        self.mqtt_connected = False
        # stop loop
        self.client.loop_stop()

    def on_subscribe(self, mqttsub, obj, mid, granted_qos):
        print("Subscribed: " + str(mid) + " " + str(granted_qos))

    def on_message(self, client, userdata, message):
        # print("message received " ,str(message.payload.decode("utf-8")))
        self.msg_data = str(message.payload.decode("utf-8")).split(",")
        print("event type:", self.msg_data[0])
        print("date:", self.msg_data[1])
        print("time:", self.msg_data[2])
        print("description:", self.msg_data[3])
        self.save_events(
            self.msg_data[0], self.msg_data[1], self.msg_data[2], self.msg_data[3])
        self.update_events_listview()
        self.update_calendar_status()

    ################################################################
    # The callback for when the broker responds to our connection request.
    # def on_connect(self, client, userdata, flags, rc):
    #     self.window.write("Connected to server with with flags: %s, result code: %s" % (flags, rc))

    #     if rc == 0:
    #         print("Connection succeeded.")

    #     elif rc > 0:
    #         if rc < len(mqtt_rc_codes):
    #             print("Connection failed with error: %s", mqtt_rc_codes[rc])
    #         else:
    #             print("Connection failed with unknown error %d", rc)

    #     # Subscribing in on_connect() means that if we lose the connection and reconnect then subscriptions will be renewed.
    #     client.subscribe(self.subscription)
    #     self.window.show_status("Connected.")
    #     self.window.set_connected_state(True)
    #     return

    # # The callback for when the broker responds with error messages.
    # def on_log(client, userdata, level, buf):
    #     print("on_log level %s: %s", level, userdata)
    #     return

    # def on_disconnect(self, client, userdata, rc):
    #     print("disconnected")
    #     self.window.write("Disconnected from server.")
    #     self.window.show_status("Disconnected.")
    #     self.window.set_connected_state(False)

    # # The callback for when a message has been received on a topic to which this
    # # client is subscribed.  The message variable is a MQTTMessage that describes
    # # all of the message parameters.

    # # Some useful MQTTMessage fields: topic, payload, qos, retain, mid, properties.
    # #   The payload is a binary string (bytes).
    # #   qos is an integer quality of service indicator (0,1, or 2)
    # #   mid is an integer message ID.


if __name__ == "__main__":
    app = QApplication(sys.argv)

    conn = sqlite3.connect("eventos.db")
    conn.close()

    window = Window()
    window.showFullScreen()
    # window.showMaximized()
    # window.resize(1280, 820)
    window.show()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    sys.exit(app.exec())
