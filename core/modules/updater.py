import os
import re
import json

LOCAL_FIRMWARE_FOLDER = '/opt/sixfab/pms_firmwares'

def update_firmware(**kwargs):
    api = kwargs.get('api')
    token = kwargs.get("token")
    remote_repository = kwargs.get("repository", None)
    mqtt_client = kwargs.get("mqtt_client", None)
    lock_feeder = kwargs.get("lock_feeder", None)

    def send_status(status):
        mqtt_client.publish(
            f"/device/{token}/hive", 
            json.dumps({
                "command": "update_status_firmware",
                "status": status
            })
        )

    send_status("git")

    if os.path.exists(LOCAL_FIRMWARE_FOLDER):
        os.system(f"cd {LOCAL_FIRMWARE_FOLDER} && sudo git pull")
    else:
        os.system(f"sudo git clone {remote_repository} {LOCAL_FIRMWARE_FOLDER}")

    latest_version = open(f"{LOCAL_FIRMWARE_FOLDER}/latest_version").read().strip()
    latest_firmware = f"{LOCAL_FIRMWARE_FOLDER}/sixfab_pms_firmware_{latest_version}.bin"

    try:
        current_firmware_version = api.getFirmwareVer()
    except:
        send_status("error")
        return

    if isinstance(current_firmware_version, str):
        current_firmware_version = re.search("v([0-9]*.[0-9]*.[0-9]*)", current_firmware_version)[1]
    elif isinstance(current_firmware_version, bytearray) or isinstance(current_firmware_version, bytes):
        current_firmware_version = current_firmware_version.decode().replace("v", "")

    #if current_firmware_version == latest_version[1:]:
    #    send_status("finish")
    #    return

    if not os.path.exists(latest_firmware):
        send_status("firmware_not_exists")
        return

    try:
        last_step_cache = 0
        for step in api.updateFirmware(latest_firmware):
            if last_step_cache < 100 and step-last_step_cache > 2 :
                last_step_cache = step
                send_status(step)
    except:
        send_status("error")
        return


    send_status("finish")



def update_agent(**kwargs):
    mqtt_client = kwargs.get("mqtt_client")
    token = kwargs.get("token")

    def send_status(status):
        mqtt_client.publish(
            f"/device/{token}/hive", 
            json.dumps({
                "command": "update_status_agent",
                "status": status
            })
        )
    
    send_status("git")

    os.system("cd /opt/sixfab/pms-agent && sudo git pull")

    send_status("restart_service")

    os.system("sudo systemctl restart pms_agent")

    send_status("finish")