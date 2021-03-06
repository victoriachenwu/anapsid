from __future__ import division
import string
import os
from Tree import Node, Leaf


class Service(object):

    def __init__(self, endpoint, triples):
        endpoint = endpoint[1:len(endpoint)-1]
        self.endpoint = endpoint
        self.triples = triples
        self.filters = []

    def include_filter(self, f):
        self.filters.append(f)

    def __repr__(self):
        if isinstance(self.triples, list):
            triples_str = " . ".join(map(str, self.triples))
        else:
            triples_str = str(self.triples)
        filters_str = " . ".join(map(str, self.filters))
        return ("\n    { SERVICE <" + self.endpoint + "> { "
                + triples_str + filters_str + " } \n    }")

    def allTriplesLowSelectivity(self):
        a = True
        if isinstance(self.triples, list):
            for t in self.triples:
                a = a and t.allTriplesLowSelectivity()
        else:
            a = self.triples.allTriplesLowSelectivity()
        return a

    def instantiate(self, d):
        if isinstance(self.triples, list):
             new_triples = [t.instantiate(d) for t in self.triples]
        else:
             new_triples = self.triples.instantiate(d)
        return Service("<"+self.endpoint+">", new_triples)

    def getTriples(self):
        if isinstance(self.triples, list):
            triples_str = " . ".join(map(str, self.triples))
        else:
            triples_str = str(self.triples)
        return triples_str + " . ".join(map(str, self.filters))

    def show(self, x):
        def pp (t):
            return t.show(x+"    ")
        if isinstance(self.triples, list):
            triples_str = " . \n".join(map(pp, self.triples))
        else:
            triples_str = self.triples.show(x+"    ")
        filters_str = " . \n".join(map(pp, self.filters))
        return (x + "SERVICE <" + self.endpoint + "> { \n" + triples_str
                + filters_str + "\n" + x + "}")

    def show2(self, x):
        def pp (t):
            return t.show2(x+"    ")
        if isinstance(self.triples, list):
            triples_str = " . \n".join(map(pp, self.triples))
        else:
            triples_str = self.triples.show2(x+"    ")
        filters_str = " . \n".join(map(pp, self.filters))
        return triples_str + filters_str

    def getVars(self):
        if isinstance(self.triples, list):
            l = []
            for t in self.triples:
                l = l + t.getVars()
        else:
            l = self.triples.getVars()
        return l

    def places(self):
        p = 0
        if isinstance(self.triples, list):
            for t in self.triples:
                p = p + t.places()
        else:
            p = self.triples.places()
        return p

    def constantNumber(self):
        p = 0
        if isinstance(self.triples, list):
            for t in self.triples:
                p = p + t.constantNumber()
        else:
            p = self.triples.constantNumber()
        return p

    def constantPercentage(self):
        return self.constantNumber()/self.places()

    def setGeneral(self, ps, genPred):
        if isinstance(self.triples, list):
            for t in self.triples:
                t.setGeneral(ps, genPred)
        else:
            self.triples.setGeneral(ps, genPred)

