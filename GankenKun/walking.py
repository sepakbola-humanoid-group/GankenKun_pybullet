#!/usr/bin/env python3
#
# generating walking pattern for the GankenKun

import pybullet as p
import numpy as np
from kinematics import *
from foot_step_planner import *
from preview_control import *
from time import sleep
import csv
import matplotlib.pyplot as plt


class walking():
    def __init__(self, RobotId, left_foot0, right_foot0, joint_angles, pc, fsp):
        self.kine = kinematics(RobotId)
        self.left_foot0, self.right_foot0 = left_foot0, right_foot0
        self.joint_angles = joint_angles
        self.pc = pc
        self.fsp = fsp
        self.X = np.matrix([[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]])
        self.pattern = []
        self.left_up = self.right_up = 0.0
        self.left_off, self.left_off_g, self.left_off_d = np.matrix(
            [[0.0, 0.0, 0.0]]), np.matrix([[0.0, 0.0, 0.0]]), np.matrix([[0.0, 0.0, 0.0]])
        self.right_off, self.right_off_g, self.right_off_d = np.matrix(
            [[0.0, 0.0, 0.0]]), np.matrix([[0.0, 0.0, 0.0]]), np.matrix([[0.0, 0.0, 0.0]])
        self.th = 0
        self.status = 'start'
        self.next_leg = 'right'
        self.foot_step = []
        return

    def setGoalPos(self, pos=None):
        if pos == None:
            if len(self.foot_step) <= 4:
                self.status = 'start'
            if len(self.foot_step) > 3:
                del self.foot_step[0]
        else:
            if len(self.foot_step) > 2:
                if not self.status == 'start':
                    offset_y = -0.06 if self.next_leg == 'left' else 0.06
                else:
                    offset_y = 0.0
                current_x, current_y, current_th = self.foot_step[1][
                    1], self.foot_step[1][2] + offset_y, self.foot_step[1][3]
            else:
                current_x, current_y, current_th = 0, 0, 0
            self.foot_step = self.fsp.calculate(
                pos[0], pos[1], pos[2], current_x, current_y, current_th, self.next_leg, self.status)
            print(f"num foot_step: {len(self.foot_step)}")
            self.status = 'walking'
#    print(str(self.foot_step)+'\n')
        t = self.foot_step[0][0]
        self.pattern, x, y = self.pc.set_param(
            t, self.X[:, 0], self.X[:, 1], self.foot_step)
        self.X = np.matrix(
            [[x[0, 0], y[0, 0]], [x[1, 0], y[1, 0]], [x[2, 0], y[2, 0]]])
        if self.foot_step[0][4] == 'left':
            if self.foot_step[1][4] == 'both':
                self.right_off_g = np.matrix(
                    [[self.foot_step[1][1], self.foot_step[1][2], self.foot_step[1][3]]])
            else:
                self.right_off_g = np.matrix(
                    [[self.foot_step[1][1], self.foot_step[1][2] + 0.06, self.foot_step[1][3]]])
            self.right_off_d = (self.right_off_g - self.right_off) / 17.0
            self.next_leg = 'right'
        if self.foot_step[0][4] == 'right':
            if self.foot_step[1][4] == 'both':
                self.left_off_g = np.matrix(
                    [[self.foot_step[1][1], self.foot_step[1][2], self.foot_step[1][3]]])
            else:
                self.left_off_g = np.matrix(
                    [[self.foot_step[1][1], self.foot_step[1][2] - 0.06, self.foot_step[1][3]]])
            self.left_off_d = (self.left_off_g - self.left_off) / 17.0
            self.next_leg = 'left'
        self.th = self.foot_step[0][3]
        return self.foot_step

    def getNextPos(self):
        X = self.pattern.pop(0)
        period = round((self.foot_step[1][0] - self.foot_step[0][0]) / 0.01)
        self.th += (self.foot_step[1][3] - self.foot_step[0][3]) / period
        x_dir = 0
        BOTH_FOOT = round(0.17 / 0.01)
        start_up = round(BOTH_FOOT / 2)
        end_up = round(period / 2)
        period_up = end_up - start_up
        foot_hight = 0.06
        if self.foot_step[0][4] == 'right':
            # up or down foot
            if start_up < (period - len(self.pattern)) <= end_up:
                self.left_up += foot_hight / period_up
            elif self.left_up > 0:
                self.left_up = max(self.left_up - foot_hight / period_up, 0.0)
            # move foot in the axes of x,y,the
            if (period - len(self.pattern)) > start_up:
                self.left_off += self.left_off_d
                if (period - len(self.pattern)) > (start_up + period_up * 2):
                    self.left_off = self.left_off_g.copy()
        if self.foot_step[0][4] == 'left':
            # up or down foot
            if start_up < (period - len(self.pattern)) <= end_up:
                self.right_up += foot_hight / period_up
            elif self.right_up > 0:
                self.right_up = max(
                    self.right_up - foot_hight / period_up, 0.0)
            # move foot in the axes of x,y,the
            if (period - len(self.pattern)) > start_up:
                self.right_off += self.right_off_d
                if (period - len(self.pattern)) > (start_up + period_up * 2):
                    self.right_off = self.right_off_g.copy()
        lo = self.left_off - np.block([[X[0, 0:2], 0]])
        ro = self.right_off - np.block([[X[0, 0:2], 0]])
        left_foot = [self. left_foot0[0] + lo[0, 0], self. left_foot0[1] + lo[0,
                                                                              1], self. left_foot0[2] + self.left_up, 0.0, 0.0, self.th - lo[0, 2]]
        right_foot = [self.right_foot0[0] + ro[0, 0], self.right_foot0[1] + ro[0,
                                                                               1], self.right_foot0[2] + self.right_up, 0.0, 0.0, self.th - ro[0, 2]]
        print("left foot: \n", left_foot)
        print("right foot: \n", right_foot)
        self.joint_angles = self.kine.solve_ik(
            left_foot, right_foot, self.joint_angles)
        xp = [X[0, 0], X[0, 1]]
        zp = [X[0, 2], X[0, 3]]

        return self.joint_angles, left_foot, right_foot, xp, zp, len(self.pattern)


