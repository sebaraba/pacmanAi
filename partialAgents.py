# partialAgent.py
# parsons/15-oct-2017
#
# Version 1
#
# The starting point for CW1.
#
# Intended to work with the PacMan AI projects from:
#
# http://ai.berkeley.edu/
#
# These use a simple API that allow us to control Pacman's interaction with
# the environment adding a layer on top of the AI Berkeley code.
#
# As required by the licensing agreement for the PacMan AI we have:
#
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
#
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@ cs.berkeley.edu).

# The agent here is was written by Simon Parsons, based on the code in
# pacmanAgents.py

from pacman import Directions
from game import Agent
import api
import random
import game
import util
from util import manhattanDistance

#My agent is trying to beat the ghosts using the following methods:
# - [__init__] + [final] methods;
# - [getAction] >> which runs at each move. It calls the methods I defined to help me:
# - [createMap, printMap] >> they help me build a pac man map using the walls positions and print it
# - [updatePosition] >> which updates visited places in my map
# - [switchIndexes] >> which helps me search on my map and on the pacman env. easier.
# - [memorizeGhosts] >> saves the ghosts positions
# - [sovleLoop] >> prevents pac man from looping back and forth
# - [pickMove] >> based on the score each move has and whether there is food on the line or colomn picks a move
# - [checkForFood] >> check on line and col. from my position if there is food
# - [checkForGhosts] >> when I see ghosts, check whether a moves takes me closer to a ghost
# - [checkForCapsules] >> checks if I ate a capsule and starts the countdown

