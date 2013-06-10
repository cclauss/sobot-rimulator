#!/usr/bin/python
# -*- Encoding: utf-8 -*

from math import *

from utils import linalg2_util as linalg
from utils import math_util

class AvoidObstaclesController:

  def __init__( self, supervisor ):
    # bind the supervisor
    self.supervisor = supervisor

    # sensor placements
    self.proximity_sensor_placements = supervisor.proximity_sensor_placements()

    # sensor gains (weights)
    self.sensor_gains = [   1.0-( (0.7*abs(p.theta)) / pi )   for p in supervisor.proximity_sensor_placements() ]

    # control gains
    self.kP = 10.0
    self.kI = 0.0
    self.kD = 0.0
    
    # stored values - for computing next results
    self.prev_time = 0.0
    self.prev_eP = 0.0
    self.prev_eI = 0.0

    # additional calculated values 
    self.obstacle_vectors = [ [ 0.0, 0.0 ] ] * len( self.proximity_sensor_placements )
    self.heading_vector = [ 0.0, 0.0 ]

  def execute( self ):
    # generate and store new heading and obstacle vectors
    self.heading_vector, self.obstacle_vectors = self.calculate_heading_vector()

    # calculate the time that has passed since the last control iteration
    current_time = self.supervisor.time()
    dt = current_time - self.prev_time

    # calculate the error terms
    theta_d = atan2( self.heading_vector[1], self.heading_vector[0] )
    eP = theta_d
    eI = self.prev_eI + eP*dt
    eD = ( eP - self.prev_eP ) / dt

    # calculate angular velocity
    omega = self.kP * eP + self.kI * eI + self.kD * eD
    
    # calculate translational velocity
    # velocity is v_max when omega is 0,
    # drops rapidly to zero as |omega| rises
    v = self.supervisor.v_max() / ( abs( omega ) + 1 )**2

    # store values for next control iteration
    self.prev_time = current_time
    self.prev_eP = eP
    self.prev_eI = eI

    self.supervisor.set_outputs( v, omega )

    # === FOR DEBUGGING ===
    # self._print_vars( eP, eI, eD, v, omega )

  # return a obstacle avoidance vector in the robot's reference frame
  # also returns vectors to detected obstacles in the robot's reference frame
  def calculate_heading_vector( self ):
    # initialize vector
    obstacle_vectors = [ [ 0.0, 0.0 ] ] * len( self.proximity_sensor_placements )
    heading_vector = [ 0.0, 0.0 ]             

    # get the distances indicated by the robot's sensor readings
    sensor_distances = self.supervisor.proximity_sensor_real_distances()

    # calculate the position of detected obstacles and find an avoidance vector
    robot_pos, robot_theta = self.supervisor.estimated_pose().vunpack()
    for i in range( len( sensor_distances ) ):
      # calculate the position of the obstacle
      sensor_pos, sensor_theta = self.proximity_sensor_placements[i].vunpack()
      vector = [ sensor_distances[i], 0.0 ]
      vector = linalg.rotate_and_translate_vector( vector, sensor_theta, sensor_pos )
      obstacle_vectors[i] = vector   # store the obstacle vectors in the robot's reference frame
       
      # accumluate the heading vector within the robot's reference frame
      heading_vector = linalg.add( heading_vector,
                                   linalg.scale( vector, self.sensor_gains[i] ) )

    return heading_vector, obstacle_vectors


  def _print_vars( self, eP, eI, eD, v, omega ):
    print "\n\n"
    print "=============="
    print "ERRORS:"
    print "eP: " + str( eP )
    print "eI: " + str( eI )
    print "eD: " + str( eD )
    print ""
    print "CONTROL COMPONENTS:"
    print "kP * eP = " + str( self.kP ) + " * " + str( eP )
    print "= " + str( self.kP * eP )
    print "kI * eI = " + str( self.kI ) + " * " + str( eI )
    print "= " + str( self.kI * eI )
    print "kD * eD = " + str( self.kD ) + " * " + str( eD )
    print "= " + str( self.kD * eD )
    print ""
    print "OUTPUTS:"
    print "omega: " + str( omega )
    print "v    : " + str( v )