class Query(object):

    def __init__(self, prefs, args, body, distinct):
        self.prefs = prefs
        self.args = args
        self.body = body
        self.distinct = distinct
        self.join_vars = self.getJoinVars()
        genPred = readGeneralPredicates(os.path.join(os.path.split(os.path.split(__file__)[0])[0],
                                                     'Catalog','generalPredicates'))
        self.body.setGeneral(getPrefs(self.prefs), genPred)

    def __repr__(self):
        body_str = str(self.body)
        args_str = " ".join(map(str, self.args))
        if self.args == []:
            args_str = "*"
        if self.distinct:
            d = "DISTINCT "
        else:
            d = ""
        return self.getPrefixes()+"SELECT "+d+args_str+"\nWHERE {\n"+body_str+"\n}"

    def instantiate(self, d):
        new_args = []
        for a in self.args:
            an = string.lstrip(string.lstrip(self.subject.name, "?"), "$")
            if not (an in d):
                new_args.append(a)
        return Query(self.prefs, new_args, self.body.instantiate(d), self.distinct)

    def places(self):
        return self.body.places()

    def constantNumber(self):
        return self.body.constantNumber()

    def constantPercentage(self):
        return self.constantNumber()/self.places()

    def show(self):

        body_str = self.body.show(" ")
        args_str = " ".join(map(str, self.args))
        if self.args == []:
            args_str = "*"
        if self.distinct:
            d = "DISTINCT "
        else:
            d = ""
        return self.getPrefixes()+"SELECT "+d+args_str+"\nWHERE {\n"+body_str+"\n}"

    def show2(self):

        body_str = self.body.show2(" ")
        args_str = " ".join(map(str, self.args))
        if self.args == []:
            args_str = "*"
        if self.distinct:
            d = "DISTINCT "
        else:
            d = ""
        return self.getPrefixes() + "SELECT " + d + args_str + "\nWHERE {\n" + body_str + "\n}"

    def getPrefixes(self):
        r = ""
        for e in self.prefs:
            r = r + "\nprefix "+e
        if not r == "":
            r = r + "\n"
        return r

    def getJoinVars(self):

        join_vars = getJoinVarsUnionBlock(self.body)
        join_vars = [ v for v in join_vars if join_vars.count(v) > 1]

        return set(join_vars)

    def getJoinVars2(self):

        join_vars = []

        for s in self.body:
          for t in s.triples:
            if not t.subject.constant:
                join_vars.append(t.subject.name)
            if not t.theobject.constant:
                join_vars.append(t.theobject.name)

        join_vars = [ v for v in join_vars if join_vars.count(v) > 1]

        return set(join_vars)

    def getTreeRepresentation(self):

        l0 = self.body
        while len(l0) > 1:
            l1 = []
            while len(l0) > 1:
                x = l0.pop()
                y = l0.pop()
                l1.append((x,y))
            if len(l0) == 1:
                l1.append(l0.pop())
            l0 = l1
        if len(l0) == 1:
            return aux(l0[0],"", " xxx ")
        else:
            return " "

def getJoinVarsUnionBlock(ub):

    join_vars = []

    for jb in ub.triples:
        join_vars.extend(getJoinVarsJoinBlock(jb))

    return join_vars

def getJoinVarsJoinBlock(jb):

    join_vars = []

    for bgp in jb.triples:

        if isinstance(bgp, Triple):
            if not bgp.subject.constant:
                join_vars.append(bgp.subject.name)
            if not bgp.theobject.constant:
                join_vars.append(bgp.theobject.name)
        elif isinstance(bgp, Service):
            join_vars.extend(getJoinVarsUnionBlock(bgp.triples))
        elif isinstance(bgp, Optional):
            join_vars.extend(getJoinVarsUnionBlock(bgp.bgg))
        elif isinstance(bgp, UnionBlock):
            join_vars.extend(getJoinVarsUnionBlock(bgp))

    return join_vars

def aux(e,x, op):
    def pp (t):
        return t.show(x+"  ")
    if type(e) == tuple:
        (f,s) = e
        r = ""
        if f:
            r = x+"{\n"+ aux(f, x+"  ", op) + "\n" + x + "}\n"
        if f and s:
            r = r + x + op + "\n"
        if s:
            r = r + x+"{\n" + aux(s,x+"  ", op) +"\n"+x+"}"
        return r
    elif type(e) == list:
        return (x + " . \n").join(map(pp, e))
    elif e:
        return e.show(x+"  ")
    return ""

def aux2(e,x, op):
    def pp (t):
        return t.show2(x+"  ")
    if type(e) == tuple:
        (f,s) = e
        r = ""
        if f:
            r = x+"{\n"+ aux2(f, x+"  ", op) + "\n" + x + "}\n"
        if f and s:
            r = r + x + op + "\n"
        if s:
            r = r + x+"{\n" + aux2(s,x+"  ", op) +"\n"+x+"}"
        return r
    elif type(e) == list:
        return (x + " . \n").join(map(pp, e))
    elif e:
        return e.show2(x+"  ")
    return ""

class UnionBlock(object):
    def __init__(self, triples):
        self.triples = triples

    def __repr__(self):
        return self.show(" ")

    def show(self, w):

        n = nest(self.triples)
        if n:
            return aux(n, w, " UNION ")
        else:
            return " "

    def setGeneral(self, ps, genPred):
        if isinstance(self.triples, list):
            for t in self.triples:
                t.setGeneral(ps, genPred)
        else:
            self.triples.setGeneral(ps, genPred)

    def allTriplesLowSelectivity(self):
        a = True
        if isinstance(self.triples, list):
            for t in self.triples:
                a = a and t.allTriplesLowSelectivity()
        else:
            a = self.triples.allTriplesLowSelectivity()
        return a

    def instantiate(self, d):
        if isinstance(self.triples, list):
             ts = [t.instantiate(d) for t in self.triples]
             return JoinBlock(ts)
        else:
             return self.triples.instantiate(d)

    def show2(self, w):
        n = nest(self.triples)
        if n:
            return aux2(n, w, " UNION ")
        else:
            return " "

    def getVars(self):
        l = []
        for t in self.triples:
            l = l + t.getVars()
        return l

    def includeFilter(self, f):

       for t in self.triples:
           t.includeFilter(f)

    def places(self):
        p = 0
        for e in self.triples:
            p = p + e.places()
        return p

    def constantNumber(self):
        c = 0
        for e in self.triples:
            c = c + e.constantNumber()
        return c

    def constantPercentage(self):
        return self.constantNumber()/self.places()

