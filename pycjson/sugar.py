"""
data types used by the parser to generate a "sugary" reprentation of the input
JSON file
"""
#
# constants
#

# qualifier ids 
(QualConst, QualPtr) = range(2)


# classifer ids
(KindUnresolved,
 KindBuiltIn,
 KindAlias,
 KindStruct,
 KindEnum,
 KindVar,
 KindFunction) = range(7)


#
# helper methods
#

def stringifyRange(rng):
    """
    stringify the input range like object
    """
    spc = ''
    result = ''
    for i in rng:
        result += spc + str(i)
        spc = ', '
    return result


def stringifyQual(q):
    if q == QualConst:
        return 'const'
    return 'ptr_to'


def stringifyQuals(rng):
    result = ''
    for i in rng:
        result += stringifyQual(i) + '.'
    return result
    

#
# types
#

class VarInfo:
    """
    decl type decorator that adds quals/subscrits etc.
    """
    def __init__(self, declType, quals=[], subscripts=[]):
        self.declType   = declType   # the underlying type of self
        self.quals      = quals      # qualifiers (const/ptr etc.)
        self.subscripts = subscripts # the array type of self

    def hasQual(self):
        return len(self.quals) != 0
    
    def isPointer(self):
        return self.hasQual() \
                and ((len(self.quals) > 1) or (self.quals[0] == QualPtr))
        
    def isConst(self):
        return self.hasQual() and (self.quals[-1] == QualConst)
    
    def isArray(self):
        return len(self.subscripts) != 0
    
    def isVoid(self):
        """
        returns true if the function returns void
        """
        # FIXME should devise a cleaner way to test for void
        return self.declType.identifier == 'void'
    
    def isString(self):
        """
        true if the type has a natural interpertation as a CString
        """
        # FIXME should devise a cleaner way to test for char
        return self.isPointer() and (self.declType.identifier == 'char')

    def __str__(self):
        subs = ''
        if len(self.subscripts):
            subs = str(self.subscripts)      
        return stringifyQuals(self.quals) + str(self.declType.identifier) + subs


class StructDecl:
    """
    introduces a new type name
    """
    def __init__(self, identifier, fields):
        self.kind  = KindStruct
        self.identifier = identifier
        self.fields = fields
    
    def __str__(self):
        return 'rec %s {%s}' %(self.identifier, stringifyRange(self.fields))
        
        
class EnumDecl:
    """
    introduces a new enumerated type
    """
    def __init__(self, identifier, fields):
        self.kind = KindEnum
        self.identifier = identifier
        self.fields = fields 

    def __str__(self):
        return 'enum %s {%s}' %(self.identifier, stringifyRange(self.fields))   


class FunctionDecl:
    """
    introduces a new function type
    """
    def __init__(self, identifier, fields, returnInfo):
        self.kind = KindFunction
        self.identifier = identifier
        self.fields = fields 
        self.returnInfo = returnInfo
    
    def __str__(self):
        ret = str(self.returnInfo)
        args = stringifyRange(self.fields)
        return 'fun %s {%s} -> %s' %(self.identifier, args, ret)
    
        
class VarDecl:
    """
    introduces a new variable
    """
    def __init__(self, identifier, typeInfo):
        self.kind = KindVar
        self.identifier = identifier
        self.typeInfo = typeInfo
        
    def __str__(self):
        return self.identifier + ': ' + str(self.typeInfo)        


class BuiltinDecl:
    """
    introduces a new built-in type
    """
    def __init__(self, identifer, width):
        self.kind = KindBuiltIn
        self.identifier = identifer
        self.width = width
    
    def __str__(self):
        return 'builtin: ' + self.identifier
        

class ConstDecl:
    """
    indroduces a new constant
    """
    def __init__(self, identifier, value):
        self.identifier = identifier
        self.value = value
        
    def __str__(self):
        return self.identifier + ': ' + str(self.value)