import sqlite3
from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QApplication, QListWidgetItem, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextCharFormat, QColor
from PyQt5.QtCore import QDate
from PyQt5.QtCore import QTimer, QTime
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from PyQt5.uic import loadUi
import sys
import signal
import time
import requests
import json
import random
import datetime
from datetime import datetime
# from luma.led_matrix.device import max7219
# from luma.core.interface.serial import spi, noop
# from luma.core.render import canvas
# from luma.core.virtual import viewport
# from luma.core.legacy import text, show_message, textsize
# from luma.core.legacy.font import proportional, CP437_FONT, ATARI_FONT, TINY_FONT, SINCLAIR_FONT, LCD_FONT, ATARI_FONT
# documentation: https://www.eclipse.org/paho/clients/python/docs/
import paho.mqtt.client as mqtt

# Replace with your OpenWeatherMap API key
API_KEY = "23b1e28665e2cc447d07a3a268c6cede"

# create matrix device
# serial = spi(port=0, device=1, gpio=noop())
# device = max7219(serial, cascaded=8, block_orientation=-90)
# print("Created device")

broker = "maqiatto.com"
port = 8883
topic = "dagarott@gmail.com/frame"
# Generate a Client ID with the publish prefix.
client_id = f'publish-{random.randint(0, 1000)}'
username = "dagarott@gmail.com"
password = "Dau8queL"
client_id = f'python-mqtt-{random.randint(0, 1000)}'


class SerialPort(QSerialPort):
    def __init__(self, port_name, baud_rate=QSerialPort.Baud115200):
        super().__init__()
        self.setPortName(port_name)
        self.setBaudRate(baud_rate)
        self.open(QSerialPort.ReadWrite)

    def write_data(self, data):
        self.writeData(data.encode())

    def read_data(self):
        if self.canReadLine():
            return self.readLine().data().decode().strip()
        return None


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

        # Crear el QTimer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_systick)

        # Iniciar el QTimer con un intervalo de 1000 ms (1 segundo)
        self.timer.start(1000)
        # Iniciar el contador systick
        self.systick = 0

        self.serial_port = None

        self.find_serial_ports()

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
        self.EventList.clear()
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
        format.setBackground(QColor(100, 127, 100))
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
        tomorrow = QDate.currentDate().addDays(1)
        tomorrow_str = tomorrow.toString(Qt.ISODate)
        # Obtener eventos programados para mañana desde la base de datos
        conn = sqlite3.connect("eventos.db")
        c = conn.cursor()
        query = f"SELECT * FROM eventos WHERE fecha = '{tomorrow_str}'"
        c.execute(query)
        # Recorrer el resultado de la consulta y mostrar los eventos
        self.temp = c.fetchall()
        self.length = len(self.temp)
        print(self.length)
        print(self.temp)
        if len(self.temp):
            self.data = "!!!MANYANA,"
            # for event in c.fetchall():
            for idx in range(self.length):
                self.data += self.temp[idx][0] + ' ' + self.temp[idx][3] + ' ' + self.temp[idx][2] + ' | '
            print(self.data)
            self.send_data(self.data)

        conn.close()

    def show_next_month(self):
        self.calendarWidget.showNextMonth()

    def show_previous_month(self):
        self.calendarWidget.showPreviousMonth()

    def fetch_weather(self):
        city = "Alboraya"
        if not city:
            return

        url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric&lang=es"
        response = requests.get(url)

        if response.status_code == 200:
            weather_data = response.json()
            self.display_weather(weather_data)
        else:
            print("Error fetching weather data. Please check the city name.")

    def display_weather(self, weather_data):
        if "list" not in weather_data:
            print("No weather data available.")
            return
        self.today_weather_data = weather_data['list'][00]
        self.date = self.today_weather_data["dt_txt"].split()[0]
        self.current_temperature = self.today_weather_data['main']['temp']
        self.humidity = self.today_weather_data['main']['humidity']
        self.tempmin = self.today_weather_data['main']['temp_min']
        self.tempmax = self.today_weather_data['main']['temp_max']
        self.descripcion = self.today_weather_data['main']['description']
        print(f"{weather_data['city']['name']}" + ',' + f"{self.date}" + ',' +
              f"Temperatura:{self.current_temperature}ºC" + ',' +
              f"Humedad:{self.humidity}%" + ',' +
              f"Temp_min:{self.tempmin}ºC" + ','+f"Temp_max:{self.tempmax}ºC")
        self.data = weather_data['city']['name'] + ',' + "Temp:" + str(self.current_temperature) + "ºC" + ',' + "Hum:" + str(
            self.humidity) + "%" + ',' + "TempMin:" + str(self.tempmin) + ',' + "TempMax:" + str(self.tempmax) + ',' + self.descripcion
        self.send_data(self.data)

    def update_systick(self):
        # Incrementar el contador systick
        self.systick += 1
        print(self.systick)
        # Perform task 1 every 5 min
        # if self.systick  % 300 == 0:
        if self.systick % 10 == 0:
            # Se obtiene la hora actual
            self.current_time = QTime.currentTime()
        # Se verifica si está dentro del intervalo de tiempo deseado
            if self.current_time >= QTime(9, 0) and self.current_time <= QTime(22, 0):
                self.shown_on_display_coming_event()
         # Perform task 1 every 30 minutos
        if self.systick % 1800 == 0:
            self.fetch_weather()

    # All related Mqtt functions

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

    def find_serial_ports(self):
        ports = QSerialPortInfo.availablePorts()
        for port in ports:
            self.serial_port = SerialPort(port.portName())
            if self.serial_port.isOpen():
                print(f"Connected to {port.portName()}")
                self.serial_port.readyRead.connect(self.receive_data)
                break
        else:
            print("No serial port found")

    def send_data(self, data):
        if self.serial_port:
            self.serial_port.write_data(data)

    def receive_data(self):
        if self.serial_port:
            data = self.serial_port.read_data()
            if data:
                print(f"Received: {data}")


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