def nest(l):

    l0 = list(l)
    while len(l0) > 1:
        l1 = []
        while len(l0) > 1:
            x = l0.pop()
            y = l0.pop()
            l1.append((x,y))
        if len(l0) == 1:
            l1.append(l0.pop())
        l0 = l1
    if len(l0) == 1:
        return l0[0]
    else:
        return None

class JoinBlock(object):
    def __init__(self, triples):
        self.triples = triples

    def __repr__(self):
        r = ""
        if isinstance(self.triples, list):
            for t in self.triples:
                if isinstance(t, list):
                    r = r + " . ".join(map(str, t))
                elif t:
                    if r:
                        r = r + " . " + str(t)
                    else:
                        r = str(t)
        else:
            r = str(self.triples)
        return r

    def setGeneral(self, ps, genPred):
        if isinstance(self.triples, list):
            for t in self.triples:
                t.setGeneral(ps, genPred)
        else:
            self.triples.setGeneral(ps, genPred)

    def allTriplesLowSelectivity(self):
        a = True
        if isinstance(self.triples, list):
            for t in self.triples:
                a = a and t.allTriplesLowSelectivity()
        else:
            a = self.triples.allTriplesLowSelectivity()
        return a

    def show(self, x):

        if isinstance(self.triples, list):
            n = nest(self.triples)
            if n:
                return aux(n, x, " . ")
            else:
                return " "
        else:
            return self.triples.show(x)

    def instantiate(self, d):
        if isinstance(self.triples, list):
             ts = [t.instantiate(d) for t in self.triples]
             return JoinBlock(ts)
        else:
             return self.triples.instantiate(d)

    def show2(self, x):
        if isinstance(self.triples, list):
            n = nest(self.triples)
            if n:
                return aux2(n, x, " . ")
            else:
                return " "
        else:
            return self.triples.show2(x)

    def getVars(self):
        l = []
        if isinstance(self.triples, list):
            for t in self.triples:
                l = l + t.getVars()
        else:
            l = self.triples.getVars()
        return l

    def includeFilter(self, f):
        for t in self.triples:
            if isinstance(t, list):
                for s in t:
                    s.include_filter(f)
            else:
                t.includeFilter(f)

    def places(self):
        p = 0
        if isinstance(self.triples, list):
            for e in self.triples:
                p = p + e.places()
        else:
            p = self.triples.places()
        return p

    def constantNumber(self):
        c = 0
        if isinstance(self.triples, list):
            for e in self.triples:
                c = c + e.constantNumber()
        else:
            c = self.triples.constantNumber()
        return c

    def constantPercentage(self):
        return self.constantNumber()/self.places()

class Filter(object):
    def __init__(self, expr):
        self.expr = expr

    def __repr__(self):
        return ("\n        FILTER ("+str(self.expr)+")")

    def show(self, x):
        return "\n"+x+"FILTER ("+str(self.expr)+")"

    def getVars(self):
        return self.expr.getVars()

    def setGeneral(self, ps, genPred):
        return

    def places(self):
        return self.expr.places()

    def allTriplesLowSelectivity(self):
        return True

    def instantiate(self, d):
        return Filter(self.expr.instantiate(d))

    def constantNumber(self):

        return self.expr.constantNumber()

    def constantPercentage(self):
        return self.constantNumber()/self.places()

class Optional(object):
    def __init__(self, bgg):
        self.bgg = bgg
    def __repr__(self):
        return " OPTIONAL { " + str(self.bgg)+ " }"

    def show(self, x):
        return x+"OPTIONAL {\n"+self.bgg.show(x+"  ")+"\n"+x+"}"

    def setGeneral(self, ps, genPred):
        self.bgg.setGeneral(ps, genPred)

    def getVars(self):
        return self.bgg.getVars()

    def places(self):
        return self.bgg.places()

    def allTriplesLowSelectivity(self):
        return self.bgg.allTriplesLowSelectivity()

    def instantiate(self, d):
        return Optional(self.bgg.instantiate(d))

    def constantNumber(self):

        return self.bgg.constantNumber()

    def constantPercentage(self):
        return self.constantNumber()/self.places()

