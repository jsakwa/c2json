

TabStop = ' ' * 4


class OutputBuffer:
    """
    output buffer 
    """
    def __init__(self, level=0):        
        self.indentLevel = level
        self.leadingIndent = TabStop * level 
        self.buffer = []

    def incIndent(self, count=1):
        """
        increase leading indentation
        """
        self.indentLevel += count
        self.leadingIndent = TabStop * self.indentLevel
    
    def decIndent(self, count=1):
        """
        decrease the leading indentation
        """
        self.indentLevel -= count
        self.leadingIndent = TabStop * self.indentLevel
        
    def writeln(self, *args):
        """
        write a line to the output buffer
        """
        self.buffer += [self.leadingIndent] + [a for a in args] + ['\n']
        
    def indent(self):
        """
        append leading indent
        """
        self.buffer += [self.leadingIndent]
    
    def write(self, *args):
        """
        write without appending any extra white space
        """
        self.buffer += [a for a in args]
        
        
    def __str__(self):
        return ''.join(self.buffer)
    
    
def camelize(s):
    """
    convert to camel case 
    """
    original = s    
    if (len(s) > 2) and (s[-2:] == '_t'):
        s = s[:-2]
    s = s.title()
    s = s.replace('_', '')
    if s == '':
        return original
    return s 
    
def downCaseFirstLetter(s):
    """
    downcase the first letter
    """
    return s[:1].lower() + s[1:]


def downCamelize(s):
    """
    camelize while down-casing the first letter
    """
    return downCaseFirstLetter(camelize(s))

def toMsgId(s):
    """
    create a message type-name for the given function
    """
    return 'FunId' + camelize(s)


def resolveDecl(t):
    """
    if t is an aliased type returns the earliest ancestor that is not aliased
    with another type. Since the <stdint.h> decls are treated as builtin types
    these types will resolve reflexively -- that is uint32_t resolves to
    uint32_t
    """
    # FIXME since we don't yet support type aliasing we simply return the input
    # value unchanged. In the future we should test to see if the type is
    # an aliased type, and then if so, return it's architype
    return t


