# %%
import json
# %%
class agent:
    """
    Class to represent agents with trajectories from a simularium file
    """

    def __init__(
        self,
        agent_ID = None,
        type_ID = None,
        current_time = [],
        position = [[]],
        rotation = [[[]]],
        radius = [],
    ):
        self.agent_ID = agent_ID
        self.time_points = [current_time]
        self.position = [position]
        self.rotation = [rotation]
        self.radius = radius
        self.type_ID = type_ID

    def append_position(self, input_position):
        self.position = self.position.append(input_position)

    def append_rotation(self, input_rotation):
        self.rotation = self.rotation.append(input_rotation)

    def append_time_point(self, current_time):
        self.time_points = self.time_points.append(current_time)

# %%
def update_agent_info(agent_dict, current_time, all_data, line_counter):
    line_counter += 1
    agent_ID = all_data[line_counter]
    line_counter += 1
    type_ID = all_data[line_counter]
    line_counter += 1
    current_position = all_data[line_counter:line_counter+3]
    line_counter += 3
    current_rotation = all_data[line_counter:line_counter+3]
    line_counter += 3
    radius = all_data[line_counter]
    line_counter += 1
    number_of_subpoints = all_data[line_counter]
    if(number_of_subpoints):
        pass
    else:
        line_counter += 1
    
    if(agent_ID in agent_dict):
        # import ipdb; ipdb.set_trace()
        current_agent = agent_dict[agent_ID]
        current_agent.time_points.append(current_time)
        current_agent.position.append(current_position)
        current_agent.rotation.append(current_rotation)
    else:
        agent_dict[agent_ID] = agent(agent_ID,
                                    type_ID,
                                    current_time,
                                    current_position,
                                    current_rotation,
                                    radius,
                                )
    return agent_dict, line_counter

# %%
data_file = open("/mnt/c/Users/saurabh.mogre/OneDrive - Allen Institute/Projects/cellpack/jitter.simularium")
parsed_data = json.load(data_file)

# %%
len(parsed_data['spatialData']['bundleData'])

# %%
parsed_data['spatialData']['bundleData'][299]['frameNumber']

# %%
frame_list = parsed_data['spatialData']['bundleData']
agent_dict = {}
for count, frame in enumerate(frame_list):
    print(count)
    all_data = frame["data"]
    line_counter = 0
    current_time = frame["time"]
    while line_counter < len(all_data):
        agent_dict, line_counter = update_agent_info(
                                    agent_dict,
                                    current_time,
                                    all_data,
                                    line_counter,
                                    )

import ipdb; ipdb.set_trace()