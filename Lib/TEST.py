'''
Created on Dec 21, 2015

@author: yfzheng
'''
'''
import time
class cls():
    def __init__(self):
        __slots__ = ('x',)
        for i in range(10000000):
            self.x = 1

time1 = time.time()
a = cls()
time2 = time.time()
print(time2 - time1)
'''