if __name__ == '__main__':
    TIME_STEP = 0.001
    physicsClient = p.connect(p.GUI)
    p.setGravity(0, 0, -9.8)
    p.setTimeStep(TIME_STEP)

    planeId = p.loadURDF("./URDF/plane.urdf", [0, 0, 0])
    RobotId = p.loadURDF("./URDF/gankenkun.urdf", [0, 0, 0])

    index = {p.getBodyInfo(RobotId)[0].decode('UTF-8'): -1, }
    for id in range(p.getNumJoints(RobotId)):
        index[p.getJointInfo(RobotId, id)[12].decode('UTF-8')] = id

    left_foot0 = p.getLinkState(RobotId, index['left_foot_link'])[0]
    right_foot0 = p.getLinkState(RobotId, index['right_foot_link'])[0]

    joint_angles = []
    for id in range(p.getNumJoints(RobotId)):
        if p.getJointInfo(RobotId, id)[3] > -1:
            joint_angles += [0, ]
    left_foot = [left_foot0[0] - 0.015,
                 left_foot0[1] + 0.01, left_foot0[2] + 0.02]
    right_foot = [right_foot0[0] - 0.015,
                  right_foot0[1] - 0.01, right_foot0[2] + 0.02]

    pc = preview_control(0.01, 1.0, 0.27)
    fsp = foot_step_planner_v1(0.05, 0.03, 0.2, 0.34, 0.06)

    walk = walking(RobotId, left_foot, right_foot, joint_angles, pc, fsp)

    index_dof = {p.getBodyInfo(RobotId)[0].decode('UTF-8'): -1, }
    for id in range(p.getNumJoints(RobotId)):
        index_dof[p.getJointInfo(RobotId, id)[12].decode(
            'UTF-8')] = p.getJointInfo(RobotId, id)[3] - 7

    walk.setGoalPos([0.4, 0.0, 0.0])
    j = 0
    with open('result.csv', mode='w') as f:
        f.write('')
    foot_step = [0, ] * 10
    x_cnt = 0
    torso_pos = []
    zmp_pos = []
    left_foot_pos = []
    right_foot_pos = []
    left_foot_y = []
    fig, axs = plt.subplots(4, 2)
    fig.tight_layout(pad=1.0)
    axs = axs.ravel()

    while p.isConnected():
        j += 1
        if j >= 10:
            joint_angles, lf, rf, xp, zp, n = walk.getNextPos()
            torso_pos.append(xp)
            zmp_pos.append(zp)
            left_foot_pos.append(lf)
            right_foot_pos.append(rf)

            with open('result.csv', mode='a') as f:
                writer = csv.writer(f)
                writer.writerow(np.concatenate([lf, rf, xp]))
            j = 0
            x_cnt += 1
            if n == 0:
                if (len(foot_step) <= 6):
                    foot_step = walk.setGoalPos(
                        [foot_step[0][1] + 0.4, foot_step[0][2] + 0.1, foot_step[0][3] + 0.5])
                    print("send new target *************************")
                else:
                    foot_step = walk.setGoalPos()
                with open('result.csv', mode='a') as f:
                    f.write('\n')
        for id in range(p.getNumJoints(RobotId)):
            qIndex = p.getJointInfo(RobotId, id)[3]
            if qIndex > -1:
                p.setJointMotorControl2(
                    RobotId, id, p.POSITION_CONTROL, joint_angles[qIndex - 7])

        p.stepSimulation()
        if x_cnt > 200:
            break

    torso_pos = np.asarray(torso_pos)
    zmp_pos = np.asarray(zmp_pos)
    left_foot_pos = np.asarray(left_foot_pos).squeeze()
    right_foot_pos = np.asarray(right_foot_pos).squeeze()

    print(torso_pos.shape)
    print(left_foot_pos.shape)
    print(right_foot_pos.shape)

    print(torso_pos[0])
    print(left_foot_pos[0])
    print(right_foot_pos[0])

    axs[0].plot(torso_pos[:, 0], label='Torso X')
    axs[0].plot(zmp_pos[:, 0], label='ZMP X')
    axs[1].plot(torso_pos[:, 1], label='Torso Y')
    axs[1].plot(zmp_pos[:, 1], label='ZMP Y')
    axs[2].plot(left_foot_pos[:, 2], label='Foot Left Z')
    axs[2].plot(right_foot_pos[:, 2], label='Foot Right Z')
    axs[2].legend(loc='upper left', prop={'size': 10})
    axs[3].plot(left_foot_pos[:, 1], label='Foot Left Y')
    axs[3].plot(right_foot_pos[:, 1], label='Foot Right Y')
    axs[3].legend(loc='upper left', prop={'size': 10})
    axs[4].plot(left_foot_pos[:, 0], label='Foot Left X')
    axs[4].plot(right_foot_pos[:, 0], label='Foot Right X')
    axs[4].legend(loc='upper left', prop={'size': 10})
    plt.show()

#    sleep(0.01)
#    sleep(TIME_STEP)
