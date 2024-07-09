import numpy as np
from .const import EARLY_STANCE, MIDDLE_STANCE, LATE_STANCE, SWING


class GaitPhase:
    def __init__(self, datarate=50):
        """
        This class is to Calulate the gait phase
        @input: datarate, the update rate, unit is Hz.
        """

        # start at 0.6s of stance time, will update each step
        self.last_stance_time = 0.6
        # 25% of stance time
        self.MIDDLESTANCE_ITERS_THRESHOLD = self.last_stance_time * 0.25 * datarate
        # 50% of stance time
        self.LATESTANCE_ITERS_THRESHOLD = self.last_stance_time * 0.5 * datarate
        self.GYROMAG_THRESHOLD_HEELSTRIKE = 45  # unit:degree
        self.GYROMAG_THRESHOLD_TOEOFF = 45  # unit:degree
        self.HEELSTRIKE_ITERS_THRESHOLD = 0.1 * datarate  # 0.1s
        self.DATARATE = datarate

        self.gaitphase = LATE_STANCE
        self.gaitphase_old = LATE_STANCE
        self.step_count = 0
        self.iters_consecutive_below_gyroMag_thresh = 0
        self.iters_stance = 0

        self.in_feedback_window = False

        self.FPA_buffer = []
        self.FPA_this_frame = 0
        self.FPA_this_step = 0

    def update_gaitphase(self, sensor_data):
        gyroMag = np.linalg.norm(
            [sensor_data["GyroX"], sensor_data["GyroY"], sensor_data["GyroZ"]],
            ord=2,
        )
        if self.gaitphase == SWING:
            self.gaitphase_old = SWING
            if gyroMag < self.GYROMAG_THRESHOLD_HEELSTRIKE:
                # If the gyroMag below than the threshold for a certain time,
                # change gaitphase to stance.
                self.iters_consecutive_below_gyroMag_thresh += 1
                if (
                    self.iters_consecutive_below_gyroMag_thresh
                    > self.HEELSTRIKE_ITERS_THRESHOLD
                ):
                    self.iters_consecutive_below_gyroMag_thresh = 0
                    self.iters_stance = 0
                    self.step_count += 1
                    self.gaitphase = EARLY_STANCE
            else:
                # If the gyroMag larger than the threshold, reset the timer
                self.iters_consecutive_below_gyroMag_thresh = 0
        elif self.gaitphase == EARLY_STANCE:
            self.gaitphase_old = EARLY_STANCE
            self.iters_stance += 1
            # If the timer longer than a threshold, change gaitphase to late stance
            if self.iters_stance > self.MIDDLESTANCE_ITERS_THRESHOLD:
                self.gaitphase = MIDDLE_STANCE
        elif self.gaitphase == MIDDLE_STANCE:
            self.gaitphase_old = MIDDLE_STANCE
            self.iters_stance += 1
            if self.iters_stance > self.LATESTANCE_ITERS_THRESHOLD:
                self.gaitphase = LATE_STANCE
        elif self.gaitphase == LATE_STANCE:
            self.gaitphase_old = LATE_STANCE
            self.iters_stance += 1
            # If the gyroMag larger than the threshold, change gaitphase to swing.
            if gyroMag > self.GYROMAG_THRESHOLD_TOEOFF:
                self.last_stance_time = self.iters_stance / self.DATARATE
                if self.last_stance_time > 2:
                    self.last_stance_time = 2
                elif self.last_stance_time < 0.4:
                    self.last_stance_time = 0.4
                self.gaitphase = SWING

        self.in_feedback_window = (
            self.gaitphase_old == MIDDLE_STANCE and self.gaitphase == LATE_STANCE
        )
