import rhinoscriptsyntax as rs
import math
import random

class structureSystem():
    def __init__(self, radius, times):
            self.radius = radius # radius of a circle for create triangle
            self.times = times # times of tringale crack recursion
            self.count = 1
            self.triangle = None
            self.surfaceList = []
            self.surfaces = []
            self.surfaces2 = []
            self.original_branch = []
            ### call functions ###
            # create crack surfaces
            self.setuptriangle() # initialize triangle
            # crack triangle
            surfaceSyetem(self.triangle, self.surfaceList, self.surfaces,
                          self.surfaces2, self.count, self.times)
            # ser up inital branch
            self.setupLine()
            # create branch structure
            self.branchStructure()

    # set up a triangle
    def setuptriangle(self):
        cir = rs.AddCircle((0,0,0), self.radius)
        ver = rs.DivideCurve(cir, 3, return_points = True)
        rs.DeleteObject(cir)
        self.triangle = rs.AddSrfPt(ver)

    # set up first line for branch
    def setupLine(self):
        plane = rs.WorldXYPlane()
        for srf in self.surfaces2:
            centroid = rs.SurfaceAreaCentroid(srf)[0]
            groundPt = rs.PlaneClosestPoint(plane, centroid)
            distance = rs.Distance(centroid, groundPt)
            upperPt = (groundPt[0], groundPt[1], groundPt[2]+distance/2)
            self.original_branch += [rs.AddLine(groundPt, upperPt)]

    # branch recursion
    def branchStructure(self):
        branchSystem(self.original_branch, self.surfaces)
        material_index = []
        for i in self.surfaces:
            material_index += [rs.AddMaterialToObject(i)]
            borderCurves = rs.DuplicateEdgeCurves(i)
            for crv in borderCurves:
                rs.AddPipe(crv, 0, 0.5)
        for i in material_index:
            rs.MaterialColor(i, (255, 219, 249))
            rs.MaterialTransparency(i, 0.42)
        rs.AddObjectsToGroup(self.surfaces, rs.AddGroup("srf"))
        # delete some unecessary objects
        rs.DeleteObjects(self.surfaceList)
        rs.DeleteObject(self.triangle)

class surfaceSyetem:
    def __init__(self, triangle, surfaceList, surfaces, surfaces2, count, times):
        self.srf = triangle
        self.times = times
        self.count = count
        self.triangleCrack(surfaceList, surfaces, surfaces2)
    # Recursion of triangle crack
    def triangleCrack(self, surfaceList, surfaces, surfaces2):
            # Get border of input triangle
            borderCurves = rs.DuplicateEdgeCurves(self.srf)
            cornerPts = [] # save vertex of triangle
            Pts = [] # save middle point for each border
            for crv in borderCurves:
                # Get middle point
                mPt = rs.CurveMidPoint(crv)
                # Get surface normal on middle point
                vector = rs.SurfaceNormal(self.srf, (0,0))
                vector = rs.VectorUnitize(vector)
                vector = rs.VectorScale(vector, math.sqrt(rs.CurveLength(crv))*3)
                newPt = rs.PointAdd(vector, mPt)
                cornerPts += [rs.CurveEndPoint(crv)]
                Pts += [newPt]
            # create new surfaces
            srf1 = [rs.AddSrfPt((Pts[2], Pts[0], Pts[1]))]
            srf2 = [rs.AddSrfPt((Pts[0], cornerPts[0], Pts[1]))]
            srf3 = [rs.AddSrfPt((Pts[1], cornerPts[1], Pts[2]))]
            srf4 = [rs.AddSrfPt((Pts[2], cornerPts[2], Pts[0]))]
            # save new surdaces
            if self.count < self.times:
                surfaceList += [srf1]
                surfaceList += [srf2]
                surfaceList += [srf3]
                surfaceList += [srf4]
            else:
                surfaces += [srf1]
                surfaces += [srf2]
                surfaces += [srf3]
                surfaces += [srf4]
                surfaces2 += [srf1]
            # Delete border
            rs.DeleteObjects(borderCurves)
            if self.count < self.times:
                surfaceSyetem(srf1, surfaceList, surfaces, surfaces2, self.count + 1, self.times)
                surfaceSyetem(srf2, surfaceList, surfaces, surfaces2, self.count + 1, self.times)
                surfaceSyetem(srf3, surfaceList, surfaces, surfaces2, self.count + 1, self.times)
                surfaceSyetem(srf4, surfaceList, surfaces, surfaces2, self.count + 1, self.times)

