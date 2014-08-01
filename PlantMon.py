import sys
import cherrypy
from cherrypy.lib import auth_digest
import hashlib
import os
import serial
from cherrypy.process.plugins import Monitor
import peewee
from peewee import *
from datetime import datetime, timedelta
import calendar
from pushbullet import PushBullet

# set up the database access
db = MySQLDatabase('plantmon', user='root', passwd='pi', threadlocals=True)

ALARM_SETPOINT = 10
ALARM_CLEARPOINT = 80

PUSHBULLET_API = ''
with open('../pushbullet.apikey', 'r') as f:
	PUSHBULLET_API = f.read().strip()

class WaterSensorLog(peewee.Model):
	timestamp = peewee.DateTimeField(formats='%Y-%m-%d %H:%M:%S')
	sensor0 = peewee.FloatField()
	sensor1 = peewee.FloatField()
	sensor2 = peewee.FloatField()
	sensor3 = peewee.FloatField()
	sensor4 = peewee.FloatField()
	sensor5 = peewee.FloatField()

	class Meta:
		database = db

# make sure the tables exist
if not WaterSensorLog.table_exists():
	WaterSensorLog.create_table()

class PlantMon(object):
	def __init__(self):
		super(PlantMon, self).__init__()
		cherrypy.engine.subscribe('stop', self.stop)

		# set up the serial connection
		self.ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=5)

		# set up the data collection
		self._sensorNames = ['Tomatoes', 'Grape Vines', 'Petunias', 'Grass', 'Spruce', '?']
		self.lastUpdate = datetime.now()
		self.vals = [0, 0, 0, 0, 0, 0]
		self.calibrations = [
			[20, 70],
			[20, 70],
			[20, 70],
			[20, 70],
			[20, 70],
			[20, 70]
		]
		self.existingAlarms = [False, False, False, False, False, False]

		# set up pushbullet
		self.pb = PushBullet(PUSHBULLET_API)

		# set up the repetitive background tasks
		self.firstRun = True
		Monitor(cherrypy.engine, self.querySensors, frequency=2).subscribe()
		Monitor(cherrypy.engine, self.logToDB, frequency=300).subscribe()

	# the main template page
	@cherrypy.expose
	def index(self):
		html = ""

		# open the template file
		with open('template/index.html', 'r') as templateFile:
			html = templateFile.read()

		# and return the templated file
		return html

	# interact with the actual sensors
	def querySensors(self):
		self.ser.write("q");
		resp = self.ser.readline()
		try:
			if resp.strip() != '':
				parts = resp.strip().split(",");
				for i in range(0, len(parts)):
					self.vals[i] = ((1024.0 - float(parts[i])) / 1024.0) * 100.0
					self.vals[i] = ((self.vals[i] - self.calibrations[i][0]) / (self.calibrations[i][1] - self.calibrations[i][0])) * 100;
					if self.vals[i] < 0:
						self.vals[i] = 0
					elif self.vals[i] > 100:
						self.vals[i] = 100;
				self.lastUpdate = datetime.now()

				# now check if we're going into alarm
				newAlarms = [False, False, False, False, False, False]
				for i in range(0, 6):
					if self.vals[i] <= ALARM_SETPOINT:
						newAlarms[i] = True
					elif self.vals[i] >= ALARM_CLEARPOINT:
						newAlarms[i] = False

				# see what has changed from the database
				alarmsChanged = False
				hasAlarms = False
				for i in range(0, 6):
					if self.existingAlarms[i] != newAlarms[i]:
						alarmsChanged = True
					if newAlarms[i]:
						hasAlarms = True

				# notify the user
				if alarmsChanged:
					success = None
					push = None
					if hasAlarms:
						msg = 'The following sensors are in alarm: '
						plants = []
						for i in range(0, 6):
							if newAlarms[i]:
								plants.append(self._sensorNames[i])
						msg += ', '.join(plants)
						success, push = self.pb.push_note("PlantMon: PLANT ALARM", msg)
					else:
						success, push = self.pb.push_note("PlantMon: Alarms Cleared", 'All plant alarms have been cleared!')
					print('>>> PLANT ALARM:')
					print('>>>   %s' % msg)
					print('>>>   Push status: %s' % ("sucess" if success else "failed"))

				# update the alarm status
				self.existingAlarms = newAlarms

				if self.firstRun:
					self.logToDB()
					self.firstRun = False
		except Exception as ex:
			print(ex)
			pass

	def logToDB(self):
		loggedRecord = WaterSensorLog(timestamp=self.lastUpdate,
			sensor0=self.vals[0],
			sensor1=self.vals[1],
			sensor2=self.vals[2],
			sensor3=self.vals[3],
			sensor4=self.vals[4],
			sensor5=self.vals[5])
		loggedRecord.save()
		return ['Success']

	@cherrypy.expose
	@cherrypy.tools.json_out()
	def sensors(self):
		return {
			"lastUpdate": calendar.timegm(self.lastUpdate.timetuple()),
			"values": self.vals
		}

	@cherrypy.expose
	@cherrypy.tools.json_out()
	def alarms(self):
		return self.existingAlarms

	@cherrypy.expose
	@cherrypy.tools.json_out()
	def sensorNames(self):
		return self._sensorNames

	@cherrypy.expose
	@cherrypy.tools.json_out()
	def history(self, sensor=-1, cnt=1000, dt=None):
		ret = []
		sensor = int(sensor)
		results = None
		if dt is None:
			results = WaterSensorLog.select().order_by(WaterSensorLog.timestamp.desc()).limit(cnt)
		else:
			results = WaterSensorLog.select().where(WaterSensorLog.timestamp >= (datetime.now() - timedelta(seconds=int(dt)))).order_by(WaterSensorLog.timestamp.desc()).limit(cnt)
		if sensor == -1:
			ret = [[], [], [], [], [], []]
		for record in results:
			if sensor == -1:
				ts = calendar.timegm(record.timestamp.timetuple()) * 1000
				ret[0].append([ts, record.sensor0])
				ret[1].append([ts, record.sensor1])
				ret[2].append([ts, record.sensor2])
				ret[3].append([ts, record.sensor3])
				ret[4].append([ts, record.sensor4])
				ret[5].append([ts, record.sensor5])
			else:
				v = 0
				if sensor == 0:
					v = record.sensor0
				elif sensor == 1:
					v = record.sensor1
				elif sensor == 2:
					v = record.sensor2
				elif sensor == 3:
					v = record.sensor3
				elif sensor == 4:
					v = record.sensor4
				elif sensor == 5:
					v = record.sensor5
				ret.append([calendar.timegm(record.timestamp.timetuple()) * 1000, v])

		# sort the data
		if sensor == -1:
			for i in range(0, 6):
				ret[i] = sorted(ret[i], key=lambda record: record[0])
		else:
			ret = sorted(ret, key=lambda record: record[0])

		return ret

	#def error_page_404(status, message, traceback, version):
	#	return "Nothing to see here!"
	#cherrypy.config.update({'error_page.404': error_page_404})

	def stop(self):
		pass

if __name__ == '__main__':
	# setup the cherrypy configuration
	cherrypy.server.socket_host = '0.0.0.0'
	cherrypy.server.socket_port = 80
	conf = {
		'/': {
			'tools.staticdir.root': os.path.abspath(os.getcwd()),
			'tools.sessions.on': True,
		},
		'/css': {
			'tools.staticdir.on': True,
			'tools.staticdir.dir': os.path.join('template', 'css')
		},
		'/js': {
			'tools.staticdir.on': True,
			'tools.staticdir.dir': os.path.join('template', 'js')
		},
		'/fonts': {
			'tools.staticdir.on': True,
			'tools.staticdir.dir': os.path.join('template', 'fonts')
		},
		'/img': {
			'tools.staticdir.on': True,
			'tools.staticdir.dir': os.path.join('template', 'img')
		},
		'/favicon.ico': {
			'tools.staticfile.on': True,
			'tools.staticfile.filename': os.path.abspath(os.path.join('template', 'favicon.ico'))
		}
	}

	# disable auto-reload
	cherrypy.config.update({'engine.autoreload.on': False})

	# initialize the server
	app = PlantMon()

	# start the server
	cherrypy.quickstart(app, '/', conf)
