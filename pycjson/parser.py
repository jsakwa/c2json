"""
parse JSON types and create a simplified and fully resolved list of type
descriptions that is convenient for Python based source-level tools
"""

import json
from sugar import *

#
# constatns 
#

# fields 
FieldKind       = 'kind'
FieldFields     = 'fields'
FieldReturn     = 'return'
FieldValue      = 'value'
FieldIdent      = 'identifier'

# kind/type class
KindNameStruct  = 'struct'
KindNameEnum    = 'enum'
KindNameFunction= 'function'

# C reserved identifiers needed
KeywordConst    = 'const'
KeywordPtr      = '*'

# extra reserved identifier names
AnonymousEnum   = '(anonymous)'


# build-in type initialier list
builtinInitList = (
    ('void',    0),   
    ('char',    1),   
    ('int8_t',  1),
    ('uint8_t', 1),
    ('int16_t', 2),
    ('uint16_t',2),
    ('int32_t', 4),
    ('uint32_t',4),
    ('int64_t', 8),
    ('uint64_t',8),
    ('size_t',  4), 
    ('float',   4),
    ('double',  8))

# construct all builtin types from the initializer list
builtins = [BuiltinDecl(ident, width)
                for (ident, width) in builtinInitList]

typeMap = None

def reset():
    """
    reset the parser to intial state
    """
    global typeMap
    typeMap = {}
    for t in  builtins: typeMap[t.identifier] = t

# initialize type map with builtin types
reset()

#
# convenience functions
#

def isIdentOrQualCandidate(part):
    part = str(part)
    return str.isalpha(part[0]) or (part[0] == '_') or (part == AnonymousEnum)
def isQual(part): return part in (KeywordConst, KeywordPtr)
def isPointer(part): return part == KeywordPtr
def isAnonymous(t): return t.identifier == AnonymousEnum
def isDeclKnown(t): return typeMap.has_key(t.identifier)


def valsForKeys(h, *keys):
    """
    obtain fields for keys
    """
    return [h[k] for k in keys]


def findOrCreateDeclForIdent(ident):
    """
    looks-up the type in the type map and return it, or adds a new type
    and returns it
    """
    # FIXME handle forward references by adding an unresolved type to the
    # the list (if necessary)
    return typeMap[ident]


def  addDecl(decl):
    """
    add a new decl to the type map
    """
    # FIXME we need to handle the case where there is an existing unresolved
    # type in the map
    typeMap[decl.identifier] = decl
#
# parser components
#

def parseSubscripts(part):
    """
    parse out subscript values
    """
    subs = str(part)
    subs = part.split("]")[:-1]
    return [int(sub[1:]) for sub in subs]


def parseVarInfo(t):
    """
    parse type information
    """
    identifier = ""
    quals      = []
    subscripts = []
    
    for part in t.split(' '):
        if isIdentOrQualCandidate(part):
            if isQual(part):
                # must be qualifier part
                if part == KeywordConst:
                    quals.append(QualConst)
            else:
                # must be identifier part
                identifier = part
                
        elif isPointer(part):
            # the type is a pointer
            quals.append(QualPtr)
        else:
            # must be subscript
            subscripts = parseSubscripts(part)
    
    return VarInfo(findOrCreateDeclForIdent(identifier), quals, subscripts)
            

def  parseVarFields(fields):
    """
    decode field set
    """
    fields = [valsForKeys(f, FieldIdent, FieldKind) for f in fields]
    return [VarDecl(identifier, parseVarInfo(kind)) for (identifier, kind) in fields]

    
def parseStruct(struct):
    """
    decode structure
    """
    identifier, fields = valsForKeys(struct, FieldIdent, FieldFields)
    t = StructDecl(identifier, parseVarFields(fields))
    addDecl(t)
    
    
def parseFunction(func):
    """
    decode function representation
    """
    identifier, fields, returnType = \
            valsForKeys(func, FieldIdent, FieldFields, FieldReturn)
    
    t = FunctionDecl(identifier,
                         parseVarFields(fields),
                         parseVarInfo(returnType))
    addDecl(t)


def parseConstant(const):
    """
    parse a constants
    """
    identifier, value = valsForKeys(const, FieldIdent, FieldValue)
    return ConstDecl(identifier, value)


def parseEnum(enum):
    """
    parse an enumerated type
    """
    identifier, fields = valsForKeys(enum, FieldIdent, FieldFields)
    t = EnumDecl(identifier, [parseConstant(c) for c in fields])
    if isAnonymous(t) and isDeclKnown(t):
        # handle adding fields to anonymously specified enumerated type
        enum = typeMap[identifier]
        enum.fields += t.fields
    else:
        # add ordinary enum decl
        addDecl(t)
 
    
#
# do the parsing
#
    
parser = {
    KindNameStruct   : parseStruct,
    KindNameFunction : parseFunction,
    KindNameEnum     : parseEnum
}

def parse(inf):
    """
    parse json input file
    """
    for rec in json.load(inf):
        parser[rec[FieldKind]](rec)
    return typeMap
        
    
def getResults():
    """
    get the parser result
    """
    return typeMap