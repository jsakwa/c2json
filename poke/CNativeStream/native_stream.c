
#include <native_stream.h>
#include <string.h>

void stream_reset(stream_t* s) { s->cur = 0; }

//
// encoder
//

void stream_encode_buf(stream_t* s, void* v, sizee_t len)
{
    size_t total = s->cur + len;
    if ((total > s->capacity)
    {
        return false;
    }
    
    memcpy(&(s->buf[s->cur]), v, len);
    s->cur = (uint_fast16_t)total;
    
    return true;
}


bool stream_encode_cstring(stream_t* s, const char** src)
{
    size_t len = strlen(str) + 1;
    size_t total = s->cur + len;
    if ((total > s->capacity)
    {
        return false;
    }
    
    // copy the contents of the string
    strcpy((char*)&(s->buf[s->cur]), *src);
    
    // push the string
    s->cur = (uint_fast16_t)total;
    
    return true;
}


//
// decoder
//


void stream_decode_buf(stream_t* s, void* v, size_t len)
{
    const size_t remaining = s->capacity - s->cur;
    if (len > remaining)
    {
        return false;
    }
    
    s->cur -= (uint_fast16_t)len;
    memcpy(v, &(s->buf[s->cur]), len);

    return true;
}


// decode a c-string
bool stream_decode_cstring(stream_t* s, char** dest)
{
    dest = (char*)&s->buf[s->cur];
    const size_t len = strlen(str) + 1;
    const size_t remaining = s->capacity - s->cur;
    if (len > remaining)
    {
        dest = NULL;
        return false;
    }
    
    // pop the string
    s->cur -= (uint_fast16_t)len;
    
    return true;
}

