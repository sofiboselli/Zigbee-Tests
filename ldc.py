from zigbee_controller import ZigbeeController
import asyncio
import json
import readline
import aioconsole


zigbee_controller = ZigbeeController()

command_description = {'join': 'allow devices to pair for 60 seconds.', 'devices': 'list of devices with ieee, endpoints and clusters.', 'state': 'state of each supported cluster and attribute of defined ieee. address needed', 'command': 'fires command on defined ieee with defined parameters. Address, command and parameters needed.'}

async def permit_join(ieee=None, command=None, params=None):
    print("Devices can join for the next 60 seconds")
    permit_join_future = asyncio.create_task(zigbee_controller.permit_join())
    permit_join_future.add_done_callback(lambda future: print("devices can no longer join the network"))

async def get_devices(ieee=None, command=None, params=None):
    print(zigbee_controller.get_devices())

async def get_state(ieee=None, command=None, params=None):
    v = await zigbee_controller.get_state_by_ieee(ieee)
    print(v)

async def fire_command(ieee=None, command=None, params=None):
    await zigbee_controller.send_command(ieee, command, params)

def help():
    print("ZIGBEE COMMAND LINE:")
    print("Accepts: {\"command\":{zigbee_command}, \"address\":{address}, \"attributes\":{\"command\":{command}, \"params\":{parameters}}}")
    print("Available commands:")
    for command, description in command_description.items():
        print("- "+command+":", description)

zigbee_functions = {'join':permit_join, 'devices':get_devices, 'state':get_state, 'command':fire_command}

async def input_loop():
    while True:
        #line = input('>')
        line = await aioconsole.ainput('>')
        data = json.loads(line)
        ieee = data['address'] if 'address' in data.keys() else None
        command = data['attributes']['command'] if 'attributes' in data.keys() else None
        params = data['attributes']['params'] if 'attributes' in data.keys() and 'params' in data['attributes'].keys() else []
        zigbee_command = data['command'] if 'command' in data.keys() else None
        if zigbee_command in zigbee_functions:
            await zigbee_functions[zigbee_command](ieee, command, params)

help()
readline.parse_and_bind('tab: complete')
readline.parse_and_bind('set editing-mode vi')

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(zigbee_controller.setup_network())
    asyncio.get_event_loop().run_until_complete(input_loop())
