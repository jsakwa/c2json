#ifndef _test_h_
#define _test_h_

#include <stdint.h>
#include <stdlib.h>


enum
{
    
    item0 = 0,
    item1 = 1,
    item2 = 3,
};

typedef enum
{
    
    enum2_item1,
    enum2_item3,
} enum2_t;

typedef struct
{
    uint32_t it_was;
} saying_t;


typedef struct
{
    char* hello;
    char* world;
    saying_t array[10][2];
} greeting_t;



void say_hello(const greeting_t* msg);

void do_math(int32_t *x);
    
#endif
