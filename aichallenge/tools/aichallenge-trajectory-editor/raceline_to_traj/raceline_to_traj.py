import math
import pandas as pd
import os, tkinter, tkinter.filedialog, tkinter.messagebox
import numpy as np

def euler_from_quaternion(quaternion):
    """
    Converts quaternion (w in last place) to euler roll, pitch, yaw
    quaternion = [x, y, z, w]
    Bellow should be replaced when porting for ROS 2 Python tf_conversions is done.
    """
    x = quaternion.x
    y = quaternion.y
    z = quaternion.z
    w = quaternion.w

    sinr_cosp = 2 * (w * x + y * z)
    cosr_cosp = 1 - 2 * (x * x + y * y)
    roll = np.arctan2(sinr_cosp, cosr_cosp)

    sinp = 2 * (w * y - z * x)
    pitch = np.arcsin(sinp)

    siny_cosp = 2 * (w * z + x * y)
    cosy_cosp = 1 - 2 * (y * y + z * z)
    yaw = np.arctan2(siny_cosp, cosy_cosp)

    return roll, pitch, yaw

def quaternion_from_euler(roll, pitch, yaw):
    """
    Converts euler roll, pitch, yaw to quaternion (w in last place)
    quat = [x, y, z, w]
    Bellow should be replaced when porting for ROS 2 Python tf_conversions is done.
    """
    cy = math.cos(yaw * 0.5)
    sy = math.sin(yaw * 0.5)
    cp = math.cos(pitch * 0.5)
    sp = math.sin(pitch * 0.5)
    cr = math.cos(roll * 0.5)
    sr = math.sin(roll * 0.5)

    q = [0] * 4
    q[0] = cy * cp * cr + sy * sp * sr
    q[1] = cy * cp * sr - sy * sp * cr
    q[2] = sy * cp * sr + cy * sp * cr
    q[3] = sy * cp * cr - cy * sp * sr

    return q

def read_csv_file(file_path):
    """
    header: #がついている行はコメント行として読み飛ばす
    """
    data = pd.read_csv(file_path, comment='#', sep=';')
    return data

def write_csv_file(file_path, data):
    """Headerを付けて保存する
    # x,y,z,x_quat,y_quat,z_quat,w_quat,speed
    """
    header = ['x', 'y', 'z', 'x_quat', 'y_quat', 'z_quat', 'w_quat', 'speed']
    df = pd.DataFrame(data, columns=header)
    df.to_csv(file_path, float_format='%.6f', index=False, sep=',')

def convert_raceline_to_traj(data):
    """
    racelineのデータをtrajectoryのデータに変換する

    racelineの1列目がx座標, 2列目がy座標
    """
    x = []
    y = []
    psi_rad = []
    traj_data = []
    speed = []
    for i in range(len(data)):
        x.append(data.iloc[i, 1])
        y.append(data.iloc[i, 2])
        psi_rad.append(data.iloc[i, 3])
        speed.append(data.iloc[i, 5])
    
    quat = []
    for i in range(len(psi_rad)):
        q = quaternion_from_euler(0, 0, psi_rad[i])
        quat.append(q)
    for i in range(len(x)):
        traj_data.append([x[i], y[i], 0, quat[i][0], quat[i][1], quat[i][2], quat[i][3], speed[i]])
    return traj_data


def main():
    read_file_path = tkinter.filedialog.askopenfilename(filetypes=[('select raceline file', '*.csv')])
    if not read_file_path:
        return
    data = read_csv_file(read_file_path)
    traj_data = convert_raceline_to_traj(data)
    write_file_path = tkinter.filedialog.asksaveasfilename(filetypes=[('save trajectory file', '*.csv')])
    if not write_file_path:
        return
    write_csv_file(write_file_path, traj_data)



if __name__ == '__main__':
    main()

    