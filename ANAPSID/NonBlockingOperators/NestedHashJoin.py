'''
NestedHashJoin.py

Implements a depending operator, similar to block nested join and symmetric
hash join

Autor: Gabriela Montoya
Date: July 18th, 2012

'''
from multiprocessing import Queue, Process
from time import time
import string, sys
from Queue import Empty
from ANAPSID.Operators.Join import Join
from ANAPSID.Decomposer.Tree import Leaf, Node
from OperatorStructures import Table, Partition, Record


class NestedHashJoin(Join):

    def __init__(self, vars):
        self.left_table = dict()
        self.right_table = dict()
        self.qresults    = Queue()
        self.vars        = vars

    def instantiate(self, d):
        newvars = self.vars - set(d.keys())
        return NestedHashJoin(newvars)

    def execute(self, left_queue, right_operator, out):

        self.left_queue = left_queue
        self.right_operator = right_operator
        self.qresults = out

        tuple1 = None
        tuple2 = None

        right_queues = dict()

        while (not(tuple1 == "EOF") or (len(right_queues) > 0)):

            # Try to get and process tuple from left queue
            if not(tuple1 == "EOF"):
                try:
                    tuple1 = self.left_queue.get(False)
                    #print "tuple1: "+str(tuple1)
                    instance = self.probeAndInsert1(tuple1, self.right_table,
                                                    self.left_table, time())
                    if instance: # the join variables have not been used to
                                 # instanciate the right_operator

                        new_right_operator = self.makeInstantiation(tuple1,
                                                                    self.right_operator)
                        #print "new op: "+str(new_right_operator)
                        resource = self.getResource(tuple1)
                        queue = Queue()
                        right_queues[resource] = queue
                        p2 = Process(target=new_right_operator.execute, args=(queue,))
                        p2.start()
                except Empty:
                    pass
                except TypeError:
                    # TypeError: in resource = resource + tuple[var], when the tuple is "EOF".
                    pass
                except:
                    print "Unexpected error:", sys.exc_info()[0]
                    #raise
                    pass

            toRemove = [] # stores the queues that have already received all its tuples

            for r in right_queues:
                try:
                    q = right_queues[r]
                    tuple2 = q.get(False)
                    if (tuple2 == "EOF"):
                        toRemove.append(r)
                    else:
                        self.probeAndInsert2(r, tuple2, self.left_table,
                                             self.right_table, time())
                except Exception:
                    # This catch:
                    # Empty: in tuple2 = self.right.get(False), when the queue is empty.
                    # TypeError: in att = att + tuple[var], when the tuple is "EOF".
                    #print "Unexpected error:", sys.exc_info()[0]
                    pass

            for r in toRemove:
                del right_queues[r]
        # Put EOF in queue and exit.
        self.qresults.put("EOF")
        return

    def getResource(self, tuple):
        resource = ''
        for var in self.vars:
            resource = resource + tuple[var]
        return resource

    def makeInstantiation(self, tuple, operator):
        d = {}
        for var in self.vars:
            v = tuple[var]
            if string.find(v, "http") == 0: # uris must be passed between < .. >
                v = "<"+v+">"
            d[var] = v
        #print type(operator)
        new_operator = operator.instantiate(d)
        return new_operator

    def probeAndInsert1(self, tuple, table1, table2, time):

        record = Record(tuple, time, 0)
        r = self.getResource(tuple)
        if r in table1:
            records =  table1[r]
            for t in records:
                if t.ats > record.ats:
                    continue
                x = t.tuple.copy()
                x.update(tuple)
                self.qresults.put(x)
        p = table2.get(r, [])
        i = (p == [])
        p.append(record)
        table2[r] = p
        return i

    def probeAndInsert2(self, resource, tuple, table1, table2, time):

        record = Record(tuple, time, 0)
        if resource in table1:
            records =  table1[resource]
            for t in records:
                if t.ats > record.ats:
                    continue
                x = t.tuple.copy()
                x.update(tuple)
                self.qresults.put(x)
        table2.get(r, []).append(record)
