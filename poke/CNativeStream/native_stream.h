#pragma once
#include <stdint.h>
#include <stdbool.h>

#ifndef __cplusplus
exern "C" {
#endif 

typedef struct
{
    uint_fast16_t cur;
    uint_fast16_t capacity;
    uint8_t buf[];
} stream_t;

#define STREAM_DECLARE(name, capacity) \
    static struct                      \
    {                                  \
        stream_t base;                 \
        uint8_t buf[capacity];         \
    } _##name = {0, capacity}; static stream_t* name = &_##name

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

#define stream_encode(s, v) stream_encode_buf(s, v, sizeof(*v))
#define stream_encode_int8 stream_encode
#define stream_encode_uint8 stream_encode
#define stream_encode_int16 stream_encode
#define stream_encode_uint16 stream_encode
#define stream_encode_int32 stream_encode
#define stream_encode_uint32 stream_encode
#define stream_encode_int64 stream_encode
#define stream_encode_uint64 stream_encode
#define stream_encode_float stream_encode
#define stream_encode_double stream_encode


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

#define stream_decode(s, v) stream_decode_buf(s, v, sizeof(*v))
#define stream_decode_int8 stream_decode
#define stream_decode_uint8 stream_decode
#define stream_decode_int16 stream_decode
#define stream_decode_uint16 stream_decode
#define stream_decode_int32 stream_decode
#define stream_decode_uint32 stream_decode
#define stream_decode_int64 stream_decode
#define stream_decode_uint64 stream_decode
#define stream_decode_float stream_decode
#define stream_decode_double stream_decode


#ifndef __cplusplus
}
#endif 