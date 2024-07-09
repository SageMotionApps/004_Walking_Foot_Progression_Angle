# 004 Walking Foot Progression Angle
Measure and train foot progression angle during walking.

### Nodes Required: 3 
- Sensing (1): foot (top, switch pointing forward) 
- Feedback (2): 
  - foot_medial
  - foot_lateral 


## Algorithm & Calibration
### Algorithm Information
This algorithm is based on the Tan2020 magnetometer-free FPA algorithm [1]. It only uses accelerometer and gyroscope data thus avoiding magnetic disturbance issues. It detects the heading direction based on the max acceleration direction of the foot and could work on either treadmill or overground. Abnormal gait may influence the accuracy. Foot sensor calibration depends on foot sensor installation.

### Calibration Process:
- Tape the node onto the foot with the Y-axis aligned with the foot axis and node switch pointing towards the toe.
- Subject stands up straight with foot flat on the ground.
- Click the start button in the web interface and the subject may start walking.
### References:
Tan T, Strout ZA, Xia H, Orban M, Shull PB, “Magnetometer-Free, IMU-Based Foot Progression Angle Estimation for Real-Life Walking Conditions,” IEEE Trans Neural Syst Rehabil Eng, vol. PP 10.1109/TNSRE.2020.3047402. 25 Dec. 2020.

## Description of Data in Downloaded File
- time (sec): time since trial start
- Step_Count: steps of walking
- Gait_Phase: gait phase of either left foot or the right foot as selected in the app configuration. 
  - 0 is “Early stance”; 
  - 1 is “Middle stance” ; 
  - 2 is “Late stance”; 
  - 3 is  “Swing” 
- FPA_This_Step: Foot Progression Angle of this step
- FPA_Feedback_Medial: The feedback state for medial feedback node. 
  - 0 is “feedback off”; 
  - 1 is “feedback on” 
- FPA_Feedback_Lateral : The feedback state for lateral feedback node. 
  - 0 is “feedback off”; 
  - 1 is “feedback on” 
- SensorIndex: index of raw sensor data
- AccelX/Y/Z (m/s^2): raw acceleration data
- GyroX/Y/Z (deg/s): raw gyroscope data
- MagX/Y/Z (μT): raw magnetometer data
- Quat1/2/3/4: quaternion data (Scaler first order)
- Sampletime: timestamp of the sensor value
- Package: package number of the sensor value