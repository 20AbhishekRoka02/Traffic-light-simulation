import traci
traci.start(['sumo', '-c', 'simulation.sumocfg', '--no-step-log'])
traci.simulationStep()
tls_list = traci.trafficlight.getIDList()
print('All TLS IDs:')
for tls in tls_list:
    print(f'  {tls}')
traci.close()