import rhinoscriptsyntax as rs
import ghpythonlib.components as ghc
import scriptcontext as sc
import Rhino
import math
import random

class Agent(object):
    #initilize data in class
    def __init__(self, point, coord, vec):
        #initialize agent data
        self.ptID = point
        self.pos = coord
        self.vector = vec
        self.trailPts = []
        self.trailPts += [self.pos]
        self.curveID = None

    # find out the closest mesh
    def detectMesh(self, mesh):
        distances = []
        closestMesh = {}
        for each in mesh:
            ptData = ghc.MeshClosestPoint(self.ptID, each)
            distance = rs.Distance(ptData[0], self.pos)
            distances += [distance]
            closestMesh[distance] = [each, ptData[0]]
        distance = min(distances)
        self.closestMesh = closestMesh[distance]
        return self

    # find the closest agent
    def detectAgent(self, agentPopulation):
        distances = []
        closestAgent = {}
        for agent in agentPopulation:
            distance = rs.Distance(self.pos, agent.pos)
            # select a closest agent within a random distance
            if distance > random.randint(2,20):
                distances += [distance]
                closestAgent[distance] = [agent, distance]
        distance = min(distances)
        self.closestAgent = closestAgent[distance]
        return self

    def vectorAttract(self):
        # if the closest agent is close enough, change the default vector to push agent toward other agents
        if self.closestAgent[1] > random.randint(5,8) and self.closestAgent[1] < random.randint(9,13) and self.pos[2] > 1:
            direction = rs.AddLine(self.pos, self.closestAgent[0].pos)
            translation = rs.CreatePoint((0,0,1)) - rs.CreatePoint(self.pos)
            rs.MoveObject(direction, translation)
            self.tempVector = rs.VectorCreate(rs.CurveEndPoint(direction), (0,0,0))
            rs.DeleteObject(direction)
            if rs.VectorLength(self.tempVector) >= 1:
                self.tempVector = rs.VectorUnitize(self.tempVector)
        # if agent is too close to each other, push it away from other agents
        elif self.closestAgent[1] <= 5 and self.pos[2] > 1:
            direction = rs.AddLine(self.closestAgent[0].pos, self.pos)
            translation = rs.CreatePoint((0,0,1)) - rs.CreatePoint(self.pos)
            rs.MoveObject(direction, translation)
            self.tempVector = rs.VectorCreate(rs.CurveEndPoint(direction), (0,0,0))
            rs.DeleteObject(direction)
            if rs.VectorLength(self.tempVector) >= 1:
                self.tempVector = rs.VectorUnitize(self.tempVector)
        else:
            self.tempVector = self.vector

    def move(self):
        self.vectorAttract()
        # keep moving upward if agent is far from barriers
        if rs.Distance(self.closestMesh[1], self.pos) > 2 or self.closestMesh[1][2] == self.pos[2]:
            self.pos = rs.PointAdd(self.pos, self.tempVector)
        else: # make agent detour
            # get normal from the closest point on the closest mesh
            self.closestMesh[0].FaceNormals.ComputeFaceNormals()
            fid,mPt = self.closestMesh[0].ClosestPoint(self.closestMesh[1],2)
            meshNormal = self.closestMesh[0].FaceNormals[fid]
            # add vector to the closest point on the closest mesh
            vecPt = rs.PointAdd(self.closestMesh[1], meshNormal)
            # create direction line starting from vector point to ClosestPoint
            # when agent is below half the height of the sphere
            if self.closestMesh[1][2] > self.pos[2]:
                direction = rs.AddLine(self.closestMesh[1], vecPt)
            # when the height of agent is more than half the height of the sphere
            elif self.closestMesh[1][2] < self.pos[2]:
                direction = rs.AddLine(vecPt, self.closestMesh[1])
            startPt = rs.CurveStartPoint(direction)
            # create an elevated point from agent
            pt = (self.pos[0], self.pos[1], self.pos[2]+1/math.sin(math.radians(45)))
            # move direction line to elevated point
            translation = rs.CreatePoint(pt) - startPt
            rs.MoveObject(direction, translation)
            # relocate agent at the end point of moved direction line
            self.pos = rs.CurveEndPoint(direction)
            rs.DeleteObject(direction)
        self.trailPts += [self.pos]
        rs.DeleteObject(self.ptID)
        self.ptID = rs.AddPoint(self.pos)
        return self

    # draw trails
    def drawTrails(self):
        if self.curveID != None:
            rs.DeleteObject(self.curveID)
        self.curveID = rs.AddCurve(self.trailPts)

def main():
    ptNum = rs.GetInteger('how many attractor points?', 60)
    startPtNum = rs.GetInteger('how many streams?', 80)
    steps = rs.GetInteger('How many steps?', 80)

    # moving direction
    vector = (0,0,1)
    spheres = []
    agentPopulation = []

    # setup barrier sphere mesh
    for i in range(ptNum):
        x = random.randrange(5, 45)
        y = random.randrange(5, 45)
        z = random.randrange(5, 80)
        point = (x,y,z) # center point
        radius = random.randrange(3, 10) # random radius
        plane = ghc.XYPlane(rs.AddPoint(point))
        sphere = ghc.MeshSphere(plane, radius)
        spheres += [sphere]

    # convert separate sphere into subD and then convert subD in to mesh
    mesh = ghc.MeshUnion(spheres)
    subD = ghc.SubDfromMesh(mesh)
    meshFSubD = ghc.MeshfromSubD(subD)
    meshIDs = []
    for i in meshFSubD:
        meshIDs += [sc.doc.Objects.AddMesh(i)]

    # setup start points for line structure
    for i in range(startPtNum):
        x = random.randrange(0, 50)
        y = random.randrange(0, 50)
        z = 0
        point = (x,y,z)
        agentPopulation += [Agent(rs.AddPoint(point), point, vector)]

    # call Agent methods
    n = 0
    while n <= steps:
    #while not sc.escape_test():
        n += 1
        for agent in agentPopulation:
            agent.detectMesh(meshFSubD).detectAgent(agentPopulation).move().drawTrails()

main()
