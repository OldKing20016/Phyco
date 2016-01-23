'''This is a PhycoE module deal with dynamics.
For now, it supports ,specifically, collision detection and 2-D dynamics.'''
import alg
from error import UnderConstruction


class colSolver():
    """A class to deal with various kind of collisions
    """
    def __init__(self, e=1, v=None):
        self.e = e
        self.v = v

    def solve(self):
        self.v += 1
        return


class field():

    def __init__(self, x=0, y=0, z=0, dim=3):
        self.dim = dim
        self.x = compile(str(x), '<string>', mode='eval')
        self.y = compile(str(y), '<string>', mode='eval')
        self.z = compile(str(z), '<string>', mode='eval')
        __slots__ = ('dim', 'x', 'y', 'z')

    def __getitem__(self, index):
        x, y, z = index.x, index.y, index.z
        return alg.vector(eval(self.x), eval(self.y), eval(self.z))

    def __add(self, other):
        return field(eval(self.x) + eval(self.y))
       
    def curl(self, pos):
        return
    
    def grad(self, pos):
        return
    
    def div(self, pos):
        return


class obj():

    def __init__(self, mass=1, initPos=alg.vector(), point=True, mode='rigid',
                 charge=False, initv=alg.vector(), material=None):
        self.mass = mass
        self.ability = False
        self.pos = initPos
        self.mode = mode
        if point:
            self.shape = 0
        if charge:
            self.charge = charge
            self.ability = True
        self.velocity = initv
        self.material = material
        __slots__ = ('velocity', 'mass', 'pos', 'mode',
                     'shape', 'charge', 'material', 'ability')

    def fix(self):
        self.fixed = True

    def shape(self, geom):
        self.shape = geom

    def getforce(self, obj):
        if self.ability:
            return
        return alg.vector()
        raise UnderConstruction


class constraint():
    pass
