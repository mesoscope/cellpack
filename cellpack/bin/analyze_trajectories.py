from simularium_agent import simularium_agent

data_file = open("/mnt/c/Users/saurabh.mogre/OneDrive - Allen Institute/Projects/cellpack/jitter.simularium")

agent_dict, time_step_size, time_units, space_units = simularium_agent.parse_simularium_file(data_file=data_file)

simularium_agent.get_MSD_for_all_agents(agent_dict)

print(agent_dict[1].MSD)