class PartialAgent(Agent):

    # My constructor defines 4 state variables:
    # - [self.last] >> keeps track of my last direciton
    # - [self.pos] >> keeps track of my last positions
    # - [self.capsules] >> keeps track of the capsules
    # - [self.ghosts] >> a list storing the positions of ghosts
    def __init__(self):
        self.last = None
        self.pos = (0,0)
        self.capsule = (0,0)
        self.ghosts = [(0,0)]


    # After each game is finished I need to rebuild
    # My 2d array and set the state variables to the initial value
    def final(self, state):
        walls = api.walls(state)
        width, height = api.corners(state)[-1]
        self.last = None
        self.createMap(walls, width + 1, height + 1)
        self.pos = (0,0)
        self.capsule = (0,0)
        self.ghosts = [(0,0)]
        food = api.food(state)



    # [getAction] is used to move my pac man on the map.
    # It takes self and state as parameters.
    # First if the map isn't created I add it to the state
    # Then if there are ghosts I memorize their postion
    # The algorithm erases any move that takes me closer to a
    # ghost if it exists. Finally I pick the most best move I have
    # and update the position in my 2d array.
    def getAction(self,state):
        walls = api.walls(state)
        width,height = api.corners(state)[-1]
        legal = api.legalActions(state)
        me = api.whereAmI(state)
        food = api.food(state)
        ghosts = api.ghosts(state)
        capsules = api.capsules(state)
        direction = Directions.STOP
        x, y = me

        if not hasattr(self, 'map'):
            self.createMap(walls, width + 1, height + 1)

        self.checkForCapsules(capsules, legal, ghosts)
        legal = self.solveLoop(ghosts, legal)

        if len(ghosts):
            self.memorizeGhosts(ghosts)
            if self.counter < 0:
                for ghost in ghosts:
                    legal = self.checkForGhosts(ghost, me, legal)

        direction = self.pickMove(me, legal, width  + 1, height + 1, food)
        self.updatePosition(me, 1, self.map)


        self.printMap(self.map)


        self.last = direction
        return direction

    # I use this function to build a 2d array
    # that imitates the map. This array helps me
    # diced which move is better to take in each state
    # At the begging if there is a wall on the map I
    # mark it with -1 and 0 otherwise
    def createMap(self, walls, width, height):
        self.map = [[0] * width for i in range(height)]
        for i in range(width):
            for j in range(height):
                if (i, j) in walls:
                    self.updatePosition((i,j), -1, self.map)

    # I used this for debuging purposes
    # it just prints my 2d array
    def printMap(self, harta):
        for x in reversed(harta):
            print x

    # This method increments the postion(in my map) where pac man
    # has walking on.
    def updatePosition(self, pos, val, harta):
        col,line = pos
        harta[line][col] += val

    # I need to switch coordinates (x, y) -> (y, x)
    # in order to connect perfectly my map with pac man's map
    def switchIndexes(self, location):
        x, y = location
        return (y,x)

    # When I see a ghost I store its position
    # This helps me when I whant to check if I have
    # "super powers" but I already eate the ghost
    def memorizeGhosts(self, ghosts):
        for g in ghosts:
            x, y = g
            x = int(x)
            y = int(y)
            self.ghosts.append((x,y))

    # When There are no ghosts I erase from legal the
    # move that takes me back to the position I've just between
    # Sometimes it used to create an infinite loop between SOUTH and NORTH
    # I am not sure why tho. This is the best solution I managed to come up with.
    def solveLoop(self, ghosts, legal):
        if len(ghosts) == 0:
            for l in legal:
                if self.last == Directions.REVERSE[l]:
                    legal.remove(l)
        return legal

    # [pickMove] gets the location where the pac man currently is,
    # a list of legal moves and the width, height of the map.
    # It checks for each move in legal whether the value on the postion
    # it takes the pac man to is smaller than the previouse legal move.
    # In other words, it checks which "road" was least visited. If it finds a
    # postion with value 0(food) in the legal moves it picks it and breaks.
    # If there is no food near me, I use checkForFood to see if I can find food
    # On the line or the col. If there is food I pick that move.
    # Finally I returne a direction
    def pickMove(self, location, legal, width, height, food):
        x,y = self.switchIndexes(location)
        minimum = 9999
        direction = Directions.STOP

        for l in legal:
            if l == Directions.WEST:
                value = self.map[x][y - 1]
                pos = (x, y - 1)
                if value == 0:
                    if self.switchIndexes(pos) not in food:
                        if len(food):
                            print pos, 'possss', food, 'foood', 'ON WEST'
                            self.map[x][y-1] = -1

                if value  < minimum:
                    self.pos = pos
                    minimum = value
                    direction = Directions.WEST
                    if value == 0:
                        break

                if self.checkForFood(pos, width, height):
                    direction = Directions.WEST
                    self.pos = pos


            if l == Directions.EAST:
                value = self.map[x][y + 1]
                pos = (x, y + 1)
                if value == 0:
                    if self.switchIndexes(pos) not in food:
                        if len(food):
                            print pos, 'possss', food, 'foood', 'ON EAST'
                            self.map[x][y+1] = -1

                if value < minimum:
                    self.pos = pos
                    minimum = value
                    direction = Directions.EAST
                    if value == 0:
                        break

                if self.checkForFood(pos, width, height):
                    direction = Directions.EAST
                    self.pos = pos



            if l == Directions.SOUTH:
                value = self.map[x - 1][y]
                pos = (x - 1, y)
                if value == 0:
                    if self.switchIndexes(pos) not in food:
                        if len(food):
                            print pos, 'possss', food, 'foood', 'ON SOUTH'
                            self.map[x - 1][y] = -1

                if value < minimum:
                    self.pos = pos
                    minimum = value
                    direction = Directions.SOUTH
                    if value == 0:
                        break

                if self.checkForFood(pos, width, height):
                    direction = Directions.SOUTH
                    self.pos = pos



            if l == Directions.NORTH:
                value = self.map[x + 1][y]
                pos = (x + 1, y)
                if value == 0:
                    if self.switchIndexes(pos) not in food:
                        if len(food):
                            print pos, 'possss', food, 'foood', 'ON SOUTH'
                            self.map[x+1][y] = -1
                if value < minimum:
                    self.pos = pos
                    minimum = value
                    direction = Directions.NORTH
                    if value == 0:
                        break

                if self.checkForFood(pos, width, height):
                    direction = Directions.NORTH
                    self.pos = pos


        return direction


    # This method takes my location and the width,height of the map.
    # Then it searches in my 2d array to see if it can find food
    # on the col or line pac man is. If it finds food it returns true.
    # However if it finds a wall without finding any food it stops searching
    # in that direction.
    def checkForFood(self, location, width, height):
        x, y = location

        for i in range(y - 1, 0, -1):
            value = self.map[x][i]
            if value == -1:
                break
            elif value == 0:
                return True

        for i in range(y + 1, width):
            value = self.map[x][i]
            if value == -1:
                break
            elif value == 0:
                return True

        for i in range(x - 1, -1, -1):
            value = self.map[i][y]
            if value == -1:
                break
            elif value == 0:
                return True

        for i in range(x + 1, height):
            value = self.map[i][y]
            if value == -1:
                break
            elif value == 0:
                return True

        return False

    # This method takes my location, the legal moves and the ghosts locations
    # and checks whether a move that is legal to take, will decrease the distance
    # between me and any of the ghosts. If I find such a legal move then I erase it from
    # the legal moves and pas the rest of the list further
    def checkForGhosts(self, ghost, me, legal):
        x, y = ghost
        l, c = me
        distance1 = manhattanDistance(ghost, me)
        if distance1 <= 2:
            for direction in legal:
                if direction == Directions.WEST:
                    if manhattanDistance((l - 1, c), ghost) < distance1:
                        legal.remove(direction)

                if direction == Directions.EAST:
                    if manhattanDistance((l + 1, c), ghost) < distance1:
                        legal.remove(direction)

                if direction == Directions.SOUTH:
                    if manhattanDistance((l, c - 1), ghost) < distance1:
                        legal.remove(direction)

                if direction == Directions.NORTH:
                    if manhattanDistance((l, c + 1), ghost) < distance1:
                        legal.remove(direction)


        return legal

    # This method checks if I ate a capsule
    # If I ate one, I know that there are 35 moves when I can eat ghosts
    # (I found out this by using a raw_input() inside my code and counting
    # how many enters I needed untill the "super powers" were gone)
    # The counter decrements by one each time I make a move.
    # I didn't know how to keep track of which ghost I ate so if I eat one I
    # reset the counter to -1 in order to dodge both of them.
    def checkForCapsules(self, capsules, legal, ghosts):
        if not hasattr(self, 'counter'):
            self.counter = -1
        if len(capsules):
            self.capsule = self.switchIndexes(capsules[0])



        if self.capsule != (0,0):
            if self.pos == self.capsule:
                self.counter = 35
                self.capsule = (0,0)
        if self.counter >= 0:
            self.counter -= 1
        if self.switchIndexes(self.pos) in self.ghosts and self.pos != (0,0):
            self.counter = -1


    def computeScore(self, legal):
        for l in legal:
            if direction == Directions.WEST:
                if manhattanDistance((l - 1, c), ghost) < distance1:
                    legal.remove(direction)

            if direction == Directions.EAST:
                if manhattanDistance((l + 1, c), ghost) < distance1:
                    legal.remove(direction)

            if direction == Directions.SOUTH:
                if manhattanDistance((l, c - 1), ghost) < distance1:
                    legal.remove(direction)

            if direction == Directions.NORTH:
                if manhattanDistance((l, c + 1), ghost) < distance1:
                    legal.remove(direction)
