#!/usr/bin/env python3

import socket, requests, subprocess, docker, sys, json, time, os
HOST = socket.gethostname()
DOCKER_CLIENT = docker.from_env()
BGP_IP = "147.75.40.26"
CONTAINER_CRON = "fdt-cron"

def is_BGPIP_exist():
    unreachable = "BGP IP not in here!"
    cmd = f'ip a | grep -w {BGP_IP} | awk '"'{print $2}'"' | awk -F"/" '"'{print $1}'"''
    process = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    if BGP_IP in process.stdout:
        return process.stdout
    else:
        return unreachable

def is_container_running(container_name):
    container = DOCKER_CLIENT.containers.get(container_name)
    container_state = container.attrs['State']
    container_status = ""
    if container_state['Status'] == 'running':
        container_status = 'running'
        return container_status
    elif container_state['Status'] == 'exited':
        container_status = 'exited'
        return container_status

def is_running_true(container_name):
    container = DOCKER_CLIENT.containers.get(container_name)
    container_state = container.attrs['State']
    is_running = ""
    if container_state['Running'] == True:
        is_running = True
        return is_running
    elif container_state['Running'] == False:
        is_running = False
        return is_running


def slack(message, stat_color, status):
    url = "https://hooks.slack.com/services/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"
    title = (f"FDT Status!")
    slack_data = {
        "username": "FDT-BOT",
        "icon_emoji": ":packet:",
        "channel" : "#fdt-alerts",
        "attachments": [
            {
                "pretext": status,
                "color": stat_color,
                "fields": [
                    {
                        "title": title,
                        "value": message,
                        "short": "false",
                    }
                ]
            }
        ]
    }
    byte_length = str(sys.getsizeof(slack_data))
    headers = {'Content-Type': "application/json", 'Content-Length': byte_length}
    response = requests.post(url, data=json.dumps(slack_data), headers=headers)
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)

def main():
    is_exist = is_BGPIP_exist()
    cont_status = is_container_running(CONTAINER_CRON)
    is_cont_running = is_running_true(CONTAINER_CRON)

    if BGP_IP in is_exist:
        if is_cont_running == False and cont_status == 'exited':
            print("BGP IP exist and checking container status.")
            print(f"Container {CONTAINER_CRON} is ", cont_status, "and Running state is", is_cont_running)
            print(f"Starting container {CONTAINER_CRON}")
            docker_start = f"docker start {CONTAINER_CRON}"
            p = subprocess.run(docker_start , shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(5)

            #show container status
            container = DOCKER_CLIENT.containers.get(CONTAINER_CRON)
            container_state = container.attrs['State']
            #Verify container if it runs after the command
            container_status = container_state['Status']
            container_running = container_state['Running']
            if container_status == 'running' and container_running == True:
                # message = f"Anyoung haseyo! Started {CONTAINER_CRON} at {HOST}"
                print('Container started!')
                message = f"Anyoung haseyo! Started {CONTAINER_CRON} at {HOST}"
                color="#2EB67D"
                status = "_Container Started_"
                print("Sending status to slack...")
                slack(message, color, status)
            else:
                print("Container is not running!")
        elif is_cont_running == True and cont_status == 'running':
            print(f"Container {CONTAINER_CRON} is already running!")
            
    elif BGP_IP != is_exist:
        print("BGP IP does not exist!")
        if is_cont_running == True and cont_status == 'running':
            #check if container is running
            docker_stop = f"docker stop {CONTAINER_CRON} || docker kill -s 15 {CONTAINER_CRON}"
            p = subprocess.run(docker_stop , shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(5)

            container = DOCKER_CLIENT.containers.get(CONTAINER_CRON)
            container_state = container.attrs['State']
            #Verify container if it runs after the command
            container_status = container_state['Status']
            container_running = container_state['Running']

            print(container_status, container_status)
            if container_status == 'exited' and container_running == False:
                print('Container stopped!')
                message = f"Anyoung haseyo! Stopped {CONTAINER_CRON} at {HOST}"
                color="#B62E2E"
                status = "_Container Stopped_"
                print("Sending status to slack...")
                slack(message, color, status)
            else:
                print("Container does not stop! Please check.")
        else:
            print("Container is not running!")

if __name__ == "__main__":
    pid = str(os.getpid())
    scriptname = os.path.basename(__file__)
    pidfile= f"/var/run/{scriptname}.pid"

    if os.path.isfile(pidfile):
        print ("%s already exists, exiting" % pidfile)
        sys.exit()
    file = open(pidfile, 'w').write(pid)
    try:
        main()
    finally:
        os.unlink(pidfile)

