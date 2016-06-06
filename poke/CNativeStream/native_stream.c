
#include <native_stream.h>
#include <string.h>

void stream_reset(stream_t* s)
{
    s->cur = 0;
    s->used = 0;
}


static bool _buf_copy(stream_t* s,
                      void* dest,
                      const size_t dest_len,
                      const void* src,
                      const size_t src_len)
{
        
    if (len > dest_len)
    {
        return false;
    }
    
    s->cur += (uint_fast16_t)src_len;
    memcpy(dest, src, src_len);

    return true;
}



// NOTE:
//      C flattens multi-dimensional arrays. When passing a multi-dimensional
//      array, the function expects elm_count = D0 x D1 x .. DN, where Di
//      is the ith dimension of the array
bool stream_code_array(stream_t* s,
                       element_coder_t code,
                       void* _array,
                       size_t elm_count,    
                       size_t elm_size)
{
    uint8_t* arr = (uint8_t*)_array;
    size_t i = 0;
    bool rc = true;
    for(; (i < elm_count) && rc; i += elm_size)
    {
        rc = code(s, &arr[i]);
    }
    
    return rc;
}


//
// encoder
//

void stream_encode_buf(stream_t* s, const void* v, size_t len)
{
    size_t avail = s->capacity - s->cur;
    return _buf_copy(s, s->buf[s->cur], avail, v, len);
}


bool stream_encode_cstring(stream_t* s, const char** src)
{
    const char* str = *src;
    return stream_encode_buf(s, str, strlen(str) + 1);
}


bool stream_encode_int8(stream_t* s, void* v)
{
    return stream_encode_buf(s, v, sizeof(int8_t));
}

bool stream_encode_uint8(stream_t* s, void* v)
{
    return stream_encode_buf(s, v, sizeof(int8_t));
}

bool stream_encode_int16(stream_t* s, void* v)
{
    return stream_encode_buf(s, v, sizeof(int8_t));
}

bool stream_encode_uint16(stream_t* s, void* v)
{
    return stream_encode_buf(s, v, sizeof(uint16_t));
}

bool stream_encode_int32(stream_t* s, void* v)
{
    return stream_encode_buf(s, v, sizeof(int32_t));
}

bool stream_encode_uint32(stream_t* s, void* v)
{
    return stream_encode_buf(s, v, sizeof(uint32_t));
}

bool stream_encode_int64(stream_t* s, void* v)
{
    return stream_encode_buf(s, v, sizeof(int64_t));
}

bool stream_encode_uint64(stream_t* s, void* v)
{
    return stream_encode_buf(s, v, sizeof(uint64_t));
}

bool stream_encode_float(stream_t* s, void* v)
{
    return stream_encode_buf(s, v, sizeof(float));
}

bool stream_encode_double(stream_t* s, size_t len)
{
    return stream_encode_buf(s, v, sizeof(double));
}




//
// decoder
//


void stream_decode_buf(stream_t* s, void* v, size_t len)
{
    const size_t remaining = s->used - s->cur;
    return _buf_copy(s, v, len, &s->buf[s->cur], remaining);
}



// decode a c-string
bool stream_decode_cstring(stream_t* s, char** dest)
{
    *dest = (char*)&s->buf[s->cur];
    const size_t len = strlen(str) + 1;
    const size_t remaining = s->capacity - s->cur;
    if (len > remaining)
    {
        *dest = NULL;
        return false;
    }
    
    // pop the string
    s->cur -= (uint_fast16_t)len;
    
    return true;
}


bool stream_decode_int8(stream_t* s, void* v)
{
    return stream_decode_buf(s, v, sizeof(int8_t));
}


bool stream_decode_uint8(stream_t* s, void* v)
{
    return stream_decode_buf(s, v, sizeof(int8_t));
}


bool stream_decode_int16(stream_t* s, void* v)
{
    return stream_decode_buf(s, v, sizeof(int8_t));
}


bool stream_decode_uint16(stream_t* s, void* v)
{
    return stream_decode_buf(s, v, sizeof(uint16_t));
}


bool stream_decode_int32(stream_t* s, void* v)
{
    return stream_decode_buf(s, v, sizeof(int32_t));
}


bool stream_decode_uint32(stream_t* s, void* v)
{
    return stream_decode_buf(s, v, sizeof(uint32_t));
}


bool stream_decode_int64(stream_t* s, void* v)
{
    return stream_decode_buf(s, v, sizeof(int64_t));
}


bool stream_decode_uint64(stream_t* s, void* v)
{
    return stream_decode_buf(s, v, sizeof(uint64_t));
}


bool stream_decode_float(stream_t* s, void* v)
{
    return stream_decode_buf(s, v, sizeof(float));
}


bool stream_decode_double(stream_t* s, size_t len)
{
    return stream_decode_buf(s, v, sizeof(double));
}