class Expression(object):

    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self):
        return (str(self.left)+" "+ self.op +" "+str(self.right))

    def getVars(self):
        return self.left.getVars()+self.right.getVars()

    def instantiate(self, d):
        return Expression(self.op, self.left.instantiate(d),
                          self.right.instantiate(d))

    def allTriplesLowSelectivity(self):
        return True

    def setGeneral(self, ps, genPred):
        return

    def places(self):
        return self.left.places() + self.right.places()

    def constantNumber(self):

        return self.left.constantNumber() + self.right.constantNumber()

    def constantPercentage(self):
        return self.constantNumber()/self.places()

class Triple(object):
    def __init__(self, subject, predicate, theobject):
        self.subject = subject
        self.predicate = predicate
        self.theobject = theobject
        self.isGeneral = False

    def __repr__(self):
        return ("\n        "+self.subject.name+" "+ self.predicate.name +" "
                +self.theobject.name)

    def setGeneral(self, ps, genPred):
        self.isGeneral = (getUri(self.predicate, ps) in genPred)

    def __eq__(self, other):

        return ((self.subject == other.subject) and
                (self.predicate == other.predicate) and
                (self.theobject == other.theobject))

    def __hash__(self):
        return hash((self.subject,self.predicate,self.theobject))

    def allTriplesLowSelectivity(self):
        return ((not self.predicate.constant)
                or ((self.isGeneral) and (not self.subject.constant)
                    and (not self.theobject.constant)))

    def show(self, x):
        return x+self.subject.name+" "+ self.predicate.name +" "+self.theobject.name

    def getVars(self):

        l = []
        if not self.subject.constant:
            l.append(self.subject.name)
        if not self.theobject.constant:
            l.append(self.theobject.name)
        return l

    def places(self):
        return 3;

    def instantiate(self, d):
        sn = string.lstrip(string.lstrip(self.subject.name, "?"), "$")
        pn = string.lstrip(string.lstrip(self.predicate.name, "?"), "$")
        on = string.lstrip(string.lstrip(self.theobject.name, "?"), "$")
        if (not self.subject.constant) and (sn in d):
            s = Argument(d[sn], True)
        else:
            s = self.subject
        if (not self.predicate.constant) and (pn in d):
            p = Argument(d[pn], True)
        else:
            p = self.predicate
        if (not self.theobject.constant) and (on in d):
            o = Argument(d[on], True)
        else:
            o = self.theobject
        return Triple(s, p, o)

    def constantNumber(self):
        n = 0
        if self.subject.constant:
            n = n + 1
        if self.predicate.constant:
            n = n + 1
        if self.theobject.constant:
            n = n + 1
        return n

    def constantPercentage(self):
        return self.constantNumber()/self.places()

class Argument(object):
    def __init__(self, name, constant):
        self.name = name
        self.constant = constant

    def __repr__(self):
        return self.name

    def __eq__(self, other):
        return self.name == other.name and self.constant == other.constant

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((self.name,self.constant))

    def getVars(self):
        if self.constant:
            return []
        else:
            return [self.name]

    def places(self):
        return 1;

    def constantNumber(self):
        n = 0
        if self.constant:
            n = n + 1
        return n

    def constantPercentage(self):
        return self.constantNumber()/self.places()

def readGeneralPredicates(fileName):

    f = open(fileName, 'r')
    l = []
    l0 = f.readline()
    while not l0 == '':
        l0 = string.rstrip(l0, '\n')
        l.append(l0)
        l0 = f.readline()
    f.close()
    return l

def getUri(p, prefs):
    hasPrefix = prefix(p)
    if hasPrefix:
        (pr, su) = hasPrefix
        n = prefs[pr]
        n = n[:-1]+su+">"
        return n
    return p.name

def prefix(p):
    s = p.name
    pos = s.find(":")
    if (not (s[0] == "<")) and pos > -1:
        return (s[0:pos].strip(), s[(pos+1):].strip())

    return None

def getPrefs(ps):
    prefDict = dict()
    for p in ps:
         pos = p.find(":")
         c = p[0:pos].strip()
         v = p[(pos+1):len(p)].strip()
         prefDict[c] = v
    return prefDict
