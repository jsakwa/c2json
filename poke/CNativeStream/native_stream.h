#pragma once
#include <stdint.h>
#include <stdbool.h>

#ifndef __cplusplus
exern "C" {
#endif 

typedef struct
{
    uint_fast16_t cur;  // always reset to 0
    uint_fast16_t used; // only valid for input streams
    uint_fast16_t capacity;
    uint8_t buf[];
} stream_t;

typedef bool (*element_coder_t)(stream_t* s, void* v)


#define STREAM_DECLARE(name, capacity) \
    static struct                      \
    {                                  \
        stream_t base;                 \
        uint8_t buf[capacity];         \
    } _##name = {0, 0, capacity}; static stream_t* name = &_##name

void stream_reset(stream_t* s);


//
// encoder
//

// append len bytes to the output stream
bool stream_encode_buf(stream_t* s, void* v, size_t len);

// encode a c-string
// NOTE:
//      the extra level of indirection saves some logic in the code generator
bool stream_encode_cstring(stream_t* s, const char** str);

// encode 
// NOTE:
//      C flattens multi-dimensional arrays. When passing a multi-dimensional
//      array, the function expects elm_count = D0 x D1 x .. DN, where Di
//      is the ith dimension of the array
bool stream_code_array(stream_t* s,
                       element_coder_t codeer,
                       void* _array,
                       size_t elm_count,    
                       size_t elm_size)

//
// decoder
//

// extract length bytes from the input stream
bool stream_decode_buf(stream_t* s, void* v, size_t len);

// decode a c-string
// NOTE:
//      creates a shallow copy, that must be consumed prior to cleaining the
//      call-stack
bool stream_decode_cstring(stream_t* s, char** str);


// NOTE:
//      C flattens multi-dimensional arrays. When passing a multi-dimensional
//      array, the function expects elm_count = D0 x D1 x .. DN, where Di
//      is the ith dimension of the array
bool stream_decode_array(stream_t* s,
                         element_coder_t decode,
                         void* _array,
                         size_t elm_count,    
                         size_t elm_size)




#ifndef __cplusplus
}
#endif 