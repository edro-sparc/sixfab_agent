from power_api import SixfabPower, Definition, Event
import time
import os
api = SixfabPower()

intiateShutdown = False

def main():
	global intiateShutdown
	try:
		print(api.get_button1_status())
	except Exception:
		print("Exception")
	while True:
		try:
			if(api.get_button1_status() is 1):
				print("Turning OFF")
				intiateShutdown = True
				# print("Soft Pwr-Off set: " + str(api.create_scheduled_event(1, Definition.EVENT_INTERVAL, Definition.EVENT_ONE_SHOT, 1, Definition.INTERVAL_TYPE_SEC, 0, 3, 500)))
		except Exception:
			time.sleep(5)
			print("Exception")
		else:
			if(intiateShutdown):
				time.sleep(5)
				turnOff()
				# return
			time.sleep(1)


def turnOff():
	# print(api.hard_power_off(15))
	api.create_scheduled_event(1, Definition.EVENT_INTERVAL, Definition.EVENT_ONE_SHOT, 25, Definition.INTERVAL_TYPE_SEC, 0, 2, 500)
	try:
		# print(api.soft_power_off(5))
		# print("button")
		api.get_button1_status()
	except Exception:
		print("Button Exception")
	# os.system("sudo halt")
	os.system("sleep 5 && sudo shutdown -h now")
	# except

if __name__ == '__main__':
	main()