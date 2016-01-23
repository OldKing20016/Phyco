"""Physics Simulator by Finite Difference Method (FDM)"""
from itertools import combinations
from error import UnderConstruction
import alg
import mechanics


class event():

    def __init__(self, mode='occurred', *arg):
        if mode == 'occurred':
            pass
        elif mode == 'pass':
            pass


class sim():
    """FDM solver"""

    def __init__(self, *arg, field=None, step=10 ** -2, end=1, var=[]):
        self.objs = arg
        self.__comb = combinations(self.objs, 2)
        self.field = field
        self.step = step
        self.constraints = {}
        self.X = []
        self.V = []
        __slots__ = ('objs', 'comb', 'field', 'step', 'end',
                     'constriants', 'cache', 'X', 'V')

    def start(self, end):
        """
        WARNING: Using dict to store all combinations of two objects,
        data loss would happen when too many objects encountered.
        """
        dt = self.step
        i = int(end / dt)  # number of steps needed
        x = dict(zip(self.objs, [obj.pos for obj in self.objs]))
        v = dict(zip(self.objs, [obj.velocity for obj in self.objs]))
        X = []
        V = []
        X.append(x.copy())
        V.append(v.copy())
        # compute initial distance between each other
        d = dict(zip(self.__comb, [abs(x[comb[0]] - x[comb[1]]) \
                                   for comb in self.__comb]))
        self.cache = (_cache(x), _cache(d))  # initialize cache
        for i in range(i):
            for Obj in self.objs:
                pos = x[Obj]
                try:
                    F = sum([obj.getforce(Obj) for obj in self.objs if obj != Obj])\
                    + self.field[pos]  # compute resultant force
                except:
                    F = alg.vector()
                a = F / Obj.mass
                x[Obj] += (v[Obj] + a * self.step / 2) * dt
                # should have been improved
                v[Obj] += a * dt

            # update distance, preparing for collision check
            d = dict(zip(self.__comb, [abs(x[comb[0]] - x[comb[1]])\
                                       for comb in self.__comb]))
            self.cache[0].append(x)  # push newly computed data to cache
            self.cache[1].append(d)
            D = self.cache[1].diff()  # change of distance
            self.__check(d, D, v, x)

            X.append(x.copy())
            V.append(v.copy())
        self.X = X
        self.V = V

    def __check(self, d, D, v, x):
        # check constraints
        # pass
        # check collision
        for a in self.__comb:  # enumerate to find collision
            # Fixed value 5*dt*v assumes v cannot change 10 times in an interval
            o1, o2 = a[0], a[1]
            if d[a] < max(v[o1], v[o2]) * self.step and D[a] < 0:
                # two bodies are at critical distance, check if they're coplannar
                if self.__isCoplannar(x[o1], x[o2], v[o1], v[o2]):
                    # two trajectories are coplannar, check if they intersect
                    if self.__isIntersect(x[o1], x[o2], self.cache[0][o1], self.cache[0][o2]):
                        # collision detected
                        mechanics.colSolver()
                        self.collisiondetect(d, D, v, x)
                        # WARNING: May encounter infinite loop

    def __isCoplannar(self, point1, point2, d1, d2):
        """Determine if two trajectories are coplannar

        If two segments are coplannar then any segment
        between two points on the lines are in their
        plane and vice versa. It uses scalar triple
        product to check if two segments are coplannar.

        """
        D = point1 - point2
        A = alg.matrix([d1, D, d2])
        if A.det() == 0:
            return True
        return False

    def __isIntersect(self, p1, p2, p3, p4):
        pass

    def __str__(self):
        X = self.X
        for i in X:
            for obj in self.objs:
                i[obj] = i[obj].list()
            i = str(i)
        return str(X)


class _cache():
    """Imitating list to store fixed length of data

    Cache object is list which is intended to store fixed
    number of elements. Assignment or appending elements
    to saturated cache would replace the first one. It's
    not been optimized to store large amount of data. All
    of your input data should be externally verified to
    be of the same length.

    """

    def __init__(self, iterable, l=2):
        """
        Though the usage of the class is not limited to dict,
        if you want to use this class in other ways, replace this.
        """
        self.__len = l  # NOTE: It's not the length of iterable!
        a = len(iterable)
        self.__list = [None] * (l - a) + list(iterable)
        self.__keys = iterable.keys()

    def append(self, object):
        self.__list.append(object)
        self.__list = self.__list[1:]

    def __iter__(self):
        for i in self.__list:
            yield i

    def __getitem__(self, index):
        pass

    def diff(self):
        """compare objects stored in cache

        Substract last two entry of cache. It won't
        check if two entry are of the same length!
        """
        return {i:self.__list[-1][i] - self.__list[-2][i] for i in self.__keys}
