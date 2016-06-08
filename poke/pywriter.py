"""
Uses the pycjson parser results to generate bindings for python. This is very
similar to the CFFI project. However instead of making direct calls through the
Python API the "marshaled" results are serialized into a client specified
canonical format. This allows for a modicum of flexibility in terms of where the
callee resides. For instance the callee could be running in another process,
or even running on another machine. Those details are left to clients.

Clients must subclass ApiBase, and implement the _createOstream and
_invoke methods. _createOstream is a factory method that resturns a stream
object that enables calls to be serialized using the perferred serialization
scheme of the client. This is done by deriving from AbstractStream. A reference
BinaryStream serializer is provided.

There are a vast number of similar projects on the Web, so why another C to
Python utility? What I've tried to do is build light weight components, with
injectable functionality. If you need that type of flexibility then this project
might be for you. Otherwise, there are lot's of great tools that do exactly the
same thing and have large communities of active users.
"""

import sys
sys.path.append('../') # permit access to parent directory modules
from pycjson import util, parser, sugar

#
# normalization transforms to be applied (these can be overriden by clients)
#
normalize      = util.camelize
normallizeFunc = util.camelize
normalizeField = util.downCamelize
normalizeType  = util.camelize

#
# create some buffers objects to hold the output
#

structs = util.OutputBuffer()
funcs = util.OutputBuffer()
funcHeader = \
"""
class ApiBase:
    def __init__(self):
        pass
    
    def _createOstream(self):
        pass
        
    def _invoke(method):
        pass
"""
funcs.writeln(funcHeader)
funcs.incIndent()
 
 # type declarations already encountered
declsSeen = {}
  
#
# struct encoder 
#
    
structs.writeln("""
def codeArray(subs, arr, coder):
    count = subs[0]
    if len(subs) == 1:
        # base case
        for i in range(count):
            coder(arr[i])
    else:
        subs = subs[1:]
        arr  = arr[1:]
        for i in range(count):
            # encode dimension K + 1
            codeArray(subs, arr, coder)
            
""")

    
    
def writeArrayEncoder(out, f, pre):
    """
    handle encoding an array
    """
    t = f.typeInfo.declType
    rt = util.resolveDecl(t)
    
    # select the encoder 
    coder = ''
    if rt.kind == sugar.KindStruct:
        coder = 'lambda obj: obj.writeToStream(s))'
    if f.typeInfo.isString():
        coder = 'lambda obj: s.putCString(obj)'
    else:
        coder = 'lambda obj: s.put' +  normalize(rt.identifier) + '(obj)'
    
    # perform the encoding 
    out.writeln('codeArray(',
                    pre,
                    normalizeField(f.identifier),
                    ', ',
                    str(tuple(f.typeInfo.subscripts)),
                    ', ',
                    coder)
        
    
def writeFieldEncoder(buf, f, pre):
    """
    get decoder value for input type
    """
    t = f.typeInfo.declType
    rt = util.resolveDecl(t)
    if f.typeInfo.isArray():
        writeArrayEncoder(buf, f, pre)
    if rt.kind == sugar.KindStruct:
        buf.writeln(pre, normalizeField(f.identifier), '.writeToStream(s)')
    elif f.typeInfo.isString():
        buf.writeln('s.putCString(', pre, normalizeField(f.identifier), ')')
    else:
        buf.writeln('s.put',
                    normalize(rt.identifier),
                    '(',
                    pre,
                    normalizeField(f.identifier),
                    ')')
    


def writeEncoder(out, t):
    """
    write the encoder functionality
    """
    out.writeln("def writeToStream(self, s):")
    out.incIndent()
    for f in t.fields:
        writeFieldEncoder(out, f, 'self.')
    out.decIndent()


#
# struct decoer
#

def writeArrayDecoder(out, f, pre):
    """
    handle decoding an array
    """
        

def writeFieldDecoder(out, f):
    """
    get decoder value for input type
    """
    t = f.typeInfo.declType
    rt = util.resolveDecl(t)
    if rt.kind == sugar.KindStruct:
        out.writeln('self.', normalizeField(f.identifier),'.loadFromStream(s)')
    elif f.typeInfo.isString():
        out.writeln('self.', normalizeField(f.identifier), ' = s.getCString()')
    else:
        out.writeln('self.',
                    normalizeField(f.identifier),
                    ' = s.get',
                    normalize(rt.identifier),
                    '()')


def writeDecoder(out, t):
    """
    write the struct initializer that takes a stream as an argument
    """
    out.writeln('def loadFromStream(self, s):')
    out.incIndent()
    for f in t.fields:
        writeFieldDecoder(out, f)
    out.decIndent()
    out.writeln()
 

def writeInitBody(out, t):
    """
    write the struct initializer that takes no arguments
    """
    for f in t.fields:
        rval = '0'
        rt = util.resolveDecl(f.typeInfo.declType)
        if rt.kind == sugar.KindStruct:
            rval = normalizeType(rt.identifier) + '()'
        elif f.typeInfo.isString():
            rval = "''"
        out.writeln('self.', normalizeField(f.identifier), ' = ', rval)


def writeStruct(t):
    """
    find or create structure definition
    """
    if declsSeen.has_key(t):
        return declsSeen[t]
    
    # mark as seen
    declsSeen[t] = None
    
    # write out a new structure definition
    identifier = normalizeType(t.identifier)
    out = structs
    out.writeln('class ', identifier, ':')
    out.incIndent()
    out.writeln('def __init__(self, s=None):')
    out.incIndent()
    writeInitBody(out, t)
    out.writeln('if s != None:')
    out.incIndent()
    out.writeln('self.loadFromStream(s)')
    out.decIndent(2)
    out.writeln()
    writeDecoder(out, t)
    writeEncoder(out, t)
    out.decIndent()
    out.write('\n\n')
    # return the identifier    

#
# function encoder
#

def writeFunction(t):
    """
    encoder for functions
    """
    # we don't support typedef for functions so no need to resolve the type
    if declsSeen.has_key(t):
        # FIXME should raise an error 
        return 
    # mark the function as visited
    declsSeen[t] = None
    method = util.downCamelize(t.identifier)
    funcs.indent()
    funcs.write('def ', method, '(self')
    for f in t.fields:
        funcs.write(', _', f.identifier)
    funcs.write('):')
    funcs.writeln()
    funcs.incIndent()
    
    # parse input parameters
    funcs.writeln('s = self._createOstream()')
    for f in t.fields:
        writeFieldEncoder(funcs, f, '_')
        
    # process (TODO might be nice to support non-blocking)
    funcs.writeln('s = self._invoke(', util.toMsgId(t.identifier), ', s)\n')
    
    # handle return by reference
    for f in t.fields:
        pass
        
    if not t.returnInfo.isVoid():
        # decod return value
        pass
    
    funcs.decIndent()
    return method 
    
        
def writeNothing(t): pass


transcoders = {
    parser.KindStruct   : writeStruct,
    parser.KindEnum     : writeNothing,
    parser.KindFunction : writeFunction,
    parser.KindBuiltIn  : writeNothing,
}


def process(decls):
    for t in decls:
        transcoders[t.kind](t)
    

if __name__ == '__main__':
    # parse the given input file
    with open(sys.argv[1]) as inf: parser.parse(inf)
    process(parser.getResults())
    print structs
    print funcs   
    