# attach branch structure to crack surfaces
class branchSystem():
    def __init__(self, branches, surfaces):
        self.inputbranches = branches
        self.inputsurfaces = surfaces
        self.branch_list = []
        self.branch = []
        # call functions
        for l in self.inputbranches:
            # create pipe from original line
            self.branch += [rs.AddPipe(l, 0, 0.5)]
            self.count_num = 1
            firstEndPt = rs.CurveEndPoint(l)
            firstAttrSrf = self.closestSrf(firstEndPt)
            # branch recursion
            self.add3Dbranch(l, firstAttrSrf)
        # create pipe for each branch
        for each in self.branch_list:
            self.branch += [rs.AddPipe(each, 0, 0.5)]
        rs.AddObjectsToGroup(self.branch, rs.AddGroup("branch"))
        rs.DeleteObjects(self.branch_list)

    # find closest triangle surface from endpoint of branch
    def closestSrf(self, endPt):
        distance = []
        closest_srf = {}
        for srf in self.inputsurfaces:
            para = rs.SurfaceClosestPoint(srf, endPt)
            closest_pt = rs.EvaluateSurface(srf, para[0], para[1])
            distance += [rs.Distance(endPt, closest_pt)]
            closest_srf[rs.Distance(endPt, closest_pt)] = srf
        distance = min(distance)
        closest_surface = closest_srf[distance]
        return closest_surface

    # randomly get point in cone zone
    def RandomPointInCone(self, origin, direction, rotate_angle):
        #define parameters
        minDist = 15
        maxDist = 30
        maxAngle = 70
        #unitize input direction vector
        vecBranch = rs.VectorUnitize(direction)
        #scale input direction vector - within working cone
        vecBranch = rs.VectorScale(vecBranch, minDist + (maxDist - minDist))
        #find mutation plane
        MutationPlane = rs.PlaneFromNormal(origin, vecBranch)
        #rotate branch around y-axis of mutation plane
        vecBranch = rs.VectorRotate(vecBranch, maxAngle, MutationPlane[1])
        #rotate branch around direction vector
        vecBranch1 = rs.VectorRotate(vecBranch, rotate_angle, direction)
        #return new point location for branch
        return rs.PointAdd(origin, vecBranch1)

    def attractSrf(self, line, attrSrf):
        # Get border of input triangle
        borderCurves = rs.DuplicateEdgeCurves(attrSrf)
        cornerPts = [] # save vertex of triangle
        for border in borderCurves:
            cornerPts += [rs.CurveEndPoint(border)]
        #find startPt and endPt of line
        endPt = rs.CurveEndPoint(line)
        #create new branch
        newLine1 = rs.AddLine(endPt,cornerPts[0])
        newLine2 = rs.AddLine(endPt,cornerPts[1])
        newLine3 = rs.AddLine(endPt,cornerPts[2])
        # delete boundary line
        rs.DeleteObjects(borderCurves)
        return newLine1, newLine2, newLine3

    # add branch
    def add3Dbranch(self, crv, attrSrf):
        # random scales
        scale = (.75, .75, .75)
        # rotate angles
        rotate_angles = [120, 240, 360]
        # start and end points of input curve
        if rs.IsCurve(crv):
            # translation
            translation = rs.CurveEndPoint(crv) - rs.CurveStartPoint(crv)
            # duplicate curves
            crv1 = rs.CopyObject(crv, translation)
            crv2 = rs.CopyObject(crv, translation)
            crv3 = rs.CopyObject(crv, translation)
            # get start point
            stPt1 = rs.CurveStartPoint(crv1)
            stPt2 = rs.CurveStartPoint(crv2)
            stPt3 = rs.CurveStartPoint(crv3)
            # scale duplicated curve
            rs.ScaleObject(crv1, stPt1, scale)
            rs.ScaleObject(crv2, stPt2, scale)
            rs.ScaleObject(crv3, stPt3, scale)
            # find vector of curve
            vector1 = rs.VectorCreate(rs.CurveEndPoint(crv1), stPt1)
            vector2 = rs.VectorCreate(rs.CurveEndPoint(crv2), stPt2)
            vector3 = rs.VectorCreate(rs.CurveEndPoint(crv3), stPt3)
            # find random point in cone based on branchs
            pt1 = self.RandomPointInCone(stPt1, vector1, rotate_angles[0])
            pt2 = self.RandomPointInCone(stPt2, vector2, rotate_angles[1])
            pt3 = self.RandomPointInCone(stPt3, vector3, rotate_angles[2])
            # create branchs
            branch1 = rs.AddLine(stPt1, pt1)
            branch2 = rs.AddLine(stPt2, pt2)
            branch3 = rs.AddLine(stPt3, pt3)
            # get end point of branch
            EndPt1 = rs.CurveEndPoint(branch1)
            EndPt2 = rs.CurveEndPoint(branch2)
            EndPt3 = rs.CurveEndPoint(branch3)
            # find the closest surface
            attrSrf1 = self.closestSrf(EndPt1)
            attrSrf2 = self.closestSrf(EndPt2)
            attrSrf3 = self.closestSrf(EndPt3)
            # attract branch by closest surface after several iteratoins
            if self.count_num == 1:
                attrSrf1 = self.closestSrf(EndPt1)
                attrSrf2 = self.closestSrf(EndPt2)
                attrSrf3 = self.closestSrf(EndPt3)
                newLine1, newLine2, newLine3 = self.attractSrf(branch1, attrSrf1)
                newLine4, newLine5, newLine6 = self.attractSrf(branch2, attrSrf2)
                newLine7, newLine8, newLine9 = self.attractSrf(branch3, attrSrf3)
                self.branch_list += [newLine1, newLine2, newLine3,
                                     newLine4, newLine5, newLine6,
                                     newLine7, newLine8, newLine9]
            self.branch_list += [branch1]
            self.branch_list += [branch2]
            self.branch_list += [branch3]
            # delete duplicate curves
            rs.DeleteObjects((crv1, crv2, crv3))
            self.count_num += 1
            if self.count_num <= 1:
                self.add3Dbranch(branch1, attrSrf1)
                self.add3Dbranch(branch2, attrSrf2)
                self.add3Dbranch(branch3, attrSrf3)

def main():
    # set radius of a circle for creating triangle
    radius = rs.GetInteger(message="set radius for a circle", number=200)
    # set times of recursion
    times = rs.GetInteger(message="set times of recursion (must be larger than 2)", number=3)
    structureSystem(radius, times)

main()
