//
// Simple Clang Libtooling extension to parse a C header file and emit JSON
// definitions for all C type definitions encountered in the source. This is a
// useful intermediate file, for creating other tools.
//
// This code was derived from the ourboros-introspector. The original code
// didn't do quite what I wanted (but proved to be a super useful example.) I
// eliminated most of the C++ parsing, and added the necessary code to do C
// parsing. I've also restructured things to emit the JSON immediately in a
// slightly different format than the original. I may reintroduce the C++
// features down the road, after C is working correctly.
//
// The original code from which the project is based was developed by
// Henrique Gemignani and may be found here:
//      https://github.com/ouroboros-project/ouroboros-introspector
//
// To build the project follow the instructions to install the clang
// source:
//      http://clang.llvm.org/get_started.html
//
// The code is tested against Clang 3.9
//
// You will not need Compiler-RT or libcxx (and I couldn't get them to build.)
// However, you will need all the other packages (which MUST be checked out
// into the exact directories referenced in the instructions)
//
// I usually check the LLVM + Clang code into a directory called "llvm" and then
// create a directory called "llvm_build" in the parent directory. It takes
// about 4 hours to build the project.
//
// Once you've successfully built LLVM + Clang. Follow these steps to install
// c2json
//
//      step 1. checkout this code base into:
//
//                  llvm/tools/clang/tools/extra/c2json
//
//      step 2. edit llvm/tools/clang/tools/extra/CmakeList.txt
//
//      step 3. add the following line:
//
//                  add_subdirectory(c2json)
//
//      step 4. rerun cmake on the source-tree
//
//      step 5. navigate to the build directory and execute:
//
//                  make c2json
//
//      If you've followed all of the steps the tool should build within about
//      one minute. Each subsequent build takes about 20 seconds.
//
// The AST has 3 main types of objects:
//      - statements (Stmt)
//      - types (Type)
//      - declarations (Decl)
//
// Statements represent the logical blocks that form the algorithmic structure
// of the program. Declarations introduce new identifier names. And types
// represent data structures. User specified types also contain references back
// to the declaration that introduced them. 
//
// To get an idea of how the clang AST is structured you can use
// clang's AST dump:
//    clang -Xclang -ast-dump -fsyntax-only <some_source_file>
//
// Given the richness of the Clang AST, navigating the tree can be a bit
// daunting -- even with the AST dump output as a reference. Fortunately,
// Clang AST provides a dump() method that can be invoked programmatically on any
// node. Armed with the dump() method deducing the path from nodeA to nodeB
// becomes relatively straightforward. Once you get used to it, the Clang AST
// is extremely trivial to use and powerful.


// TODO
//   - handle #define constants
//   - handle forward declaritions/aliased types
//   - handle scoped structs



#include "clang/Frontend/FrontendActions.h"
#include "clang/Tooling/CommonOptionsParser.h"
#include "clang/Tooling/Tooling.h"
#include "clang/ASTMatchers/ASTMatchers.h"
#include "clang/ASTMatchers/ASTMatchFinder.h"
#include "clang/AST/ASTContext.h"
#include "clang/AST/Type.h"
#include "clang/Basic/SourceLocation.h"
#include "llvm/Support/CommandLine.h"

#include <set>
#include <unordered_map>
#include <iostream>
#include <sstream>

using namespace clang;
using namespace clang::ast_matchers;
using namespace clang::tooling;
using namespace llvm;
using namespace std;

//
// constants, macros etc.
//


#define Indent "    "
#define IndentL2 Indent Indent
#define IndentL3 Indent Indent Indent

#define QT(x) "\"" x "\""

// binding string indentifiers
#define BindToRecordDecl    "recordMatch"
#define BindToTypedefDecl   "typedefMatch"
#define BindToEnumDecl      "enumMatch"
#define BindToFuncDecl      "functionMatch"


// stringified kind names
#define KindNameStruct      QT("struct")
#define KindNameEnum        QT("enum")
#define KindNameFunction    QT("function")

