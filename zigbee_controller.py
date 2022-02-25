from bellows.ezsp import EZSP
from bellows.zigbee.application import ControllerApplication
from zigpy.exceptions import ZigbeeException
import bellows
import asyncio
import os
import zigpy.config
import zigpy.endpoint
from zigpy import types as t
import logging

LOGGER = logging.getLogger(__name__)

APP_CONFIG = {bellows.config.CONF_DEVICE: {bellows.config.CONF_DEVICE_PATH: "/dev/ttyUSB1",
                                           bellows.config.CONF_DEVICE_BAUDRATE: 57600, },
              zigpy.config.CONF_DATABASE: "devices.db",
              bellows.config.CONF_PARAM_UNK_DEV: "yes", }

DEVICE_CONFIG = {
    bellows.config.CONF_DEVICE_PATH: "/dev/ttyUSB1",
    bellows.config.CONF_DEVICE_BAUDRATE: 57600,
    bellows.config.CONF_FLOW_CONTROL: "software",
}


class ZigbeeController():

    def __init__(self):
        self.ezsp = EZSP(DEVICE_CONFIG)
        app_cfg = bellows.zigbee.application.ControllerApplication.SCHEMA(
            APP_CONFIG)
        self.app = asyncio.get_event_loop().run_until_complete(
            bellows.zigbee.application.ControllerApplication.new(
                app_cfg, start_radio=True)
        )

    async def setup_network(self):
        LOGGER.info("Setting up the ZigBee network")
        LOGGER.info("Network setup complete!")

    async def permit_join(self):
        await self.app.permit()
        await asyncio.sleep(60)

    def _ieee_to_number(self, ieee):
        ieee_string = str(t.EUI64(map(t.uint8_t, ieee)))
        return int(ieee_string.replace(':', ''), 16)

    def _get_device_by_ieee(self, ieee_to_find):
        for ieee, dev in self.app.devices.items():
            if self._ieee_to_number(ieee) == ieee_to_find:
                return dev
        raise Exception("Device %s is not in the device database" %
                        (ieee_to_find,))

    def _get_cluster_by_command(self, device, command):
        for epid, ep in device.endpoints.items():
            if epid == 0 or not hasattr(ep, "in_clusters"):
                continue
            for cluster_id, cluster in ep.in_clusters.items():
                for server_command_id, server_command in cluster.server_commands.items():
                    if command in server_command:
                        return cluster

        raise Exception("Device does not support command %s!" % (command,))

    def get_devices(self):
        devices = []

        for ieee, dev in self.app.devices.items():
            device = {
                "ieee": self._ieee_to_number(ieee),
                "nwk": dev.nwk,
                "endpoints": []
            }
            for epid, ep in dev.endpoints.items():
                if epid == 0:
                    continue
                device["endpoints"].append({
                    "id": epid,
                    "input_clusters": [in_cluster for in_cluster in ep.in_clusters] if hasattr(ep, "in_clusters") else [],
                    "output_clusters": [out_cluster for out_cluster in ep.out_clusters] if hasattr(ep, "out_clusters") else [],
                    "status": "uninitialized" if ep.status == zigpy.endpoint.Status.NEW else "initialized"
                })

            devices.append(device)
        return devices


    async def IASZoneEnroll(self, cluster):
        ieee = 3781220875909033
        try:
            res = await cluster.write_attributes({"cie_addr": ieee})
        except ZigbeeException as ex:
            #LOGGER.info("ERROR OCCURRED: %s",str(ex))
            LOGGER.info("ERROR OCCURRED")
        LOGGER.info("Sending IAS enroll response")
        cluster.create_catching_task(cluster.enroll_response(0,0))



    async def get_state_by_ieee(self, device_ieee):
        cluster_states = []
        supported_clusters = {6: [0], 8:[0], 768: [0,1,3,4,7], 1280: [0]}
        device = self._get_device_by_ieee(device_ieee)
        for epid, ep in device.endpoints.items():
            if epid == 0 or not hasattr(ep, "in_clusters"):
                continue
            for cluster_id, cluster in ep.in_clusters.items():
                if cluster_id in supported_clusters:
                    if cluster_id == 1280:
                        await self.IASZoneEnroll(cluster)
                    v = await cluster.read_attributes(supported_clusters[cluster_id])
                    state = []
                    for x in v[0]:
                        state.append({"attribute": x, "value": v[0][x]})
                    cluster_states.append({"cluster_id":cluster_id, "state":state})
        return cluster_states

    async def send_command(self, device_ieee, command, params=""):
        device=self._get_device_by_ieee(device_ieee)
        LOGGER.info("sending command %s to device %s" % (command, device_ieee))
        v=await getattr(self._get_cluster_by_command(device, command), command)(*params)
        LOGGER.info(v)

