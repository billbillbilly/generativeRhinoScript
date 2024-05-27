# This script transforms randomly generated surfaces from a given surface to pipes tower.
# First, an input surface is used to generate surfaces based on uv point matrix.
# These surfaces are ramdomly trimmed to create new scaled surfaces.
# Then, slope, area, centroid, vertexes, and GUID are save in different lists.
# Slopes in list are sorted from smallest to largest.
# finally, the surface is recognized and relocated one by one based on slope.
# The surface is transformed to circle based on four vertexes.
# The circle is also scale by factor calculated by slope and area.
# Each circle is used to create a pipe whose diameter is based on slope again.

import rhinoscriptsyntax as rs
import math
import random

class surfaceStructure(object):
    def __init__(self, surface = None):
        self.surface = surface
        self.pointMatrix = {}
    # setup domain and step
    def surfaceParameter(self, u_number, v_number):
        self.u_number = u_number
        self.v_number = v_number
        self.u_domain = rs.SurfaceDomain(self.surface, 0)
        self.v_domain = rs.SurfaceDomain(self.surface, 1)
        self.u_step = (self.u_domain[1]-self.u_domain[0])/u_number
        self.v_step = (self.v_domain[1]-self.v_domain[0])/v_number
        return self
    # get point matrix from surface
    def setupPointVector(self):
        for i in range(self.u_number+1):
            for j in range(self.v_number+1):
                u = self.u_domain[0] + i*self.u_step
                v = self.v_domain[0] + j*self.v_step
                self.pointMatrix[(i,j)] = rs.EvaluateSurface(self.surface, u, v)
                vec = rs.VectorUnitize(rs.SurfaceNormal(self.surface, (u, v)))
        return self
    # setup a series of surfaces based on point matrix
    def setupSurface(self):
        self.surfaces = []
        for i in range(self.u_number+1):
            for j in range(self.v_number+1):
                if i > 0 and j > 0:
                    self.surfaces += [rs.AddSrfPt((self.pointMatrix[(i,j)], self.pointMatrix[(i,j-1)],
                                                   self.pointMatrix[(i-1,j-1)], self.pointMatrix[(i-1,j)]))]
        return self
    # process surface structure
    class SrfData:
        def __init__(self, surfaceID):
            # the information of a series of geometries
            self.surfaceID = surfaceID
            self.domain_u = list(rs.SurfaceDomain(surfaceID, 0))
            self.domain_v = list(rs.SurfaceDomain(surfaceID, 1))
        # randomly scaled surface based on domain
        def randomScale(self):
            scale_0 = random.uniform(0.55, 0.95)
            scale_1 = random.uniform(0.55, 0.95)
            self.domain_u[0] = (self.domain_u[1] - self.domain_u[0]) * scale_0
            self.domain_u[1] = (self.domain_u[1] - self.domain_u[0]) * scale_1
            self.domain_v[0] = (self.domain_v[1] - self.domain_v[0]) * scale_0
            self.domain_v[1] = (self.domain_v[1] - self.domain_v[0]) * scale_1
            self.surface = rs.TrimSurface(self.surfaceID, 2, (self.domain_u, self.domain_v))
            self.centroid = rs.SurfaceAreaCentroid(self.surface)[0]
            self.area = rs.Area(self.surface)
            rs.HideObject(self.surfaceID)
            return self

        def getSlope(self):
            edges = rs.DuplicateEdgeCurves(self.surface)
            self.vertex = [] # save four vertexes of surface
            # get four vertexes of surface
            for each in edges:
                self.vertex += [rs.CurveEndPoint(each)]
            # list heights of four vertexes
            heights = [self.vertex[0][2], self.vertex[1][2], self.vertex[2][2], self.vertex[3][2]]
            # calculate the largest slope
            self.slope = max(heights) - min(heights)
            rs.DeleteObjects(edges)
            return self

        # reorgnize geometry based on area
        def reorgnize(self, slopes):
            for i in range(len(slopes)):
                # recognize surace by slope
                if self.slope == slopes[i]:
                    translation = ((0 - self.centroid[0]),
                                   (0 - self.centroid[1]),
                                   (i*20 - self.centroid[2]))
                    # move surface and its vertexes
                    rs.MoveObject(self.surface, translation)
                    rs.MoveObjects(self.vertex, translation)
                    # create circle based on vertexes
                    self.circle = rs.AddCurve(self.vertex+[self.vertex[0]])
                    # scale circle based on area
                    factor = math.sqrt(self.area)/(self.slope+1)**2 + 1
                    centroid = rs.SurfaceAreaCentroid(self.surface)[0]
                    rs.ScaleObject(self.circle, centroid, (factor,factor,factor))
                    # create pipe based on circle and
                    rs.AddPipe(self.circle, 0, 1.5*math.sqrt(self.slope))
                    rs.HideObject(self.surface)
            return self

def main():
    # select a surface in rhino space
    srfGUID = rs.GetObject(message="select a surface")
    # input the number of point on uv direction
    u_number = rs.GetInteger(message="set the number of point on u direction",
                             number=5)
    v_number = rs.GetInteger(message="set the number of point on v direction",
                             number=5)
    # setup initial surface
    srfs = surfaceStructure(srfGUID).surfaceParameter(u_number, v_number).setupPointVector().setupSurface().surfaces
    srf_member = [] # save each surface from initial surface
    slope_member = []
    # save surface geberated from point matrix on initial surface
    for i in range(len(srfs)):
        srf_member += [surfaceStructure().SrfData(srfs[i]).randomScale().getSlope()]
        slope_member += [srf_member[i].slope]
    # delete initial surface
    rs.DeleteObject(srfGUID)
    # sort slope from smallest to largest
    slope_member.sort()
    #slope_member.reverse()
    # reorgnize members
    for each in srf_member:
        each.reorgnize(slope_member)

main()
