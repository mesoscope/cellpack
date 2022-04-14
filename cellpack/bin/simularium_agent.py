import json
import numpy

class simularium_agent:
    """
    Class to represent agents with trajectories from a simularium file
    """

    def __init__(
        self,
        agent_ID = None,
        type_ID = None,
        current_time = [],
        position = [],
        rotation = [],
        radius = [],
    ):
        self.agent_ID = agent_ID
        self.time_points = current_time
        self.position = position
        self.rotation = rotation
        self.radius = radius
        self.type_ID = type_ID

    def append_position(self, input_position):
        self.position.append(input_position)

    def append_rotation(self, input_rotation):
        self.rotation.append(input_rotation)

    def append_time_point(self, current_time):
        self.time_points.append(current_time)

    def get_single_MSD(self):
        # calculates brute force MSD
        positions = numpy.array(self.position, dtype=object, copy=False)
        time_shift = numpy.arange(len(positions))
        MSD = numpy.zeros_like(time_shift)
        import ipdb; ipdb.set_trace()
        for index, shift in enumerate(time_shift):
            displacements = positions[:-shift if shift else None] - positions[shift:]
            sq_disp = numpy.square(displacements).sum(axis=1)
            MSD[index] = sq_disp.mean()

        self.MSD = MSD
        
        return MSD
    
    @classmethod
    def get_MSD_for_all_agents(self,agent_dict):
        for agent in agent_dict.values():
            self.MSD = self.get_single_MSD(agent)

    @classmethod
    def parse_simularium_file(self, data_file):
        parsed_data = json.load(data_file)

        frame_list = parsed_data["spatialData"]["bundleData"]
        time_step_size = parsed_data["trajectoryInfo"]["timeStepSize"]
        time_units = (parsed_data["trajectoryInfo"]["timeUnits"]["magnitude"],
                    parsed_data["trajectoryInfo"]["spatialUnits"]["name"]
                    )
        space_units  = (parsed_data["trajectoryInfo"]["timeUnits"]["magnitude"],
                    parsed_data["trajectoryInfo"]["spatialUnits"]["name"],
                    )
        agent_dict = {}
        for frame in frame_list:
            all_data = frame["data"]
            line_counter = 0
            current_time = frame["time"]
            while line_counter < len(all_data):
                agent_dict, line_counter = self.update_agent_info(
                                            agent_dict,
                                            current_time,
                                            all_data,
                                            line_counter,
                                            )
        return agent_dict, time_step_size, time_units, space_units

    @staticmethod
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
            current_agent = agent_dict[agent_ID]
            current_agent.time_points.append(current_time)
            current_agent.position.append(current_position)
            current_agent.rotation.append(current_rotation)
        else:
            agent_dict[agent_ID] = simularium_agent(agent_ID,
                                        type_ID,
                                        [current_time],
                                        [current_position],
                                        [current_rotation],
                                        radius,
                                    )
        return agent_dict, line_counter