// stringified field names
#define FieldNameIdent      QT("identifier")
#define FieldNameFields     QT("fields")
#define FieldNameReturn     QT("return")
#define FieldNameKind       QT("kind")
#define FieldNameValue      QT("value")

// JSON component strings
#define JsonAssign          " : "
#define JsonSep             ", "


// field definitions
#define IdentField          FieldNameIdent JsonAssign
#define KindField           FieldNameKind JsonAssign
#define FieldsField         FieldNameFields JsonAssign
#define ValueField          FieldNameValue JsonAssign


// return the identifier name
#define identNameOf(decl) (decl->getIdentifier()? \
                            decl->getName() : "(anonymous)")


//
// globals
//

// parsed input file paths
static std::set<const FileEntry*> inputFiles;


//
// helper function
//


static std::string toString(QualType type)
{
    std::string str = type.getAsString();
    if (str == "_Bool")
        return "bool";
    return str;
}


// creates the start of a new record
static void writeRecordBegin(void)
{
    static const char* delim = Indent "{\n";
    
    cout << delim;
    
    delim =  ",\n" Indent "{\n";
}


static bool isTemplateContext(const DeclContext* ctx)
{
    auto parent = dyn_cast<CXXRecordDecl>(ctx);
    
    return parent and
        (parent->getDescribedClassTemplate()
            or isa<ClassTemplateSpecializationDecl>(parent));
}


// determine if the context is a template
static bool isInsideTemplateContext(const Decl* decl)
{
    bool rc = false;
    
    for (const DeclContext *ctx = decl->getDeclContext();
         ctx and isa<NamedDecl>(ctx) and not (rc = isTemplateContext(ctx));
         ctx = ctx->getParent())
        ;
    
    return rc;
}


// determine if the decl was declared in the input files (or external header)
static bool isDeclFromInputFiles(const Decl* decl, SourceManager* sourcemanager)
{
    auto id    = sourcemanager->getFileID(decl->getLocation());
    auto entry = sourcemanager->getFileEntryForID(id);
    return inputFiles.find(entry) != inputFiles.end();
}


// qotify a string
static const std::string quotify(const std::string& s) {
    return "\"" + s + "\"";
}


// write the common header used by all type classes
static void writeCommon(const NamedDecl* decl, std::string kindName)
{
    // start the rcord
    writeRecordBegin();
    
    // write the header fields
    cout << IndentL2 IdentField
         << quotify(identNameOf(decl))
         << ",\n" 
         << IndentL2 KindField
         << kindName
         << ",\n" IndentL2 FieldsField "[";
}



// returns field range for record
inline static RecordDecl::field_range
fieldRangeOf(const RecordDecl* decl) {return decl->fields(); }


// returns field range for function
inline static FunctionDecl::param_const_range
fieldRangeOf(const FunctionDecl* decl) { return decl->params(); }


// write a record like field list
template <class T>
static void writeFieldList(const T& recDecl)
{
    const char* delim = "\n";
             
    for (const auto& decl : fieldRangeOf(recDecl))
    {
        cout << delim
             << IndentL3 "{" FieldNameIdent JsonAssign
             << quotify(decl->getName())
             << JsonSep FieldNameKind JsonAssign
             << quotify(toString(decl->getType()))
             << "}";
                  
        delim = ",\n";
    }
    
    cout << "]";
}


// write the body of an emum
static void writeEnumBody(const EnumDecl* enumDecl)
{
    const char* sep = "\n";

    for (const auto& constDecl : enumDecl->enumerators())
    {
        cout << sep
             << IndentL3 "{" IdentField
             << quotify(constDecl->getName())
             << JsonSep ValueField
             << constDecl->getInitVal().toString(10)
             << "}";
        
        sep = ",\n";
    }
    
    cout << "]\n" Indent "}";
}


// write the body of a struct
static void writeStructBody(const TagDecl* tagDecl)
{
    // inside struct (therefore must be RecordDecl)
    auto recDecl = static_cast<const RecordDecl*>(tagDecl);
    
    writeFieldList(recDecl);
    
    cout << "\n" Indent "}";
}


