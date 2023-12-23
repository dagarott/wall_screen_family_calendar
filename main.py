import sqlite3
from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QApplication, QListWidgetItem, QMessageBox
from PyQt5.uic import loadUi
import sys
import signal
import time
import random
import datetime
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
username ="dagarott@gmail.com" 
password ="Dau8queL"
client_id = f'python-mqtt-{random.randint(0, 1000)}'

class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()
        loadUi("main.ui", self)
        # self.calendarWidget.selectionChanged.connect(self.calendarDateChanged)
        # self.calendarDateChanged()
        # self.saveButton.clicked.connect(self.saveChanges)
        # self.addButton.clicked.connect(self.addNewTask)
         # mqtt client
        self.client = mqtt.Client(client_id, transport="websockets")
        self.client.username_pw_set(username, password)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message= self.on_message
        self.mqtt_connected = False
        print(f'Connecting now to {broker}:{port}')
        self.client.connect(broker, port)
        self.client.loop_start()
        self.client.subscribe(topic)
        
    def calendarDateChanged(self):
        print("The calendar date was changed.")
        dateSelected = self.calendarWidget.selectedDate().toPyDate()
        print("Date selected:", dateSelected)
        # self.updateTaskList(dateSelected)
        # self.msg = "MAX7219 LED Matrix Demo"
        # print(self.msg)
        # show_message(device, self.msg, fill="white", font=proportional(CP437_FONT))

    def mostrar_eventos(self):
        # Obtener la fecha de mañana
        mañana = datetime.date.today() + datetime.timedelta(days=1)
        print(mañana)

        # Obtener eventos programados para mañana desde la base de datos
        conn = sqlite3.connect("eventos.db")
        c = conn.cursor()
        c.execute("SELECT fecha, hora, descripcion FROM eventos WHERE fecha = ?;", (mañana,))
        eventos = c.fetchall()
        conn.close()

        if eventos:
            texto_eventos = "\n".join([f"{evento[0]} {evento[1]}: {evento[2]}" for evento in eventos])
            print(texto_eventos)
        else:
            print("No hay eventos programados para mañana.")

    def guardar_evento(self, msg_date,msg_time,msg_description):
        self.fecha = msg_date
        self.hora = msg_time
        self.descripcion = msg_description

        # Guardar evento en la base de datos
        conn = sqlite3.connect("eventos.db")
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS eventos (fecha DATE, hora TIME, descripcion TEXT);")
        c.execute("INSERT INTO eventos VALUES (?, ?, ?);", (self.fecha, self.hora, self.descripcion))
        conn.commit()
        conn.close()
        print("Evento guardado exitosamente.")
        self.mostrar_eventos()

    # def updateTaskList(self, date):
    #     self.tasksListWidget.clear()

    #     db = sqlite3.connect("data.db")
    #     cursor = db.cursor()

    #     query = "SELECT task, completed FROM tasks WHERE date = ?"
    #     row = (date,)
    #     results = cursor.execute(query, row).fetchall()
    #     for result in results:
    #         item = QListWidgetItem(str(result[0]))
    #         item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
    #         if result[1] == "YES":
    #             item.setCheckState(QtCore.Qt.Checked)
    #         elif result[1] == "NO":
    #             item.setCheckState(QtCore.Qt.Unchecked)
    #         self.tasksListWidget.addItem(item)


    # def saveChanges(self):
    #     db = sqlite3.connect("data.db")
    #     cursor = db.cursor()
    #     date = self.calendarWidget.selectedDate().toPyDate()

    #     for i in range(self.tasksListWidget.count()):
    #         item = self.tasksListWidget.item(i)
    #         task = item.text()
    #         if item.checkState() == QtCore.Qt.Checked:
    #             query = "UPDATE tasks SET completed = 'YES' WHERE task = ? AND date = ?"
    #         else:
    #             query = "UPDATE tasks SET completed = 'NO' WHERE task = ? AND date = ?"
    #         row = (task, date,)
    #         cursor.execute(query, row)
    #     db.commit()

    #     messageBox = QMessageBox()
    #     messageBox.setText("Changes saved.")
    #     messageBox.setStandardButtons(QMessageBox.Ok)
    #     messageBox.exec()

    # def addNewTask(self):
    #     db = sqlite3.connect("data.db")
    #     cursor = db.cursor()

    #     newTask = str(self.taskLineEdit.text())
    #     date = self.calendarWidget.selectedDate().toPyDate()

    #     query = "INSERT INTO tasks(task, completed, date) VALUES (?,?,?)"
    #     row = (newTask, "NO", date,)

    #     cursor.execute(query, row)
    #     db.commit()
    #     self.updateTaskList(date)
    #     self.taskLineEdit.clear()

    def on_connect(self, client, userdata, flags, rc):
        print("Connected With Result Code " + str(rc))
        self.mqtt_connected = True

    def on_disconnect(self, *args):
        print("Disconnected from broker")
        self.mqtt_connected = False
        # stop loop
        self.client.loop_stop()

    def on_subscribe(self,mqttsub, obj, mid, granted_qos):
        print("Subscribed: " + str(mid) + " " + str(granted_qos))

    def on_message(self, client, userdata, message):
        # print("message received " ,str(message.payload.decode("utf-8")))
        self.msg_data =str(message.payload.decode("utf-8")).split(",")
        print("date:",self.msg_data[0])
        print("time:",self.msg_data[1])
        print("description:",self.msg_data[2])
        self.EventList.addItem(str(message.payload.decode("utf-8")))
        self.guardar_evento( self.msg_data[0],self.msg_data[1],self.msg_data[2])

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