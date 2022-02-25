from zigbee_controller_prueba import ZigbeeController
zigbee_controller = ZigbeeController()

def prueba():
	v = zigbee_controller.get_state_by_ieee(3781220557901936)
	print(v)

prueba()


