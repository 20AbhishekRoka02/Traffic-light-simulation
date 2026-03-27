import traci
TARGET_TLS = 'cluster_267196276_6666318646_6666318659_6666328407_#2more'
traci.start(['sumo', '-c', 'simulation.sumocfg', '--no-step-log'])
traci.simulationStep()

links = traci.trafficlight.getControlledLinks(TARGET_TLS)
print(f'Number of controlled links: {len(links)}')

logics = traci.trafficlight.getAllProgramLogics(TARGET_TLS)
for program in logics:
    print(f'Program ID: {program.programID}')
    for i, phase in enumerate(program.phases):
        print(f'  Phase {i}: duration={phase.duration}s  state={phase.state}')
traci.close()