import time
from sage.base_app import BaseApp

if __name__ == '__main__':
    from FPA_algorithm import FPA
    from gaitphase import GaitPhase
else:
    from .FPA_algorithm import FPA
    from .gaitphase import GaitPhase


class Core(BaseApp):
    ###########################################################
    # INITIALIZE APP
    ###########################################################
    def __init__(self, my_sage):
        BaseApp.__init__(self, my_sage, __file__)

        # Set up the algorithm
        self.iteration = 0
        self.pulse_length = self.info["pulse_length"]

        # Init the Gaitphase and Foot Progression Angle (FPA) class
        self.my_GP = GaitPhase(datarate=self.info['datarate'])
        self.my_FPA = FPA(self.config['Is_right_foot'], self.info['datarate'], self.info['alpha'])

        # Define the node numbers for sensors
        self.sensor_foot = self.info["sensors"].index("foot")

        # Define the node numbers for feedback
        self.foot_medial_feedback_nodeNum = self.info["feedback"].index("foot_medial")
        self.foot_lateral_feedback_nodeNum = self.info["feedback"].index("foot_lateral")

        self.is_pull = self.config["PushOrPull"] == "pull"
        self.is_push = self.config["PushOrPull"] == "push"

        self.feedback_foot_medial = 0
        self.feedback_foot_lateral = 0

        # Set Thresholds
        self.FPA_medial_threshold = float(self.config['FPA_medial_threshold'])
        self.FPA_lateral_threshold = float(self.config["FPA_lateral_threshold"])

        self.fpa_lateral_feedback_state = 0
        self.fpa_medial_feedback_state = 0

    ###########################################################
    # CHECK NODE CONNECTIONS
    # Make sure all the nodes needed for sensing and feedback
    # are present before starting the app.
    #
    # If you do not need to check for feedback nodes, you can
    # comment or delete this function. The BaseApp will ensure
    # the correct number of sensing nodes are present and
    # throw an exception if they are not.
    ###########################################################
    def check_status(self):
        sensors_count = self.get_sensors_count()
        feedback_count = self.get_feedback_count()
        err_msg = ""
        if sensors_count < len(self.info['sensors']):
            err_msg += "App requires {} sensors but only {} are connected".format(
                len(self.info["sensors"]), sensors_count
            )
        if self.config["feedback_enabled"] and feedback_count < len(
            self.info["feedback"]
        ):
            err_msg += "App require {} feedback but only {} are connected".format(
                len(self.info["feedback"]), feedback_count
            )
        if err_msg != "":
            return False, err_msg
        return True, "Now running Walking Foot Progression App"

    #############################################################
    # UPON STARTING THE APP
    # If you have anything that needs to happen before the app starts
    # collecting data, you can uncomment the following lines
    # and add the code in there. This function will be called before the
    # run_in_loop() function below.
    #############################################################
    # def on_start_event(self):
    #     print("In On Start Event")

    ###########################################################
    # RUN APP IN LOOP
    ###########################################################
    def run_in_loop(self):
        data = self.my_sage.get_next_data()

        if self.iteration == 0:
            self.start_time = time.time()

        self.my_GP.update_gaitphase(data[self.sensor_foot])
        self.my_FPA.update_FPA(data[self.sensor_foot], self.my_GP.gaitphase_old, self.my_GP.gaitphase)

        if self.my_GP.in_feedback_window:
            # Initialize all variable to 0, and only update them if feedback is given
            # NOTE: This is to indicate which node actually gave the feedback, since it can be different for push/pull feedback.
            self.feedback_foot_medial = 0
            self.feedback_foot_lateral = 0
            feedback_given = self.give_FPA_feedback()

            # if no feedback should be given, make sure to toggle all feedback off
            if not feedback_given:
                self.toggle_all_feedback_off()

        time_now = self.iteration / self.info["datarate"]  # time in seconds

        my_data = {
            "time": [time_now],
            "Step_Count": [self.my_GP.step_count],
            "Gait_Phase": [self.my_GP.gaitphase],
            "FPA_This_Step": [self.my_FPA.FPA_this_step],
            "FPA_Feedback_Medial": [self.feedback_foot_medial],
            "FPA_Feedback_Lateral": [self.feedback_foot_lateral],
        }

        self.my_sage.save_data(data, my_data)
        self.my_sage.send_stream_data(data, my_data)

        # Increment and save data
        self.iteration += 1

        return True
    #############################################################
    # MANAGE FEEDBACK FOR APP
    #############################################################
    def toggle_feedback(self, feedbackNode=0, duration=1, feedback_state=False):
        if feedback_state:
            self.my_sage.feedback_on(feedbackNode, duration)
        else:
            self.my_sage.feedback_off(feedbackNode)

    def give_FPA_feedback(self):
        self.fpa_lateral_feedback_state = int(self.my_FPA.FPA_this_step > self.FPA_lateral_threshold)
        self.fpa_medial_feedback_state = int(
            self.my_FPA.FPA_this_step < self.FPA_medial_threshold
        )
        if self.config["feedback_enabled"]:
            if self.fpa_lateral_feedback_state:
                self.toggle_feedback(
                    self.foot_lateral_feedback_nodeNum,
                    duration=self.pulse_length,
                    feedback_state=self.is_pull,
                )
                self.toggle_feedback(
                    self.foot_medial_feedback_nodeNum,
                    duration=self.pulse_length,
                    feedback_state=self.is_push,
                )
                self.feedback_foot_medial = int(self.is_pull)
                self.feedback_foot_lateral = int(self.is_push)
                return True
            elif self.fpa_medial_feedback_state:
                self.toggle_feedback(
                    self.foot_lateral_feedback_nodeNum,
                    duration=self.pulse_length,
                    feedback_state=self.is_pull,
                )
                self.toggle_feedback(
                    self.foot_medial_feedback_nodeNum,
                    duration=self.pulse_length,
                    feedback_state=self.is_push,
                )
                self.feedback_foot_lateral = int(self.is_pull)
                self.feedback_foot_medial = int(self.is_push)
                return True

            self.toggle_all_feedback_off()
            return False                    

    def toggle_all_feedback_off(self):
        self.toggle_feedback(self.foot_medial_feedback_nodeNum, feedback_state=False)
        self.toggle_feedback(self.foot_lateral_feedback_nodeNum, feedback_state=False)
