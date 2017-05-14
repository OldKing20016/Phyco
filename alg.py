'''This is the math processing module of PhycoE. In normal cases, you shouldn't invoke this directly'''
import math
import error

class vector():
	"""define a vector in cartesian (rec) cylinder (cyl) or spherical (sph) mode.

	Use '*','+','-' to obtain a scalar product, sum and difference, respectively.
	'dot' and 'cross' method is provided to get inner and outer product of vectors, respectively.
	'trans' method is used for transform an vector from one to another type of coordinate system.
	'angle' method can return the angle between vectors.
	"""
	def __init__(self, a = 0, b = 0, c = 0, mode = 'rec'):

		if mode == 'rec':
			self.x = a
			self.y = b
			self.z = c
		elif mode == 'cyl':
			self.x = a * math.cos(b)
			self.y = a * math.sin(b)
			self.z = c
		elif mode == 'sph':
			self.x = a * math.sin(b) * math.cos(c)
			self.y = a * math.sin(b) * math.sin(c)
			self.z = a * math.cos(b)

	def __mul__(self, scalar):
		return vector(scalar * self.x, scalar * self.y, scalar * self.z)

	def __rmul__(self, scalar):
		return self * scalar

	def __truediv__(self, scalar):
		return vector(self.x / scalar, self.y / scalar, self.z / scalar)

	def dot(self, other):
		return self.x * other.x + self.y * other.y + self.z * other.z

	def cross(self, other):
		m = matrix([['i', 'j', 'k'], self.list(), other.list()])
		x, y, z = m.det(operator = True)
		return vector(x, y, z)

	def __add__(self, other):
		return vector(self.x + other.x, self.y + other.y, self.z + other.z)

	def __sub__(self, other):
		return vector(self.x - other.x, self.y - other.y, self.z - other.z)

	def __abs__(self):
		return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

	def __ge__(self, other):
		# only compares the magnitude
		return abs(self) > abs(other)

	def trans(self, coord = 'pol'):
		if coord == 'pol':
			raise error.UnderConstruction

	def angle(self, other):
		return math.acos(self.dot(other) / abs(self) / abs(other))

	def unitize(self):
		return self / abs(self)

	def list(self):
		return [self.x, self.y, self.z]

	def __str__(self):
		return str(self.list())

	def __len__(self):
		return 3

	def __getitem__(self, index):
		if index == 0:
			return self.x
		elif index == 1:
			return self.y
		return self.z


class matrix():

	def __init__(self, data, immutable = False):
		#=======================================================================
		# define new matrix, data should be a nested list or tuple, with each l-
		# -ist or tuple represents a column vector by default.
		#=======================================================================
		self.col = len(data)
		self.row = len(data[0])
		self.isSquare = self.row == self.col
		if immutable:
			self.data = tuple(data)
		else:
			self.data = data

	def __getitem__(self, *arg):
		if len(arg) == 1:
			return self.__rowSep(arg[0])
		elif len(arg) == 2:
			return self.data[arg[0]][arg[1]]  # !

	def __mul__(self, n):
		# scalar multiplication ------------------------------------------------
		return matrix([[self[r][c] * n for c in range(self.col)] for r in range(self.row)])

	def mul(self):
		# multiplication of matrices ---------------------------------------------
		pass

	def __rowSep(self, ROW):
		row = [self.data[n][ROW] for n in range(self.row)]
		return row

	def det(self, operator = False):
		# determinant of a matrix ------------------------------------------------
		if self.isSquare:
			if operator and self.row == 3:
				temp = []
				for i in range(3):
					ROW = [0, 1, 2]
					ROW.remove(i)
					t = matrix([self.__rowSep(n)[1:] for n in ROW])
					temp.append(t)
				return temp[0].det(), -temp[1].det(), temp[2].det()
			if not operator:
				if self.row == 2:
					return self[0][0] * self[1][1] - self[0][1] * self[1][0]
				else:
					d = 0
					for i in range(self.row):
						ROW = {i for i in range(self.row)}
						ROW.remove(i)
						t = matrix([self.__rowSep(n)[1:] for n in ROW])
						d += t.det()
					return d
			else:
				raise error.MathError('Unexpected type of operation')
		else:
			raise error.MathError('Not a square matrix')

	def transpose(self):
		return matrix([self.__rowSep(n) for n in range(self.row)])

	def __iter__(self):
		for col in self.data:
			yield col

	def __repr__(self):
		A = self.transpose()
		return '\n'.join([str(col).lstrip('[').rstrip(']') for col in A])

class operator():

	def __init__(self):
		pass
