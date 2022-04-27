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
    # adds a position to an agent
        self.position.append(input_position)

    def append_rotation(self, input_rotation):
    # adds a rotation to an agent        
        self.rotation.append(input_rotation)

    def append_time_point(self, current_time):
    # adds a time point to an agent
        self.time_points.append(current_time)

    def get_time_averaged_MSD(self):
    # calculates the time averaged MSD for a single agent
        positions = numpy.array(self.position, dtype=object, copy=False)
        time_shift = numpy.arange(len(positions))
        MSD = numpy.zeros(len(time_shift))
        for index, shift in enumerate(time_shift):
            displacements = positions[:-shift if shift else None] - positions[shift:]
            sq_disp = numpy.square(displacements).sum(axis=1)
            MSD[index] = sq_disp.mean()

        self.MSD = MSD
        
        return MSD

    @staticmethod
    def get_ensemble_MSD(agent_dict):
    # gets the ensemble averaged MSD
    # averages are performed over agents of the same type
    # assumes that all time points are evenly spaced
        ensemble_MSD = {}
        ensemble_counts = {}

        for agent in agent_dict.values():
            if agent.type_ID in ensemble_MSD:
                n_points = len(agent.MSD)

                tmp_MSD = ensemble_MSD[agent.type_ID]
                tmp_MSD[0:n_points] = tmp_MSD[0:n_points] + agent.MSD
                ensemble_MSD[agent.type_ID] = tmp_MSD
                
                tmp_count = ensemble_counts[agent.type_ID]
                tmp_count[0:n_points] += 1
                ensemble_counts[agent.type_ID] = tmp_count

            else:
                n_points = len(agent.MSD)
                ensemble_MSD[agent.type_ID] = agent.MSD
                tmp = numpy.ones(n_points)
                ensemble_counts[agent.type_ID] = tmp

        time_points = {}
        for agent_type in ensemble_MSD:
            ensemble_MSD[agent_type] = ensemble_MSD[agent_type]/ensemble_counts[agent_type]
            time_points[agent_type] = numpy.arange(len(ensemble_MSD[agent_type]))
        
        return time_points, ensemble_MSD

    
    @classmethod
    def get_MSD_for_all_agents(self,agent_dict):
    # calculates the MSD for all agents
        for agent in agent_dict.values():
            self.MSD = self.get_time_averaged_MSD(agent)

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
    def enumerate_agents(agent_dict):
        agent_counts = {}
        for agent in agent_dict.values():
            if agent.type_ID in agent_counts:
                agent_counts[agent.type_ID]['count'] += 1
            else:
                agent_counts[agent.type_ID] = {}
                agent_counts[agent.type_ID]['count'] = 1
                agent_counts[agent.type_ID]['radius'] = agent.radius
        return agent_counts

    @staticmethod
    def get_MSD_scaling(time_points, MSD):
    # calculates the scaling alpha of the MSD
    # MSD = 2D * time_points^alpha
        if not MSD[0]:
            MSD = MSD[1:]
        if not time_points[0]:
            time_points = time_points[1:]
        log_MSD = numpy.log(MSD)
        log_time = numpy.log(time_points)

        mult_matrix = numpy.vstack([log_time, numpy.ones(len(log_time))]).T
        scaling, intercept = numpy.linalg.lstsq(mult_matrix, log_MSD, rcond=None)[0]
        diffusion_coefficient = numpy.exp(intercept) / 2.0

        return diffusion_coefficient, scaling

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