// test if the decl is valid
template <class T>
static bool isValidDecl(const T* decl, const MatchFinder::MatchResult& result)
{
    return decl and isDeclFromInputFiles(decl, result.SourceManager);
}


// test if the the named decl is valid
template <class T>
static bool isValidNamedDecl(const T* decl,
                             const MatchFinder::MatchResult& result)
{
        return isValidDecl(decl, result)
            and (decl->getIdentifier() != nullptr);
}


//
// Macher callback functors
//


class TypedefWriter : public MatchFinder::MatchCallback {
public:
    virtual void run(const MatchFinder::MatchResult &result) {
        auto typeDecl = result.Nodes.getNodeAs<TypedefDecl>(BindToTypedefDecl);
        
        if (!isValidNamedDecl(typeDecl, result)) return;

        auto type = typeDecl->getUnderlyingType();
        
        if (type->isStructureType())
        {
            writeCommon(typeDecl, KindNameStruct);
            writeStructBody(type->getAs<TagType>()->getDecl());
        }
        else if (type->isEnumeralType())
        {
            writeCommon(typeDecl, KindNameEnum);
            writeEnumBody(type->getAs<EnumType>()->getDecl());
        }
    }
};


class EnumWriter : public MatchFinder::MatchCallback
{
public:
    virtual void run(const MatchFinder::MatchResult &result)
    {
        auto enumDecl = result.Nodes.getNodeAs<EnumDecl>(BindToEnumDecl);
        if (isValidDecl(enumDecl, result)
            and not isInsideTemplateContext(enumDecl)
            and not enumDecl->hasNameForLinkage())  // i.e. its a typedef
        {
            writeCommon(enumDecl, KindNameEnum);
            writeEnumBody(enumDecl);
        }
    }
};

class FunctionWriter : public MatchFinder::MatchCallback
{
public:
    virtual void run(const MatchFinder::MatchResult &result)
    {
        auto func = result.Nodes.getNodeAs<FunctionDecl>(BindToFuncDecl);
        if (isValidNamedDecl(func, result)
            and not isInsideTemplateContext(func)
            and not isa<CXXMethodDecl>(func)
            and not func->getDescribedFunctionTemplate())
        {
            writeCommon(func, KindNameFunction);
            writeFieldList(func);
            
            // write return type
            cout << ",\n" IndentL2 FieldNameReturn JsonAssign
                 << quotify(toString(func->getReturnType()))
                 << "\n" Indent "}";
        }
    }
};


// parse input and create tool
static ClangTool& toolForCommandLineOptions (int argc, const char** argv)
{
    // CommonOptionsParser declares HelpMessage with a description of the common
    // command-line options related to the compilation database and input files.
    // It's nice to have this help message in all tools.
    static const cl::extrahelp commonHelp(CommonOptionsParser::HelpMessage);

    // A help message for this specific tool can be added afterwards.
    static const cl::extrahelp MoreHelp("\nMore help text...");

    // Apply a custom category to all command-line options so that they are the
    // only ones displayed.
    static cl::OptionCategory category("my-tool options");

    static CommonOptionsParser opts(argc, argv, category);
    static auto source = opts.getSourcePathList();
    
    static ClangTool tool(opts.getCompilations(), source);
    
    auto& fm = tool.getFiles();
    for (const auto& f : source)
    {
        inputFiles.insert(fm.getFile(f));
    }
    
    return tool;
}


int main(int argc, const char **argv)
{
    // construct the matchers
    static EnumWriter enumWr;
    static FunctionWriter functionWr;
    static TypedefWriter typedefWr;
    static MatchFinder finder;
  
    // install the maters
    finder.addMatcher(typedefDecl().bind(BindToTypedefDecl), &typedefWr);
    finder.addMatcher(enumDecl(isDefinition()).bind(BindToEnumDecl), &enumWr);
    finder.addMatcher(functionDecl().bind(BindToFuncDecl), &functionWr);
  
    cout << "[\n";
  
    // do the parsing
    auto& tool = toolForCommandLineOptions(argc, argv);
    int result = tool.run(newFrontendActionFactory(&finder).get());
  
    cout << "\n]\n";
  
    return result;
}
