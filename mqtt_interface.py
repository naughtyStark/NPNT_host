import os
import paho.mqtt.client as mqtt
import time
import threading

class mqtt_interface():

    def __init__(self):
        self.host = "192.168.29.52"
        self.client = mqtt.Client()
        self.connection = False
        self.last_update = time.time() - 7
        self.client.on_connect = self.connect_cb
        self.client.on_message = self.message_cb
        self.npnt_log_topic = "NPNT/log"  # topic on which RFM publishes
        self.flgt_log_topic = "FLGT/log"  # topic on which RFM publishes
        self.error_topic = "NPNT/error"  # topic on which RFM publishes
        self.status_topic = "NPNT/status"  # topic on which RFM publishes
        self.rfm_beat_topic = "RFM/heartbeat" # topic on which RFM Publishes
        self.UIN_get_topic = "NPNT/UIN_get"  # topic which RFM publishes to
        self.npnt_pa_topic = "NPNT/permArt"  # topic which RFM listens to
        self.npnt_key_topic = "NPNT/pubkey"  # topic which RFM listens to
        self.command_topic = "NPNT/command"  # topic which RFM listens to
        self.UIN_set_topic = "NPNT/UIN_set"  # topic which RFM listens to. Psswd protected
        self.error = None
        self.info = None
        self.new_error = False
        self.new_info = False
        self.PA_filename = None
        self.RFM_connected = False
        proc = threading.Thread(target = self.update_heartbeat)
        proc.setDaemon(True)
        proc.start()

    def LOG_REQUEST(self):
        self.client.publish(self.command_topic,"send_npnt_log")

    def APM_LOG_REQUEST(self):
        self.client.publish(self.command_topic,"send_apm_log")

    def UIN_GET(self):
        self.client.publish(self.command_topic,"reflect UIN")

    def connect_cb(self, client, userdata, flags, rc):
        self.connection = True
        self.client.subscribe(self.npnt_log_topic)
        self.client.subscribe(self.flgt_log_topic)
        self.client.subscribe(self.error_topic)
        self.client.subscribe(self.status_topic)
        self.client.subscribe(self.rfm_beat_topic)
        self.client.subscribe(self.UIN_get_topic)

    def message_cb(self, client, userdata, msg):
        if(msg.topic == self.npnt_log_topic):
            self.receive_log("npnt_log.json", msg.payload)
        elif(msg.topic == self.flgt_log_topic):
            self.receive_log("flgt_log.bin", msg.payload)
        elif(msg.topic == self.error_topic):
            self.handle_error(msg.payload)
        elif(msg.topic == self.status_topic):
            self.handle_status(msg.payload)
        elif(msg.topic == self.rfm_beat_topic):
            self.handle_heartbeat(msg.payload)
        elif(msg.topic == self.UIN_get):
            self.send_UIN()
        else:
            print("invalid topic name")

    def handle_error(self, info):
        self.error = info
        self.new_error = True

    def handle_status(self,info):
        self.info = info
        self.new_info = True

    def handle_heartbeat(self,data):
        self.last_update = time.time()

    def update_heartbeat(self):
        while True:
            if(time.time() - self.last_update < 6):
                self.RFM_connected = True
            else:
                self.RFM_connected = False
            if(self.connection == False):
                self.client.connect(self.host, 1883)
                self.client.loop_start()
            time.sleep(0.5)

    def receive_log(self, filename, data):
        filename = base_path + "\\" + filename
        with open(filename, "wb") as f:
            f.write(data)
            f.close()
        print("log received and saved as:", filename)

    def send_file(self, topic, filename):
        filesize = os.path.getsize(filename)
        if(filesize > 0):
            with open(filename, "rb") as f:
                data = f.read(filesize)
                f.close()
            self.client.publish(topic, data)
        else:
            self.error = "no such file or directory"
            self.new_error = True

    def PA_SEND(self):
        self.send_file(self.npnt_pa_topic, self.PA_filename)

    def on_closing(self):
        self.client.loop_stop()