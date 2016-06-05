"""
Uses the pycjson parser results to generate bindings for C. This is very
similar to the CFFI project. However instead of making direct calls through the
Python API the "marshaled" results are serialized into a client specified
canonical format. This allows for a modicum of flexibility in terms of where the
callee resides. For instance the callee could be running in another process,
or even running on another machine. Those details are left to clients.

similar projects:
https://github.com/pearu/simple-rpc-cpp
https://thrift.apache.org/
http://www.yzhang.net/simple-rpc/
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

def nameForType(t, mode):
    return 'stream_' + mode + '_' + util.stripTypeDelim(t.identifier)
    

#
# create some buffers objects to hold the output
#

structs = util.OutputBuffer()
funcs = util.OutputBuffer()
 
 # type declarations already encountered
declsSeen = {}
  
    

#
# struct decoer
#


def writeArray(out, f):
    """
    write an array encoder/decoder
    """
    # FIXME TBD (NOTE we also need to cache these somewhere)

 
def writeField(out, f, s, mode, pre='_'):
    """
    write the decoder for the field
    """
    rt = util.resolveDecl(f.typeInfo.declType)
    
    # make sure to visit the type
    transcoders[rt.kind](rt)
    
    if f.typeInfo.isString():
        out.writeln('stream_', mode, '_cstring(', s,', &', pre,
                    f.identifier ,');')
    else:
        cast = ''
        if rt != f.typeInfo.declType:
            # cast-away type alias
            cast = '(' + rt.identifier + '*)'
        out.writeln(nameForType(rt, mode),
                      '(', s, ', ', cast, '&', pre, f.identifier, ');')
        

def visitPrerequisites(t):
    """
    ensure that all prerequisite encoder/decoders are generated before
    proceeding
    """
    for f in t.fields:
        t = f.typeInfo.declType
        transcoders[t.kind](t)


def writeStructEncoderOrDecoder(t, mode):
    """
    find or create structure encoder/deoceer
    """
    # write out a new structure definition
    out = structs
    
    # visit prerequisites before proceeding
    visitPrerequisites(t)
    
    out.writeln('static void ', nameForType(t, mode),
                '(stream_t* s, ', t.identifier, '* v) {')
    
    out.incIndent()
    for f in t.fields:
        writeField(structs, f, 's', mode, 'v->')
    out.decIndent()
    out.write('}\n\n')
    # return the identifier    


def writeStruct(t):
    """
    write struct encoder and decoder
    """
    rt = util.resolveDecl(t)
    
    if declsSeen.has_key(rt):
        return declsSeen[rt]
    
    # mark as seen
    declsSeen[t] = None
    declsSeen[rt] = None
    
    writeStructEncoderOrDecoder(rt, 'encode')
    writeStructEncoderOrDecoder(rt, 'decode')



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
    
    func = '_' + t.identifier
    funcs.writeln('static void ', func, '(stream_t* ins, stream_t* outs) {')
    funcs.incIndent()
    
    # write out temp vars to hold function args
    for f in t.fields:
        tn = f.typeInfo.declType.identifier
        funcs.writeln(tn,  ' _', f.identifier, ';')

    # write out temp var to capture return value
    if not t.returnInfo.isVoid():
        funcs.writeln(t.returnType.identifier, ' retv;')
    
    # decode input stream into temp vars
    for f in t.fields:
        writeField(funcs, f, 'ins', 'decode')
    
    # invoke underlying function
    funcs.indent()
    if not t.returnInfo.isVoid():
        # capture return value
        funcs.write('retv = ')    
    funcs.write(t.identifier)
    sep = '('
    for f in t.fields:
        funcs.write(sep,
                    f.typeInfo.getInputArgumentModifier(),
                    '_',
                    f.identifier)
        sep = ','
    funcs.write(');\n')
    
    # capture return value
    if not t.returnInfo.isVoid():
        writeField(funcs, t.returnInfo, 'outs', 'encode', '')

    # capture in/out params
    for f in t.fields:
       if f.typeInfo.isOutputByRef():
            writeField(funcs, f, 'outs', 'encode')
       
    funcs.decIndent()
    funcs.writeln('}\n')
    
    
def writeNothing(t): pass


transcoders = {
    parser.KindStruct   : writeStruct,
    parser.KindEnum     : writeNothing,
    parser.KindBuiltIn  : writeNothing,
}


def process(decls):
    for t in decls:
        if t.kind == parser.KindFunction:
            writeFunction(t)
    

if __name__ == '__main__':
    # parse the given input file
    with open(sys.argv[1]) as inf: parser.parse(inf)
    process(parser.getResults())
    print structs
    print funcs   
    